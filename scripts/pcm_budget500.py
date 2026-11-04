"""Core-hours of the 500-case PCM design under several options (budget only).
Time step: Courant-limited, dt_Co = 0.1 s * (h / 0.5 mm) * sqrt(26.5 K / dT) (Kamkari 0.5 mm
runs sit at Co ~ 1 with dt 0.1 s), capped at maxDeltaT."""
import math, sys, os
import numpy as np
from scipy.stats import qmc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcm_budget import t_est, C, WALL_PER_SIM

rng = np.random.default_rng(0)
u = qmc.Sobol(d=5, scramble=True, seed=1).random(512)[:500]


def design(sh_lo=5, sh_hi=30, W_lo=0.02, W_hi=0.1):
    out = []
    for i, x in enumerate(u):
        mat = "octadecane" if i % 2 == 0 else "lauric"
        N = 0 if rng.random() < 0.3 else int(rng.integers(1, 6))
        tilt = rng.choice([0, 45, 90], p=[0.7, 0.15, 0.15])
        out.append((mat, sh_lo + x[0] * (sh_hi - sh_lo), 0.5 + x[1] * 19.5, W_lo + x[2] * (W_hi - W_lo), N, int(tilt)))
    return out


def total(cases, h=0.0005, maxdt=0.1, tcap_h=None):
    hrs, tm = [], []
    for mat, sh, sub, W, N, tilt in cases:
        t, _ = t_est(mat, sh, sub, W, 0.1, N, tilt, C)
        t = min(t * 1.05, tcap_h * 3600) if tcap_h else t * 1.05
        dt = min(maxdt, 0.1 * (h / 0.0005) * math.sqrt(26.5 / sh))
        cells = (W / h) * (0.1 / h)
        hrs.append(t / dt * cells * WALL_PER_SIM * 0.1 / 3600)
        tm.append(t / 3600)
    hrs = np.array(hrs)
    return hrs.sum(), np.median(hrs), np.percentile(hrs, 95), hrs.max(), np.max(tm)


rows = [
    ("plan as drafted: SH 5-30 K, W 20-100 mm, 0.5 mm, maxDeltaT 0.1", design(), dict()),
    ("same, maxDeltaT up to Courant limit (cap 0.5 s)", design(), dict(maxdt=0.5)),
    ("same, 1 mm mesh, Courant-limited", design(), dict(h=0.001, maxdt=0.5)),
    ("SH 10-30 K, W 20-60 mm, 0.5 mm, Courant-limited", design(10, 30, 0.02, 0.06), dict(maxdt=0.5)),
    ("SH 10-30 K, W 20-60 mm, 1 mm, Courant-limited", design(10, 30, 0.02, 0.06), dict(h=0.001, maxdt=0.5)),
    ("SH 5-30 K, W 20-100 mm, 0.5 mm, Courant-limited, stop at 8 h simulated", design(), dict(maxdt=0.5, tcap_h=8)),
]
print("core-hours for 500 cases at the lab's measured per-core speed (~1000 core-h/day on all PCs)")
for name, cases, kw in rows:
    tot, med, p95, mx, tmax = total(cases, **kw)
    print(f"  {name}\n      total {tot:7.0f} core-h (~{tot / 1000:4.1f} days), median case {med:5.1f} h, "
          f"95th pct {p95:6.0f} h, slowest {mx:6.0f} core-h ({tmax:4.1f} h of melting)")
