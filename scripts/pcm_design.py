#!/usr/bin/env python3
"""ThermBench PCM family: design tables (full Sobol design and the corner pilot).

Every case is one make_pcm_case.py command line. Ranges, mesh and model settings are at the
top (SETTINGS / RANGES); the lauric-acid and fin settings were frozen on 2026-11-02 after the
Kamkari validation runs. Cases are defined in unit coordinates and mapped onto RANGES, so the pilot follows
any change of range. H = 100 mm, closed box, all walls no-slip, heated wall at x = 0.

Usage: pcm_design.py pilot|full <out.csv> [--h 0.0005] [--sh 5,30] [--W 0.02,0.1]
Writes a CSV with case_id, the parameters, the estimated melting time and core-hours, and
the generator arguments (column 'args').
"""
import argparse
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_pcm_case import MATERIALS     # noqa: E402
from pcm_budget import t_est, C, WALL_PER_SIM   # noqa: E402

H = 0.1
# Model settings per material. octadecane has a true melting point: a +-0.01 K range with the
# coded source reproduces OpenFOAM's isothermal source (verified 2026-11-01) and lets it use
# conducting fins too. lauric: range + Cu 5e6, FROZEN 2026-11-02 (Kamkari 70 C, no fin: 0.575
# at 80 min vs experiment 0.55).
SETTINGS = {
    "octadecane": {"melt_range": (27.99, 28.01), "Cu": 1e6},
    "lauric": {"melt_range": (43.5, 48.2), "Cu": 5e6},
}
# Kamkari's aluminium; FROZEN 2026-11-02 (decision 3): conducting and isothermal fins agree
# within 0.01 for one fin, conducting is the physically right model
FIN = {"model": "conduct", "k": 130.0}
# superheat above the range midpoint (lauric 45.85 C), subcooling below the solidus
# decided 2026-11-02 (Saxam): 0.5 mm mesh (1 mm was 8-11 % off), superheat 8-30 K, W 20-60 mm
RANGES = {"sh": (8.0, 30.0), "sub": (0.5, 20.0), "W": (0.02, 0.06), "Lf": (0.2, 0.8), "tf": (0.001, 0.004)}
TILTS = (0, 45, 90)
MAXDT = 0.5        # cap; the Courant limit (maxCo 1) sets the step in all but gentle cases

# Pilot: corners of the design, the same 12 points for each material, plus one time-step
# check (point 5 again with maxDeltaT 0.1, the validated setting). Unit coordinates:
# (sh, sub, W, N, Lf, tf, tilt)
PILOT = [
    (0.0, 0.0, 0.0, 0, 0, 0, 0),        # gentle, warm start, narrow
    (1.0, 1.0, 1.0, 0, 0, 0, 0),        # strong, cold start, wide
    (0.0, 1.0, 1.0, 0, 0, 0, 0),        # slowest corner
    (1.0, 0.0, 0.0, 0, 0, 0, 0),        # fastest corner
    (0.5, 0.5, 0.5, 1, 0.5, 0.5, 0),    # centre, one fin (Kamkari-like)
    (1.0, 0.0, 0.0, 5, 1.0, 1.0, 0),    # five long thick fins in a narrow box
    (0.0, 1.0, 1.0, 5, 0.0, 0.0, 0),    # five short thin fins in a wide box
    (0.25, 0.75, 0.25, 3, 1.0, 0.0, 0),
    (0.5, 0.5, 0.5, 0, 0, 0, 45),
    (1.0, 1.0, 1.0, 0, 0, 0, 90),       # heated from below, strongest
    (0.0, 0.0, 0.0, 3, 0.5, 1.0, 90),   # heated from below with fins
    (0.75, 0.25, 0.75, 2, 0.25, 0.75, 45),
]


def snap(x, h, lo=None):
    v = round(x / h) * h
    if lo is not None:
        v = max(v, lo)
    return round(v, 10)


