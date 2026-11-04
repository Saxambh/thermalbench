"""Train and score a neural baseline on a ThermBench PCM split.

  python pcm_train.py --model fno --split random --epochs 60 [--seed 1] [--hybrid]
Input channels: box mask, PCM mask (0 on fins), fin map, heated-wall map, tau = t / t_ref,
the standardised scalar parameters (pcm_data.PARAMS, one constant channel each), and with
--hybrid the Front baseline's theta and alpha. Output: theta and liquid fraction (with
--hybrid, the correction to Front). Loss: theta error over the box plus alpha error over the
PCM. Trains on every stride-th snapshot of the train runs, keeps the epoch with the lowest
validation loss, scores the test runs with pcm_evaluate.evaluate. Writes
ckpt_pcm_<model>_<split>.pt and merges into results_pcm/<split>.json.
"""
import argparse
import os
import time

import numpy as np
import torch

import pcm_evaluate
from models import MODELS
from pcm_baselines import Front
from pcm_data import DEFAULT_ROOTS, PARAMS, index, nx_max, pad
from pcm_splits import SPLITS, split_runs
from splits import _u

HERE = os.path.dirname(os.path.abspath(__file__))


class Encoder:
    """Input channels for a run; parameter scaling fitted on the train runs."""

    def __init__(self, train, hybrid=False):
        self.hybrid = hybrid
        P = np.array([r.params() for r in train])
        sd = P.std(0)
        self.mu, self.sd = P.mean(0), np.where(sd < 1e-6, 1.0, sd)
        self.nx_max = nx_max(train[0].meta["mesh_h_m"])
        self.front = Front().fit(train) if hybrid else None

    @property
    def channels(self):
        return 4 + 1 + len(PARAMS) + 2 * int(self.hybrid)

    def static(self, run):
        """[4 + P, ny, nx_max]: box, PCM, fins, heated wall, parameters."""
        pcm, box = pad(run.mask(), self.nx_max)
        fin = box - pcm
        wall = np.zeros_like(box)
        wall[:, 0] = 1
        p = (run.params() - self.mu) / self.sd
        consts = np.broadcast_to(p[:, None, None], (len(p),) + box.shape)
        return np.concatenate([np.stack([box, pcm, fin, wall]), consts]).astype(np.float32)

    def base(self, run, idx):
        """Front baseline [n, 2, ny, nx_max] (hybrid only)."""
        th, al = self.front.predict(run, idx)
        return np.stack([pad(th, self.nx_max)[0], pad(al, self.nx_max)[0]], 1)


def build(runs, enc, stride, device):
    """All stride-th snapshots of the runs, on the device as float16."""
    S, X, Y, M, B, K, T = [], [], [], [], [], [], []
    for k, r in enumerate(runs):
        t, tau = r.times()
        idx = np.arange(stride, len(t), stride)
        th = pad(r.field("T", idx=idx, theta=True), enc.nx_max)[0]
        al = pad(r.field("alpha", idx=idx), enc.nx_max)[0]
        y = np.stack([th, al], 1)
        st = enc.static(r)
        if enc.hybrid:
            b = enc.base(r, idx)
            B.append(b.astype(np.float16))
            y = y - b
        S.append(st.astype(np.float16))
        M.append(np.stack([st[0], st[1]]).astype(np.float16))     # theta over the box, alpha over PCM
        Y.append(y.astype(np.float16))
        K += [k] * len(idx)
        T += list(tau[idx])
    to = lambda a: torch.as_tensor(a).to(device)
    return {"static": to(np.stack(S)), "mask": to(np.stack(M)), "y": to(np.concatenate(Y)),
            "base": to(np.concatenate(B)) if enc.hybrid else None,
            "k": torch.as_tensor(K, device=device), "tau": torch.as_tensor(T, dtype=torch.float32, device=device)}


def batches(d, bs, shuffle):
    n = len(d["k"])
    order = torch.randperm(n, device=d["k"].device) if shuffle else torch.arange(n, device=d["k"].device)
    for i in range(0, n, bs):
        j = order[i:i + bs]
        st = d["static"][d["k"][j]].float()
        parts = [st, d["tau"][j][:, None, None, None].expand(-1, 1, *st.shape[2:])]
        if d["base"] is not None:
            parts.append(d["base"][j].float())
        yield torch.cat(parts, 1), d["y"][j].float(), d["mask"][d["k"][j]].float()


def masked_mse(pred, tgt, mask):
    return ((pred - tgt) ** 2 * mask).sum() / mask.sum()


