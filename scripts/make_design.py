#!/usr/bin/env python3
"""ThermBench tank family: build the case list (design) as CSV.

Full design: scrambled Sobol sample (fixed seed) over
  u_in 0.005-0.2 m/s (log), dT 5-50 K, slot s 20-80 mm, port offset 0-0.2 H,
  width W 0.25-1.0 m (H = 1 m), plus categorical draws:
  inlet type A/B (70/30), mode charge/discharge (70/30), start uniform/pre-stratified (70/30).
Pilot: 20 hand-picked cases at the corners of that space.

Geometry is snapped to a 10 mm grid that fits both the 5 mm and the 3.33 mm mesh
(type B also needs (W - s)/2 on the grid, so W may move by 10 mm). Fidelity subset:
the first 128 Sobol points (12.5 %, evenly spread), rerun at 3.33 mm. Turbulence: laminar if Re < 1500, k-omega SST with
buoyancyTurbSource if Re > 3000, both if 1500 <= Re <= 3000 (two rows, same case id).

Usage: make_design.py --h 0.005 [--n 1024] [--seed 2026] [--out design]
                      [--fine-h 0.0033333333333 --n-fine 128]
"""
import argparse
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_tank_case as gen  # noqa: E402

T_COLD = 20.0  # C, cold water temperature for every case
H = 1.0


def snap(v, step, lo, hi):
    return min(max(round(v / step) * step, lo), hi)


GRID = 0.01  # geometry grid (m): fits both the 5 mm and the 3.33 mm mesh


def build(cid, u, dT, s, off, W, itype, mode, yi, h):
    s = snap(s, GRID, 0.02, 0.08)
    W = snap(W, GRID, 0.25, 1.0)
    if itype == "B" and round((W - s) / GRID) % 2:   # centred slot: (W - s)/2 on the grid
        W = W + GRID if W + GRID <= 1.0 + 1e-9 else W - GRID
    off = snap(off, GRID, 0.0, 0.2 * H)
    th, tc = T_COLD + dT, T_COLD
    tin, t0 = (th, tc) if mode == "charge" else (tc, th)
    if yi is None:
        tstar = 1.2
    else:  # water still to be replaced: cold part (charge) or hot part (discharge)
        yi = round(yi, 3)
        tstar = round((yi if mode == "charge" else 1 - yi) + 0.2, 3)
    nu, beta, _ = gen.nu_beta_alpha(0.5 * (tin + t0) + 273.15)
    Re = u * s / nu
    Ri = 9.81 * beta * dT * H / u ** 2
    models = ["laminar"] if Re < 1500 else ["kOmegaSST"] if Re > 3000 else ["laminar", "kOmegaSST"]
    rows = []
    for m in models:
        rows.append({"case_id": cid, "run_id": f"{cid}_{'lam' if m == 'laminar' else 'sst'}",
                     "turb": m, "u_in": round(u, 6), "dT": round(dT, 3), "T_in": round(tin, 3),
                     "T_0": round(t0, 3), "s": round(s, 4), "off": round(off, 4), "W": round(W, 4),
                     "H": H, "inlet_type": itype, "mode": mode,
                     "yi": "" if yi is None else yi, "tstar": tstar, "h": h,
                     "Re": round(Re, 1), "Ri": round(Ri, 3), "AR": round(H / W, 3),
                     "end_s": round(tstar * W * H / (u * s), 2)})
    return rows


def args_for(r):
    """make_tank_case.py arguments for one design row."""
    a = ["--props", "real", "--h", str(r["h"]), "--uin", str(r["u_in"]),
         "--tin", str(r["T_in"]), "--t0", str(r["T_0"]), "--W", str(r["W"]), "--H", str(r["H"]),
         "--s", str(r["s"]), "--off", str(r["off"]), "--inlet-type", r["inlet_type"],
         "--mode", r["mode"], "--tstar", str(r["tstar"]), "--nsnap", "120"]
    if r["yi"] != "":
        a += ["--yi", str(r["yi"])]
    if r["turb"] != "laminar":
        a += ["--turb", "kOmegaSST", "--buoy"]
    return a