def case(cid, mat, u_sh, u_sub, u_W, N, u_Lf, u_tf, tilt, h, maxdt=MAXDT):
    R = RANGES
    lin = lambda k, u: R[k][0] + u * (R[k][1] - R[k][0])
    s = SETTINGS[mat]
    Ts, Tl = s["melt_range"]
    tref = 0.5 * (Ts + Tl)     # the model's reference melting temperature (range midpoint)
    # superheat above the reference (= the generator's Tmelt for Ra and Ste); subcooling below
    # the solidus, so the PCM always starts fully solid
    sh, sub = round(lin("sh", u_sh), 2), round(lin("sub", u_sub), 2)
    W = snap(lin("W", u_W), h)
    Lf = snap(lin("Lf", u_Lf) * W, h, lo=h) if N else 0.0
    tf = snap(lin("tf", u_tf), h, lo=h) if N else 0.0
    t, Ra = t_est(mat, sh, sub + (tref - Ts), W, H, N, tilt, C, tmelt_C=tref)
    write = max(1.0, round(t / 100, 0))            # ~100 snapshots over the expected melt
    end = round(2.5 * t / write) * write           # cap; the run stops itself at 0.995
    dt = min(maxdt, 0.1 * (h / 0.0005) * math.sqrt(26.5 / sh))
    core_h = t / dt * (W / h) * (H / h) * WALL_PER_SIM * 0.1 / 3600
    args = (f"--material {mat} --W {W:g} --H {H:g} --right wall --top wall --tw {tref + sh:g} "
            f"--t0 {Ts - sub:g} --h {h:g} --tilt {tilt} --melt-range {s['melt_range'][0]:g},{s['melt_range'][1]:g} "
            f"--Cu {s['Cu']:g} --maxdt {maxdt:g} --end {end:g} --write {write:g} --stop-at 0.995")
    if N:
        args += f" --nfins {N} --fin-len {Lf:g} --fin-t {tf:g} --fin-model {FIN['model']} --k-fin {FIN['k']:g}"
    return {"case_id": cid, "material": mat, "superheat_K": sh, "subcooling_K": sub, "W_m": W,
            "nfins": N, "fin_len_m": Lf, "fin_t_m": tf, "tilt_deg": tilt, "h_m": h, "maxdt_s": maxdt,
            "Ra_H": f"{Ra:.3g}", "t_melt_est_h": round(t / 3600, 2), "core_h_est": round(core_h, 1),
            "args": args}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["pilot", "full"])
    ap.add_argument("out")
    ap.add_argument("--h", type=float, default=0.0005)
    ap.add_argument("--sh", default=None, help="superheat range lo,hi (K)")
    ap.add_argument("--W", default=None, help="width range lo,hi (m)")
    ap.add_argument("--n", type=int, default=500)
    a = ap.parse_args()
    if a.sh:
        RANGES["sh"] = tuple(float(v) for v in a.sh.split(","))
    if a.W:
        RANGES["W"] = tuple(float(v) for v in a.W.split(","))
    rows = []
    if a.which == "pilot":
        for m, mat in enumerate(("octadecane", "lauric")):
            for k, p in enumerate(PILOT):
                rows.append(case(f"P{m}{k + 1:02d}", mat, *p, h=a.h))
        rows.append(case("P0dt", "octadecane", *PILOT[4], h=a.h, maxdt=0.1))   # time-step check
    else:
        import numpy as np
        from scipy.stats import qmc
        u = qmc.Sobol(d=7, scramble=True, seed=2026).random(1 << math.ceil(math.log2(a.n)))[:a.n]
        for i, x in enumerate(u):
            mat = ("octadecane", "lauric")[int(x[0] * 2)]
            N = 0 if x[3] < 0.3 else 1 + min(4, int((x[3] - 0.3) / 0.7 * 5))
            tilt = 0 if x[6] < 0.7 else 45 if x[6] < 0.85 else 90
            rows.append(case(f"P{i:04d}", mat, x[1], x[2], x[4], N, x[5], (x[5] * 7.3) % 1, tilt, h=a.h))
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    tot = sum(r["core_h_est"] for r in rows)
    print(f"{a.which}: {len(rows)} cases, h = {a.h * 1000:g} mm, superheat {RANGES['sh']}, W {RANGES['W']}: "
          f"~{tot:.0f} core-h, slowest {max(r['core_h_est'] for r in rows):.0f} core-h, "
          f"longest melt {max(r['t_melt_est_h'] for r in rows):.1f} h -> {a.out}")


if __name__ == "__main__":
    main()
