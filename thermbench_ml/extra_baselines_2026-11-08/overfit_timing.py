"""Transolver code check and timing (8 November 2026, PLAN.md). Training data only; no validation or test data.

1. Overfit: one fixed batch of 8 training samples (first runs of the random split's training set), 400
   AdamW steps at lr 1e-3 with bf16 autocast as in the real jobs; the masked RMSE must fall to near zero.
2. Timing and memory: forward + backward at the real job batch (16) on the largest training grid of the
   family, bf16 autocast; reports seconds per step and peak GPU memory.
  python overfit_timing.py tank|pcm
"""
import os, sys, time
import numpy as np
import torch
ML = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ML); os.chdir(ML)
from models import MODELS

fam = sys.argv[1]
ARCH = sys.argv[2] if len(sys.argv) > 2 else "transolver"
KW = {"fno": {"width": 32}, "unet": {"base": 32}}.get(ARCH, {"base": 32, "patch": int(ARCH.rstrip("c")[-1]), "conv": ARCH.endswith("c")})
ARCH = "transolver" if ARCH.startswith("transolver") else ARCH
dev = "cuda"
torch.manual_seed(0)
if fam == "tank":
    import train
    from data import index, DEFAULT_ROOTS
    from splits import split_runs
    s = split_runs(index(DEFAULT_ROOTS, manifest="manifest_full_h5mm.json"), "random")
    enc = train.Encoder(s["train"], hybrid=True, canon=True)
    big = max(s["train"], key=lambda r: r.meta["ny"])
    few = train.Samples(s["train"][:2], enc, 10)
    xs, ys, ms = zip(*[few[i] for i in range(8)])
    x, y, m = torch.stack(xs), torch.stack(ys), torch.stack(ms)
    bigs = train.Samples([big], enc, 10)
    bx = torch.stack([bigs[i % len(bigs)][0] for i in range(16)])
    cin, cout, loss_f = enc.channels, 1, train.masked_mse
else:
    import pcm_train
    from pcm_data import index, DEFAULT_ROOTS
    from pcm_splits import split_runs
    s = split_runs(index(DEFAULT_ROOTS, manifest="manifest_pcm.json"), "random")
    enc = pcm_train.Encoder(s["train"], hybrid=True)
    d = pcm_train.build(s["train"][:2], enc, 10, dev)
    x, y, m = next(pcm_train.batches(d, 8, False))
    bx = next(pcm_train.batches(d, 16, False))[0]   # PCM grids are all the same size (padded)
    cin, cout, loss_f = enc.channels, 2, pcm_train.masked_mse
x, y, m, bx = x.to(dev), y.to(dev), m.to(dev), bx.to(dev)
net = MODELS[ARCH](cin, cout=cout, **KW).to(dev)
print(f"{fam} {ARCH} {KW}: {sum(p.numel() for p in net.parameters()) / 1e6:.2f} M parameters; overfit batch {tuple(x.shape)}; timing batch {tuple(bx.shape)}", flush=True)
LR, STEPS = float(os.environ.get("LR", "1e-3")), int(os.environ.get("STEPS", "400"))
opt = torch.optim.AdamW(net.parameters(), lr=LR, weight_decay=1e-4)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, LR, total_steps=STEPS + 1) if os.environ.get("ONECYCLE") else None
print(f"  lr {LR}, steps {STEPS}, onecycle {bool(sched)}", flush=True)
for step in range(STEPS + 1):
    with torch.autocast("cuda", dtype=torch.bfloat16):
        out = net(x)
    loss = loss_f(out.float(), y, m)
    opt.zero_grad(); loss.backward(); opt.step()
    if sched: sched.step()
    if step % (STEPS // 8) == 0:
        print(f"  step {step:3d}  masked RMSE {loss.item() ** 0.5:.4f}", flush=True)
torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize()
times = []
for i in range(6):
    t0 = time.time()
    with torch.autocast("cuda", dtype=torch.bfloat16):
        out = net(bx)
    out.float().mean().backward(); opt.zero_grad(); torch.cuda.synchronize()
    times.append(time.time() - t0)
print(f"  timing: {np.median(times[1:]):.3f} s per step at batch 16, peak memory {torch.cuda.max_memory_allocated() / 2**30:.2f} GB", flush=True)
for arch, kw in (() if ARCH != "transolver" else (("fno", {"width": 32}),)):   # same timing for the existing models, for the cost ratio
    ref = MODELS[arch](cin, cout=cout, **kw).to(dev)
    times = []
    for i in range(6):
        t0 = time.time()
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = ref(bx)
        out.float().mean().backward(); torch.cuda.synchronize()
        times.append(time.time() - t0)
    print(f"  {arch}: {np.median(times[1:]):.3f} s per step at batch 16", flush=True)
