"""Neural baselines for the ThermBench forward task (PyTorch).

Input  [B, C_in, ny, nx_max]: initial theta field, tank mask, inlet map, outlet map, t*, and
       the standardised scalar parameters, each broadcast to a constant channel.
Output [B, cout, ny, nx_max]: theta at t* (tank, cout = 1) or theta and liquid fraction (PCM,
       cout = 2); only cells inside the mask are scored.

  FNO2d  Fourier neural operator (Li et al. 2021): lifting, L spectral layers (keep the
         lowest modes x modes Fourier coefficients) with a pointwise skip, projection
  UNet   4-level convolutional U-Net, GroupNorm + GELU, padded to a multiple of 16
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


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


MODELS = {"fno": FNO2d, "unet": UNet}