def full(n, seed, h):
    from scipy.stats import qmc
    x = qmc.Sobol(d=9, scramble=True, seed=seed).random(n)
    rows = []
    for i, p in enumerate(x):
        u = 10 ** (math.log10(0.005) + p[0] * (math.log10(0.2) - math.log10(0.005)))
        dT = 5 + 45 * p[1]
        s = 0.02 + 0.06 * p[2]
        off = 0.2 * H * p[3]
        W = 0.25 + 0.75 * p[4]
        itype = "A" if p[5] < 0.7 else "B"
        mode = "charge" if p[6] < 0.7 else "discharge"
        yi = None if p[7] < 0.7 else 0.3 + 0.6 * p[8]
        rows += build(f"T{i:04d}", u, dT, s, off, W, itype, mode, yi, h)
    return rows


def pilot(h):
    P = []
    k = 0

    def add(*a):
        nonlocal k
        P.extend(build(f"P{k:02d}", *a, h))
        k += 1
    # corners: flow x dT x inlet type (reference geometry s 40 mm, off 60 mm, W 0.5 m)
    for itype in ("A", "B"):
        for u in (0.005, 0.2):
            for dT in (5, 50):
                add(u, dT, 0.04, 0.06, 0.5, itype, "charge", None)
    add(0.03, 30, 0.04, 0.06, 0.25, "A", "charge", None)    # tallest tank (AR 4)
    add(0.03, 30, 0.04, 0.06, 1.0, "A", "charge", None)     # widest tank (AR 1), most expensive
    add(0.03, 30, 0.02, 0.0, 0.5, "A", "charge", None)      # narrowest slot, port at the lid
    add(0.03, 30, 0.08, 0.2, 0.5, "A", "charge", None)      # widest slot, lowest port
    add(0.02, 40, 0.04, 0.06, 0.5, "A", "discharge", None)
    add(0.1, 10, 0.04, 0.06, 0.5, "B", "discharge", None)
    add(0.005, 50, 0.08, 0.06, 1.0, "A", "discharge", None)  # slowest, widest: longest run
    add(0.03, 30, 0.04, 0.06, 0.5, "A", "charge", 0.6)       # pre-stratified charge
    add(0.03, 30, 0.04, 0.06, 0.5, "B", "discharge", 0.4)    # pre-stratified discharge
    add(0.055, 30, 0.04, 0.06, 0.5, "A", "charge", None)     # transition band: laminar AND SST
    add(0.08, 20, 0.04, 0.06, 0.5, "A", "charge", None)      # turbulent mid-range
    add(0.01, 15, 0.06, 0.1, 0.75, "B", "charge", None)      # laminar mid-range
    return P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h", type=float, default=0.005)
    ap.add_argument("--n", type=int, default=1024, help="power of 2 keeps Sobol balance")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default="design")
    ap.add_argument("--fine-h", type=float, default=None,
                    help="also write the fidelity subset at this cell size (e.g. 0.0033333333333)")
    ap.add_argument("--n-fine", type=int, default=128, help="Sobol points in the fidelity subset")
    a = ap.parse_args()
    sets = [("pilot", pilot(a.h)), ("full", full(a.n, a.seed, a.h))]
    if a.fine_h:  # fidelity subset: first n_fine Sobol points, same cases on the finer mesh
        fine = [r for r in full(a.n, a.seed, a.fine_h) if int(r["case_id"][1:]) < a.n_fine]
        sets.append((f"fine{len(set(r['case_id'] for r in fine))}", fine))
    for name, rows in sets:
        path = f"{a.out}_{name}.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        lam = sum(r["turb"] == "laminar" for r in rows)
        print(f"{path}: {len(rows)} runs ({len(set(r['case_id'] for r in rows))} cases), "
              f"laminar {lam}, SST {len(rows) - lam}, "
              f"Re {min(r['Re'] for r in rows):.0f}-{max(r['Re'] for r in rows):.0f}, "
              f"Ri {min(r['Ri'] for r in rows):.2g}-{max(r['Ri'] for r in rows):.3g}")


if __name__ == "__main__":
    main()
