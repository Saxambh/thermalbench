#!/usr/bin/env python3
"""Mesh convergence: compare L1 (5 mm), L2 (3.33 mm), L3 (2.22 mm) runs at common times.
Uses the centreline T profiles (sets function object) and the volume-mean T log.
Reports thermocline height and 10-90 % thickness per level, profile differences vs L3,
and Grid Convergence Index (Celik et al. 2008) for the thermocline height (r = 1.5)."""
import math
import os
import sys

import numpy as np

BASE = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/of_runs/convergence")
TC, TH = 293.15, 333.15


def profiles(case):
    root = f"{case}/postProcessing/profile"
    out = {}
    if not os.path.isdir(root):
        return out
    for d in os.listdir(root):
        p = f"{root}/{d}/centreline_T.xy"
        if os.path.exists(p):
            a = np.loadtxt(p)
            out[round(float(d), 3)] = (a[:, 0], a[:, 1])
    return out


def crossing(y, T, level):
    th = TC + level * (TH - TC)
    for j in range(len(y) - 1, 0, -1):
        a, b = T[j - 1] - th, T[j] - th
        if a * b < 0 or a == 0:
            return y[j - 1] + (y[j] - y[j - 1]) * a / (a - b) if a != b else y[j - 1]
    return float("nan")


def gci(f1, f2, f3, r=1.5):
    """f1 fine ... f3 coarse. Returns order p, extrapolated value, GCI_fine (%)."""
    e21, e32 = f2 - f1, f3 - f2
    if e21 == 0 or e32 == 0 or e32 / e21 <= 0:
        return float("nan"), float("nan"), float("nan")   # oscillatory or exact
    p = abs(math.log(abs(e32 / e21))) / math.log(r)
    f_ext = f1 + (f1 - f2) / (r ** p - 1)
    return p, f_ext, 1.25 * abs((f1 - f2) / f1) / (r ** p - 1) * 100


for reg in ("lam", "tur"):
    P = {L: profiles(f"{BASE}/{reg}_{L}") for L in ("L1", "L2", "L3")}
    times = sorted(set(P["L1"]) & set(P["L2"]) & set(P["L3"]))
    print(f"\n=== {reg}: common snapshot times {times[0] if times else '-'} to {times[-1] if times else '-'} s ({len(times)})")
    print("   t_s | y_mid L1   L2    L3  | thick L1   L2    L3  | RMS dT vs L3 (K): L1   L2")
    rows = []
    for t in times:
        r = {}
        for L in ("L1", "L2", "L3"):
            y, T = P[L][t]
            r[L] = (crossing(y, T, 0.5), crossing(y, T, 0.9) - crossing(y, T, 0.1), y, T)
        y3, T3 = r["L3"][2], r["L3"][3]
        rms = {L: float(np.sqrt(np.mean((np.interp(y3, r[L][2], r[L][3]) - T3) ** 2))) for L in ("L1", "L2")}
        rows.append((t, r, rms))
    step = max(1, len(rows) // 12)
    for t, r, rms in rows[::step] + ([rows[-1]] if rows and rows[-1] is not rows[::step][-1] else []):
        print(f"{t:6.0f} | {r['L1'][0]:.3f} {r['L2'][0]:.3f} {r['L3'][0]:.3f} | "
              f"{r['L1'][1]:.3f} {r['L2'][1]:.3f} {r['L3'][1]:.3f} | {rms['L1']:6.2f} {rms['L2']:6.2f}")
    # GCI on thermocline height at times where the thermocline is inside the tank
    g = [gci(r["L3"][0], r["L2"][0], r["L1"][0]) for t, r, _ in rows
         if all(0.1 < r[L][0] < 0.9 for L in ("L1", "L2", "L3"))]
    ok = [x for x in g if not math.isnan(x[2])]
    print(f"GCI(y_mid, fine mesh): {len(ok)} of {len(g)} times monotone; "
          + (f"median {np.median([x[2] for x in ok]):.2f} %, max {max(x[2] for x in ok):.2f} %, "
             f"median order p {np.median([x[0] for x in ok]):.2f}" if ok else "n/a"))
    dy = [abs(r["L1"][0] - r["L3"][0]) for t, r, _ in rows if all(0.1 < r[L][0] < 0.9 for L in ("L1", "L2", "L3"))]
    if dy:
        print(f"|y_mid L1 - L3|: mean {np.mean(dy)*1000:.1f} mm, max {max(dy)*1000:.1f} mm "
              f"(5 mm cells; tank height 1000 mm)")
    for L in ("L1", "L2", "L3"):
        f = f"{BASE}/{reg}_{L}/postProcessing/meanT/0/volFieldValue.dat"
        if os.path.exists(f):
            a = np.loadtxt(f, comments="#")
            tt = times[-1] if times else a[-1, 0]
            print(f"  meanT {L} at {tt:.0f} s: {np.interp(tt, a[:, 0], a[:, 1]):.4f} K")
