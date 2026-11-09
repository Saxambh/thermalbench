"""Outlet temperature of the Lou et al. (2023) tank: our 3D OpenFOAM run vs their experiment.

Experiment: Fig. 15a, initial (uniform) baffle, Qin = 1 L/min, Th = 333.15 K into Tc = 293.15 K, digitised
by curve colour from the publisher's high-resolution image (digitise.py -> fig15_333K_initial.json).
Ri_bulk = g beta (Tin - Tout) H / vin^2 is linear in Tin - Tout, so T*_out = 1 - Ri(t*) / Ri0 with Ri0 the
plateau before breakthrough (mean over t* 0.2 to 0.6, where Tout = Tc). t* = t Qin / V_tank, V_tank = 14.1 L
(their Eq. 25), so t* = 1 at 846 s.
Ours: area-averaged outlet-port temperature (postProcessing/outletT), T* = (T - Tc) / (Th - Tc); the port is
10 mm in diameter, so area and flow weighting differ little.
Digitising uncertainty: about +-0.01 in Ri (one pixel is 0.0019 in Ri; line width ~4 px), i.e. about +-0.01 in T*.
Writes compare.json and prints the comparison on a common t* grid.
"""
import glob, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
T_REF = 14.1e-3 / (1.0e-3 / 60)          # s, V_tank / Qin
TC, TH = 293.15, 333.15

d = json.load(open(os.path.join(HERE, "fig15_333K_initial.json")))
ri = np.array(d["Ri"])
ri0 = ri[(ri[:, 0] >= 0.2) & (ri[:, 0] <= 0.6), 1].mean()
lou_t, lou_T = ri[:, 0], 1 - ri[:, 1] / ri0

ours = []
for f in sorted(glob.glob(os.path.join(HERE, "ours_outletT_*.dat"))):
    a = np.loadtxt(f, comments="#")
    ours.append(a)
o = np.vstack(ours)
o = o[np.argsort(o[:, 0])]
o_t, o_T = o[:, 0] / T_REF, (o[:, 1] - TC) / (TH - TC)

grid = np.round(np.arange(0.50, 1.501, 0.05), 3)
rows = []
for t in grid:
    l = float(np.interp(t, lou_t, lou_T)) if lou_t.min() <= t <= lou_t.max() else None
    w = float(np.interp(t, o_t, o_T)) if o_t.min() <= t <= o_t.max() else None
    rows.append({"t_star": float(t), "t_s": float(t * T_REF), "lou": l, "ours": w,
                 "diff": None if l is None or w is None else w - l})
both = [r for r in rows if r["diff"] is not None]
summary = {"Ri0": float(ri0), "t_ref_s": T_REF, "ours_t_star_max": float(o_t.max()),
           "n_compared": len(both),
           "mean_diff": float(np.mean([r["diff"] for r in both])) if both else None,
           "rms_diff": float(np.sqrt(np.mean([r["diff"] ** 2 for r in both]))) if both else None,
           "max_abs_diff": float(max(abs(r["diff"]) for r in both)) if both else None}
# breakthrough timing: t* where T*_out first reaches 0.1 and 0.5
for lev in (0.1, 0.5):
    for name, tt, TT in (("lou", lou_t, lou_T), ("ours", o_t, o_T)):
        k = np.where(TT >= lev)[0]
        summary[f"t_star_at_{lev}_{name}"] = float(tt[k[0]]) if len(k) else None
json.dump({"summary": summary, "rows": rows}, open(os.path.join(HERE, "compare.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
fmt = lambda v, s="": "" if v is None else format(v, s + ".3f")
for r in rows:
    print(f"t* {r['t_star']:.2f} ({r['t_s']:6.0f} s)  Lou {fmt(r['lou']):>6}  ours {fmt(r['ours']):>6}  diff {fmt(r['diff'], '+')}")
