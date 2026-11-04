"""Recalibrated PCM cost from the pilot's measured pace (2026-11-03, 9 lab cases, 13.5 h in).
wall per case = 1.15 t_est (stop at 0.995; P0dt 1.17) / dt(sh, N) * cells * c_step(N)
  c_step [s per step per cell]: 0 fins 29e-6, 1 fin 30e-6, 5 fins 72e-6 (linear in between)
  dt [s]: 0.125 (sh/8)^-0.34 * (1 - 0.074 N)   (no fin 8 K 0.12-0.135, 30 K 0.056-0.106;
          5 fins 8 K 0.07-0.09; 1 fin 19 K 0.077)
c_step is on the lab at 22 jobs / 16 cores; a less loaded machine is faster."""
import csv, heapq, os, sys, numpy as np
f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "pcm_full.csv")
rows = list(csv.DictReader(open(f)))
def wall_h(r):
    N, sh, W, h = int(r["nfins"]), float(r["superheat_K"]), float(r["W_m"]), float(r["h_m"])
    cells = round(W / h) * round(0.1 / h)
    c = np.interp(N, [0, 1, 5], [29e-6, 30e-6, 72e-6])
    dt = 0.125 * (sh / 8) ** -0.34 * (1 - 0.074 * N)
    return 1.15 * float(r["t_melt_est_h"]) * 3600 / dt * cells * c / 3600
w = np.array([wall_h(r) for r in rows]); old = np.array([float(r["core_h_est"]) for r in rows])
N = np.array([int(r["nfins"]) for r in rows])
print(f"{len(rows)} cases: old {old.sum():.0f} core-h, new {w.sum():.0f} core-h (x{w.sum()/old.sum():.1f}); "
      f"per case median {np.median(w):.1f} h, 90 % {np.percentile(w,90):.0f} h, max {w.max():.0f} h")
for n in range(6):
    s = N == n
    print(f"  {n} fins: {s.sum():3d} cases, {w[s].sum():6.0f} core-h, max {w[s].max():5.0f} h")
print("longest 8:", ", ".join(f"{rows[i]['case_id']} {w[i]:.0f} h (N{N[i]}, sh {float(rows[i]['superheat_K']):.0f}, "
      f"t_melt {rows[i]['t_melt_est_h']} h)" for i in np.argsort(-w)[:8]))
for slots in (48, 64, 80):
    load = [0.0] * slots
    for x in sorted(w, reverse=True): heapq.heapreplace(load, load[0] + x)
    print(f"  {slots} slots (longest first): all done in {max(load)/24:.1f} days")
