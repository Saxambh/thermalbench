"""Train and score a neural baseline on a ThermalStorageBench split.

  python train.py --model fno --split random --epochs 50 [--seed 1] [--hybrid]
--hybrid: the network gets the plug-flow field as an extra input and predicts only the
correction to it; the prediction is plug flow + correction (name <model>_hybrid).
--canon: canonical frame. A discharge run (cold inlet low right, outlet high left) is a charge
run (hot inlet high left, outlet low right) turned by 180 degrees with hot and cold swapped,
exactly so under the Boussinesq approximation with constant properties (approximately with
the real water properties used). Discharge runs are therefore rotated and inverted
(theta -> 1 - theta) into the charge frame on the way in, their 'discharge' flag is set to 0,
and the prediction is transformed back before scoring (name <model>[_hybrid]_canon).
Trains on every stride-th snapshot of the train runs, picks the epoch with the lowest
validation loss, then scores the test runs with evaluate.evaluate (same metrics as the
non-neural baselines). Writes ckpt_<model>_<split>.pt and merges into results/<split>.json
(name <model>, or <model>_s<seed> for seeds other than 0).
"""
import argparse
import json
import os
import time

import numpy as np
import torch

import evaluate
from baselines import IdealStratified
from data import DEFAULT_ROOTS, PARAMS, index, pad, port_maps
from models import MODELS
from splits import SPLITS, EXTRA_SPLITS, split_runs, _u

HERE = os.path.dirname(os.path.abspath(__file__))


def plug(run, idx, nx_max):
    """Ideal plug-flow (IdealStratified) theta at snapshots idx, padded: [n, ny, nx_max]."""
    return pad(IdealStratified().predict(run, idx), nx_max)[0]


I_DISCHARGE = list(PARAMS).index("discharge")
I_YINIT = list(PARAMS).index("y_init")


def flipped(run, canon):
    return canon and run.meta["mode"] == "discharge"


def rot180(a, nx, invert=False):
    """Turn [..., ny, nx_max] (left-aligned, tank in [:nx]) by 180 degrees inside the tank;
    invert=True also swaps hot and cold (theta -> 1 - theta). Its own inverse."""
    b = np.zeros_like(a)
    r = a[..., ::-1, :nx][..., ::-1]
    b[..., :nx] = 1 - r if invert else r
    return b


class Encoder:
    """Builds the input channels for a run; parameter scaling is fitted on the train runs.
    hybrid=True adds the plug-flow field at t* as one more channel; the network then predicts
    the correction to it (see Samples and Predictor). canon=True works in the charge frame
    (see the module docstring)."""

    def __init__(self, train, hybrid=False, canon=False, canon_yi=False):
        # canon_yi (diagnostic, 2026-11-10 referee fixes; off in every released model): in the canonical frame also
        # mirror the pre-stratified interface height y_init -> 1 - y_init, as the initial field is mirrored
        self.hybrid, self.canon, self.canon_yi = hybrid, canon, canon_yi
        P = np.array([self.params(r) for r in train])
        # a parameter that never varies in training (e.g. 'discharge' in ood_mode) keeps unit
        # scale: dividing by its ~0 spread would feed the test runs values of ~1e6
        sd = P.std(0)
        self.mu, self.sd = P.mean(0), np.where(sd < 1e-6, 1.0, sd)
        self.nx_max = int(round(1.0 / train[0].meta["mesh_h_m"]))   # widest tank, W = 1 m

    @property
    def channels(self):
        return 4 + 1 + len(PARAMS) + int(self.hybrid)

    def params(self, run):
        p = run.params()
        if flipped(run, self.canon):
            p[I_DISCHARGE] = 0.0
            if self.canon_yi and run.meta["init"] != "uniform":
                p[I_YINIT] = 1.0 - p[I_YINIT]
        return p

    def theta(self, run, a):
        """A padded theta field [..., ny, nx_max] into the model frame; also the way back."""
        return rot180(a, run.meta["nx"], invert=True) if flipped(run, self.canon) else a

    def static(self, run):
        """[C - 1, ny, nx_max]: theta0, mask, inlet, outlet, then one constant channel per parameter."""
        th0, mask = pad(run.field("T", idx=[0], theta=True)[0], self.nx_max)
        ny = th0.shape[0]
        ports = port_maps(run.meta, ny, self.nx_max)
        if flipped(run, self.canon):
            th0 = self.theta(run, th0)
            ports = [rot180(m, run.meta["nx"]) for m in ports]
        p = (self.params(run) - self.mu) / self.sd
        consts = np.broadcast_to(p[:, None, None], (len(p), ny, self.nx_max))
        return np.concatenate([np.stack([th0, mask, *ports]), consts]).astype(np.float32)

    def batch(self, static, tstar, base=None):
        """static [C-1, ny, nx], tstar [n] (+ base [n, ny, nx] plug flow if hybrid) -> inputs [n, C, ny, nx]."""
        n = len(tstar)
        s = torch.as_tensor(static)[None].expand(n, -1, -1, -1)
        t = torch.as_tensor(np.asarray(tstar, np.float32))[:, None, None, None].expand(n, 1, *static.shape[1:])
        parts = [s, t] + ([torch.as_tensor(np.asarray(base, np.float32))[:, None]] if self.hybrid else [])
        return torch.cat(parts, 1)


