"""Training throughput on the GPU for the full-size problem: seconds per training sample
(forward + backward + step) for each model, batch size and precision, on synthetic inputs of
the real shape [B, C, 200, 200]. Used to set the epoch/seed budget for the full dataset.

  python bench_train.py
"""
import time

import torch

from models import MODELS

C, NY, NX = 19, 200, 200          # hybrid input channels (plain models use 18)
dev = "cuda"
for name, kw in (("fno", {"width": 32}), ("unet", {"base": 32})):
    for amp in (False, True):
        for bs in (8, 16, 32):
            torch.manual_seed(0)
            net = MODELS[name](C, **kw).to(dev)
            opt = torch.optim.AdamW(net.parameters(), 1e-3)
            x = torch.randn(bs, C, NY, NX, device=dev)
            y = torch.randn(bs, 1, NY, NX, device=dev)
            try:
                for it in range(13):
                    if it == 3:
                        torch.cuda.synchronize()
                        t0 = time.time()
                    with torch.autocast("cuda", dtype=torch.bfloat16, enabled=amp):
                        out = net(x)
                    loss = ((out.float() - y) ** 2).mean()
                    opt.zero_grad()
                    loss.backward()
                    opt.step()
                torch.cuda.synchronize()
                per = (time.time() - t0) / (10 * bs)
                mem = torch.cuda.max_memory_allocated() / 1e9
                print(f"{name:5s} amp={amp!s:5s} batch {bs:2d}: {1000 * per:6.2f} ms/sample  peak {mem:.2f} GB", flush=True)
            except torch.cuda.OutOfMemoryError:
                print(f"{name:5s} amp={amp!s:5s} batch {bs:2d}: out of memory", flush=True)
            del net, opt
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