class Predictor:
    def __init__(self, net, enc, device):
        self.net, self.enc, self.device = net, enc, device

    @torch.no_grad()
    def predict(self, run, idx):
        self.net.eval()
        idx = np.atleast_1d(idx)
        tau = run.times()[1][idx]
        st = torch.as_tensor(self.enc.static(run))[None].expand(len(idx), -1, -1, -1)
        parts = [st, torch.as_tensor(tau, dtype=torch.float32)[:, None, None, None].expand(-1, 1, *st.shape[2:])]
        base = self.enc.base(run, idx) if self.enc.hybrid else None
        if base is not None:
            parts.append(torch.as_tensor(base, dtype=torch.float32))
        x = torch.cat(parts, 1).to(self.device)
        out = torch.cat([self.net(x[i:i + 8]) for i in range(0, len(x), 8)]).float().cpu().numpy()
        if base is not None:
            out = out + base
        nx = run.meta["nx"]
        return out[:, 0, :, :nx], np.clip(out[:, 1, :, :nx], 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(MODELS), default="fno")
    ap.add_argument("--roots", nargs="+", default=DEFAULT_ROOTS)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--split", default="random", choices=SPLITS)
    ap.add_argument("--stride", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--width", type=int, default=32)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--hybrid", action="store_true", help="learn the correction to the Front baseline")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--amp", action="store_true")
    ap.add_argument("--train-frac", type=float, default=1.0)
    ap.add_argument("--outdir", default="results_pcm")
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    torch.manual_seed(a.seed)
    t_start = time.time()

    s = split_runs(index(a.roots, manifest=a.manifest), a.split)
    if a.train_frac < 1.0:
        s["train"] = [r for r in s["train"] if _u(r.case_id, "frac") < a.train_frac]
    if not s["test"] or not s["val"] or not s["train"]:
        print(f"split {a.split}: not enough runs ({ {k: len(v) for k, v in s.items()} })")
        return
    print(f"train {len(s['train'])}, val {len(s['val'])}, test {len(s['test'])} runs; device {a.device}", flush=True)
    enc = Encoder(s["train"], hybrid=a.hybrid)
    name = f"{a.model}{'_hybrid' if a.hybrid else ''}{f'_f{round(100 * a.train_frac)}' if a.train_frac < 1 else ''}"
    tr, va = build(s["train"], enc, a.stride, a.device), build(s["val"], enc, a.stride, a.device)
    ntr, nva = len(tr["k"]), len(va["k"])
    kw = {"width": a.width} if a.model == "fno" else {"base": a.width}
    net = MODELS[a.model](enc.channels, cout=2, **kw).to(a.device)
    print(f"pcm {name}: {sum(p.numel() for p in net.parameters()) / 1e6:.2f} M parameters, {ntr} train / {nva} val samples", flush=True)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, a.lr, total_steps=a.epochs * -(-ntr // a.batch))
    # per outdir and seed (2026-11-04): two workers on one machine (pc5a/pc5b) must not share a checkpoint
    os.makedirs(os.path.join(HERE, a.outdir, "ckpt"), exist_ok=True)
    ckpt = os.path.join(HERE, a.outdir, "ckpt", f"ckpt_pcm_{name}{f'_s{a.seed}' if a.seed else ''}_{a.split}.pt")
    best = float("inf")
    for ep in range(a.epochs):
        t0 = time.time()
        net.train()
        tl = torch.zeros((), device=a.device)
        for x, y, m in batches(tr, a.batch, True):
            with torch.autocast("cuda", dtype=torch.bfloat16, enabled=a.amp):
                out = net(x)
            loss = masked_mse(out.float(), y, m)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            tl += loss.detach() * len(x)
        net.eval()
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16, enabled=a.amp):
            vl = sum(masked_mse(net(x).float(), y, m).item() * len(x) for x, y, m in batches(va, a.batch, False)) / max(nva, 1)
        if vl < best:
            best = vl
            torch.save(net.state_dict(), ckpt)
        if (ep + 1) % 10 == 0 or ep == 0:
            print(f"epoch {ep + 1:3d}  train RMSE {np.sqrt(tl.item() / ntr):.4f}  val RMSE {np.sqrt(vl):.4f}  "
                  f"{time.time() - t0:5.1f} s", flush=True)
    net.load_state_dict(torch.load(ckpt))
    res, per_run = pcm_evaluate.evaluate(Predictor(net, enc, a.device), s["test"], a.stride)
    print({k: round(v, 4) for k, v in res.items()}, flush=True)
    out_name = name if a.seed == 0 else f"{name}_s{a.seed}"
    pcm_evaluate.save(a.split, {k: len(v) for k, v in s.items()}, sum(map(len, s.values())), a.stride,
                      out_name, res, per_run, {"epochs": a.epochs, "width": a.width, "seed": a.seed,
                                               "best_val_rmse": float(np.sqrt(best)), "train_frac": a.train_frac,
                                               "train_min": round((time.time() - t_start) / 60, 1)},
                      outdir=a.outdir)


if __name__ == "__main__":
    main()