class Samples(torch.utils.data.Dataset):
    """Every stride-th snapshot (t > 0) of the given runs, held in memory as float16.
    In hybrid mode the target is the correction to plug flow (CFD - plug), so the loss is
    still the full-field error of plug + network."""

    def __init__(self, runs, enc, stride):
        self.enc, self.items = enc, []
        self.static, self.target, self.mask, self.base = [], [], [], []
        for k, r in enumerate(runs):
            ts = r.times()[1]
            idx = np.arange(stride, len(ts), stride)
            tgt, mask = pad(r.field("T", idx=idx, theta=True), enc.nx_max)
            tgt = enc.theta(r, tgt)
            if enc.hybrid:
                b = enc.theta(r, plug(r, idx, enc.nx_max))
                tgt = tgt - b
                self.base.append(b.astype(np.float16))
            self.static.append(enc.static(r).astype(np.float16))
            self.target.append(tgt.astype(np.float16))
            self.mask.append(mask)
            self.items += [(k, j, ts[i]) for j, i in enumerate(idx)]

    def __len__(self):
        return len(self.items)

    def __getitem__(self, n):
        k, j, t = self.items[n]
        base = self.base[k][j][None].astype(np.float32) if self.enc.hybrid else None
        x = self.enc.batch(self.static[k].astype(np.float32), [t], base)[0]
        return x, torch.as_tensor(self.target[k][j].astype(np.float32))[None], torch.as_tensor(self.mask[k])[None]


class GPUData:
    """A Samples set held on the GPU as float16 (static channels per run, target and plug-flow
    base per snapshot); batches are assembled on the device, so no host-to-device copy per
    step. About 2.3 GB for the full 5 mm dataset (3.2 GB hybrid)."""

    def __init__(self, ds, device):
        self.hybrid = ds.enc.hybrid
        to = lambda arrs: torch.as_tensor(np.stack(arrs)).to(device)
        self.static = to(ds.static)                                        # [R, Cs, ny, nx]
        self.mask = to([m.astype(np.float16) for m in ds.mask])            # [R, ny, nx]
        self.target = torch.as_tensor(np.concatenate(ds.target)).to(device)   # [S, ny, nx]
        self.base = torch.as_tensor(np.concatenate(ds.base)).to(device) if self.hybrid else None
        start = np.cumsum([0] + [len(t) for t in ds.target])[:-1]
        self.k = torch.as_tensor([k for k, _, _ in ds.items], device=device)
        self.flat = torch.as_tensor([start[k] + j for k, j, _ in ds.items], device=device)
        self.t = torch.as_tensor([t for _, _, t in ds.items], dtype=torch.float32, device=device)
        ds.static, ds.target, ds.mask, ds.base = [], [], [], []           # free the host copies

    def __len__(self):
        return len(self.flat)

    def batches(self, bs, shuffle):
        order = torch.randperm(len(self), device=self.flat.device) if shuffle else \
            torch.arange(len(self), device=self.flat.device)
        for i in range(0, len(self), bs):
            idx = order[i:i + bs]
            k, f = self.k[idx], self.flat[idx]
            st = self.static[k].float()
            parts = [st, self.t[idx][:, None, None, None].expand(-1, 1, *st.shape[2:])]
            if self.hybrid:
                parts.append(self.base[f].float()[:, None])
            yield torch.cat(parts, 1), self.target[f].float()[:, None], self.mask[k].float()[:, None]


class Predictor:
    """evaluate.evaluate interface around a trained network."""

    def __init__(self, net, enc, device):
        self.net, self.enc, self.device = net, enc, device

    @torch.no_grad()
    def predict(self, run, idx):
        self.net.eval()
        idx = np.atleast_1d(idx)
        base = self.enc.theta(run, plug(run, idx, self.enc.nx_max)) if self.enc.hybrid else None
        x = self.enc.batch(self.enc.static(run), run.times()[1][idx], base).to(self.device)
        out = torch.cat([self.net(x[i:i + 8]) for i in range(0, len(x), 8)])[:, 0].float().cpu().numpy()
        if self.enc.hybrid:
            out = out + base   # network output is the correction to plug flow
        out = self.enc.theta(run, out)   # back to the run's own frame (no-op unless canon)
        return out[:, :, : run.meta["nx"]]


