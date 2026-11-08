"""Neural baselines for the ThermalStorageBench forward task (PyTorch).

Input  [B, C_in, ny, nx_max]: initial theta field, tank mask, inlet map, outlet map, t*, and
       the standardised scalar parameters, each broadcast to a constant channel.
Output [B, cout, ny, nx_max]: theta at t* (tank, cout = 1) or theta and liquid fraction (PCM,
       cout = 2); only cells inside the mask are scored.

  FNO2d  Fourier neural operator (Li et al. 2021): lifting, L spectral layers (keep the
         lowest modes x modes Fourier coefficients) with a pointwise skip, projection
  UNet   4-level convolutional U-Net, GroupNorm + GELU, padded to a multiple of 16
  Transolver  physics-attention transformer (Wu et al., ICML 2024; added 8 November 2026,
         extra_baselines_2026-11-08/PLAN.md): every grid cell is a token; each layer softly assigns the
         cells to M learned slices, attends among the M slice tokens and maps back, so the cost is
         linear in the number of cells. Width = 4 x base (base 32 -> width 128, the --width argument);
         tokens are 4 x 4 cell patches (PLAN.md, amendment 1).
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint


class SpectralConv2d(nn.Module):
    def __init__(self, cin, cout, m1, m2):
        super().__init__()
        self.m1, self.m2 = m1, m2
        s = 1 / (cin * cout)
        self.w1 = nn.Parameter(s * torch.randn(cin, cout, m1, m2, dtype=torch.cfloat))
        self.w2 = nn.Parameter(s * torch.randn(cin, cout, m1, m2, dtype=torch.cfloat))

    def forward(self, x):
        B, _, H, W = x.shape
        xf = torch.fft.rfft2(x.float())   # FFTs stay in float32 under mixed precision
        out = torch.zeros(B, self.w1.shape[1], H, W // 2 + 1, dtype=torch.cfloat, device=x.device)
        m1, m2 = min(self.m1, H // 2), min(self.m2, W // 2 + 1)
        out[:, :, :m1, :m2] = torch.einsum("bixy,ioxy->boxy", xf[:, :, :m1, :m2], self.w1[:, :, :m1, :m2])
        out[:, :, -m1:, :m2] = torch.einsum("bixy,ioxy->boxy", xf[:, :, -m1:, :m2], self.w2[:, :, :m1, :m2])
        return torch.fft.irfft2(out, s=(H, W))


class FNO2d(nn.Module):
    def __init__(self, cin, width=32, modes=16, layers=4, cout=1):
        super().__init__()
        self.lift = nn.Conv2d(cin + 2, width, 1)              # + 2 coordinate channels
        self.spec = nn.ModuleList(SpectralConv2d(width, width, modes, modes) for _ in range(layers))
        self.skip = nn.ModuleList(nn.Conv2d(width, width, 1) for _ in range(layers))
        self.proj = nn.Sequential(nn.Conv2d(width, 128, 1), nn.GELU(), nn.Conv2d(128, cout, 1))

    def forward(self, x):
        B, _, H, W = x.shape
        gy, gx = torch.meshgrid(torch.linspace(0, 1, H, device=x.device),
                                torch.linspace(0, 1, W, device=x.device), indexing="ij")
        x = torch.cat([x, gy.expand(B, 1, H, W), gx.expand(B, 1, H, W)], 1)
        # pad so the non-periodic domain is not wrapped onto itself by the FFT
        p = 8
        x = F.pad(self.lift(x), (0, p, 0, p))
        for i, (s, k) in enumerate(zip(self.spec, self.skip)):
            x = s(x) + k(x)
            if i < len(self.spec) - 1:
                x = F.gelu(x)
        return self.proj(x[..., :H, :W])


def _block(cin, cout):
    return nn.Sequential(nn.Conv2d(cin, cout, 3, padding=1), nn.GroupNorm(8, cout), nn.GELU(),
                         nn.Conv2d(cout, cout, 3, padding=1), nn.GroupNorm(8, cout), nn.GELU())


class UNet(nn.Module):
    def __init__(self, cin, base=32, levels=4, cout=1):
        super().__init__()
        ch = [base * 2 ** i for i in range(levels + 1)]
        self.down = nn.ModuleList([_block(cin, ch[0])] + [_block(ch[i], ch[i + 1]) for i in range(levels)])
        self.up = nn.ModuleList(nn.ConvTranspose2d(ch[i + 1], ch[i], 2, stride=2) for i in reversed(range(levels)))
        self.dec = nn.ModuleList(_block(2 * ch[i], ch[i]) for i in reversed(range(levels)))
        self.out = nn.Conv2d(ch[0], cout, 1)
        self.levels = levels

    def forward(self, x):
        H, W = x.shape[-2:]
        m = 2 ** self.levels
        x = F.pad(x, (0, (-W) % m, 0, (-H) % m))
        skips = []
        for i, d in enumerate(self.down):
            x = d(x if i == 0 else F.max_pool2d(x, 2))
            skips.append(x)
        x = skips.pop()
        for u, d in zip(self.up, self.dec):
            x = d(torch.cat([u(x), skips.pop()], 1))
        return self.out(x)[..., :H, :W]


class PhysicsAttention(nn.Module):
    """Transolver physics attention for a point set [B, N, C] (the reference irregular-mesh form)."""

    def __init__(self, dim, heads=8, slices=32, conv=False):
        super().__init__()
        self.h, self.d, self.conv = heads, dim // heads, conv
        self.temperature = nn.Parameter(torch.full((1, heads, 1, 1), 0.5))
        # conv=True: 3 x 3 convolutions on the token grid, as the reference structured-mesh variant
        self.in_x = nn.Conv2d(dim, dim, 3, padding=1) if conv else nn.Linear(dim, dim)
        self.in_fx = nn.Conv2d(dim, dim, 3, padding=1) if conv else nn.Linear(dim, dim)
        self.slice = nn.Linear(self.d, slices)
        nn.init.orthogonal_(self.slice.weight)
        self.q, self.k, self.v = (nn.Linear(self.d, self.d, bias=False) for _ in range(3))
        self.out = nn.Linear(dim, dim)

    def forward(self, x, hw=None):
        B, N, C = x.shape
        proj = (lambda f: f(x.transpose(1, 2).reshape(B, C, *hw)).flatten(2).transpose(1, 2)) if self.conv else (lambda f: f(x))
        fx = proj(self.in_fx).reshape(B, N, self.h, self.d).transpose(1, 2)    # [B, H, N, d]
        xm = proj(self.in_x).reshape(B, N, self.h, self.d).transpose(1, 2)
        w = torch.softmax(self.slice(xm) / self.temperature, dim=-1)          # [B, H, N, M]
        norm = w.sum(2)                                                        # [B, H, M]
        tok = torch.einsum("bhnm,bhnd->bhmd", w, fx) / (norm[..., None] + 1e-5)
        q, k, v = self.q(tok), self.k(tok), self.v(tok)
        tok = F.scaled_dot_product_attention(q, k, v)                         # [B, H, M, d]
        y = torch.einsum("bhmd,bhnm->bhnd", tok, w)
        return self.out(y.transpose(1, 2).reshape(B, N, -1))


class TransolverBlock(nn.Module):
    def __init__(self, dim, heads, slices, mlp_ratio=4, conv=False):
        super().__init__()
        self.n1, self.n2 = nn.LayerNorm(dim), nn.LayerNorm(dim)
        self.attn = PhysicsAttention(dim, heads, slices, conv)
        self.mlp = nn.Sequential(nn.Linear(dim, dim * mlp_ratio), nn.GELU(), nn.Linear(dim * mlp_ratio, dim))

    def forward(self, x, hw=None):
        x = x + self.attn(self.n1(x), hw)
        return x + self.mlp(self.n2(x))


class Transolver(nn.Module):
    """Grid in, grid out: [B, cin, H, W] -> [B, cout, H, W] (+ 2 coordinates as in FNO2d). Tokens are
    patch x patch cell blocks (patch 1: every cell is a token), embedded by a patch convolution and decoded
    per token to its patch x patch cells, as in vision transformers. Gradient checkpointing per block
    while training saves memory only; the computation is identical."""

    def __init__(self, cin, base=32, layers=6, heads=8, slices=32, patch=4, conv=False, cout=1):
        super().__init__()
        dim, self.p, self.cout = 4 * base, patch, cout
        self.embed = nn.Conv2d(cin + 2, dim, patch, stride=patch)
        self.pre = nn.Sequential(nn.GELU(), nn.Linear(dim, dim))
        self.blocks = nn.ModuleList(TransolverBlock(dim, heads, slices, conv=conv) for _ in range(layers))
        self.head = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, cout * patch * patch))

    def forward(self, x):
        B, _, H, W = x.shape
        p = self.p
        gy, gx = torch.meshgrid(torch.linspace(0, 1, H, device=x.device),
                                torch.linspace(0, 1, W, device=x.device), indexing="ij")
        x = torch.cat([x, gy.expand(B, 1, H, W), gx.expand(B, 1, H, W)], 1)
        x = F.pad(x, (0, (-W) % p, 0, (-H) % p))
        h, w = x.shape[-2] // p, x.shape[-1] // p
        z = self.pre(self.embed(x).flatten(2).transpose(1, 2))                 # [B, h*w, dim]
        for b in self.blocks:
            z = checkpoint(b, z, (h, w), use_reentrant=False) if self.training and torch.is_grad_enabled() else b(z, (h, w))
        y = self.head(z).transpose(1, 2).reshape(B, self.cout * p * p, h, w)
        return F.pixel_shuffle(y, p)[..., :H, :W]


MODELS = {"fno": FNO2d, "unet": UNet, "transolver": Transolver}