def masked_mse(pred, tgt, mask):
    return ((pred - tgt) ** 2 * mask).sum() / mask.sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(MODELS), default="fno")
    ap.add_argument("--roots", nargs="+", default=DEFAULT_ROOTS)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--split", default="random", choices=SPLITS + EXTRA_SPLITS)
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--width", type=int, default=32)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--hybrid", action="store_true", help="learn the correction to plug flow")
    ap.add_argument("--canon", action="store_true", help="rotate discharge runs into the charge frame")
    ap.add_argument("--canon-yi", action="store_true", help="diagnostic: with --canon, also mirror y_init (name suffix yi)")
    ap.add_argument("--outdir", default="results", help="results folder (merged into <outdir>/<split>.json)")
    ap.add_argument("--manifest", default=None, help="frozen run list (freeze_manifest.py)")
    ap.add_argument("--amp", action="store_true", help="mixed precision (bf16 autocast)")
    ap.add_argument("--gpu-data", action="store_true", help="hold the training data on the GPU")
    ap.add_argument("--train-frac", type=float, default=1.0,
                    help="learning curve: keep this fraction of the training design points "
                         "(nested subsets by hash of case_id; val and test unchanged)")
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    torch.manual_seed(a.seed)
    t_start = time.time()

    s = split_runs(index(a.roots, manifest=a.manifest), a.split)
    if a.train_frac < 1.0:   # nested: a design point kept at 0.25 is also kept at 0.5
        s["train"] = [r for r in s["train"] if _u(r.case_id, "frac") < a.train_frac]
    if not s["test"] or not s["val"]:
        print(f"split {a.split}: not enough finished runs yet ({ {k: len(v) for k, v in s.items()} })")
        return
    print(f"train {len(s['train'])}, val {len(s['val'])}, test {len(s['test'])} runs; device {a.device}")
    enc = Encoder(s["train"], hybrid=a.hybrid, canon=a.canon, canon_yi=a.canon_yi)
    model_name = a.model + ("_hybrid" if a.hybrid else "") + ("_canon" if a.canon else "") + ("yi" if a.canon_yi else "") + \
        (f"_f{round(100 * a.train_frac)}" if a.train_frac < 1.0 else "")
    tr, va = Samples(s["train"], enc, a.stride), Samples(s["val"], enc, a.stride)
    if a.gpu_data:
        tr, va = GPUData(tr, a.device), GPUData(va, a.device)
        train_batches = lambda: tr.batches(a.batch, shuffle=True)
        val_batches = lambda: va.batches(a.batch, shuffle=False)
    else:
        dl = torch.utils.data.DataLoader(tr, batch_size=a.batch, shuffle=True)
        dv = torch.utils.data.DataLoader(va, batch_size=a.batch)
        train_batches, val_batches = (lambda: iter(dl)), (lambda: iter(dv))
    steps_per_epoch = -(-len(tr) // a.batch)
    kw = {"width": a.width} if a.model == "fno" else {"base": a.width}
    net = MODELS[a.model](enc.channels, **kw).to(a.device)
    print(f"{model_name}: {sum(p.numel() for p in net.parameters()) / 1e6:.2f} M parameters, "
          f"{len(tr)} train / {len(va)} val samples; batch {a.batch}, amp {a.amp}, gpu-data {a.gpu_data}")
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.epochs * steps_per_epoch)
    name = model_name if a.seed == 0 else f"{model_name}_s{a.seed}"
    # one checkpoint per model, split AND seed, kept with the results (2026-11-03: before, seeds
    # overwrote each other's ckpt_<model>_<split>.pt in the code folder)
    os.makedirs(os.path.join(HERE, a.outdir, "ckpt"), exist_ok=True)
    ckpt = os.path.join(HERE, a.outdir, "ckpt", f"ckpt_{name}_{a.split}.pt")
    best = float("inf")
    for ep in range(a.epochs):
        t0, net = time.time(), net.train()
        tl = torch.zeros((), device=a.device)      # summed on the GPU: no sync every step
        for x, y, m in train_batches():
            x, y, m = x.to(a.device), y.to(a.device), m.to(a.device)
            with torch.autocast("cuda", dtype=torch.bfloat16, enabled=a.amp):
                out = net(x)
            loss = masked_mse(out.float(), y, m)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            tl += loss.detach() * len(x)
        tl = tl.item()
        net.eval()
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16, enabled=a.amp):
            vl = sum(masked_mse(net(x.to(a.device)).float(), y.to(a.device), m.to(a.device)).item() * len(x)
                     for x, y, m in val_batches()) / max(len(va), 1)
        if vl < best:
            best = vl
            torch.save(net.state_dict(), ckpt)
        print(f"epoch {ep + 1:3d}  train RMSE {np.sqrt(tl / len(tr)):.4f}  val RMSE {np.sqrt(vl):.4f}  "
              f"{time.time() - t0:5.1f} s", flush=True)

    net.load_state_dict(torch.load(ckpt))
    res, per_run = evaluate.evaluate(Predictor(net, enc, a.device), s["test"], a.stride)
    print({k: round(v, 4) for k, v in res.items()})
    evaluate.save(a.split, {k: len(v) for k, v in s.items()}, sum(map(len, s.values())), a.stride,
                  name, res, per_run, {"epochs": a.epochs, "width": a.width, "seed": a.seed,
                                       "best_val_rmse": float(np.sqrt(best)), "train_frac": a.train_frac,
                                       "train_min": round((time.time() - t_start) / 60, 1)}, outdir=a.outdir)


if __name__ == "__main__":
    main()
