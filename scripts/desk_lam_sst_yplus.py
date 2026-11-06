"""Desk checks on the frozen tank data (2026-11-06, read-only).
A) all designs run with both laminar and k-omega SST: how different are the two solutions?
B) every SST run: wall y+ from the first-cell tangential velocity, inverted with Spalding's law."""
import csv, json, os, sys
import numpy as np, h5py
A = os.path.dirname(os.path.abspath(__file__)) + "/../audit"
loc = json.load(open(A + "/loc.json"))
meta = {r["simulation_id"]: r for r in csv.DictReader(open("/mnt/d/ThermBench_data/samples/tank_master_metadata.csv"))}
def nu_w(TK):  # water kinematic viscosity (m2/s), Poiseuille-type fit, T in C
    t = TK - 273.15; return 1.79e-6 / (1 + 0.0337 * t + 0.000221 * t * t)
def h5(rid): return h5py.File(loc[rid][0] + "/thermbench.h5", "r")
out = sys.argv[1]
# ---------- A: laminar vs SST pairs
pairs = sorted({r[:-4] for r in loc if r.endswith("_lam")} & {r[:-4] for r in loc if r.endswith("_sst")})
rows = []
for c in pairs:
    m = meta[c + "_lam"]; dT = abs(float(m["inlet_temperature_K"]) - float(m["initial_temperature_K"]))
    with h5(c + "_lam") as a, h5(c + "_sst") as b:
        n = min(len(a["times_s"]), len(b["times_s"]))
        Ta, Tb = a["fields/T"][1:n], b["fields/T"][1:n]
        d = Ta - Tb
        To = np.interp(b["series/T_out_t_s"][:], a["series/T_out_t_s"][:], a["series/T_out_K"][:]) - b["series/T_out_K"][:]
        Ea, Eb = a["metrics/E_J"][:n], b["metrics/E_J"][:n]
        ya, yb = a["metrics/y_mid_m"][:n], b["metrics/y_mid_m"][:n]; ok = np.isfinite(ya) & np.isfinite(yb)
        nut = b["fields/nut"][1:n] if "fields/nut" in b else None
        nr = nut / nu_w(Tb) if nut is not None else None
        rows.append(dict(case=c, Re=float(m["Re_in"]), Ri=float(m["Ri_H"]), inlet=m["inlet_design"][0], mode=m["operation"],
            init=m["initial_condition"], W=float(m["tank_width_m"]), s=float(m["slot_height_m"]),
            field_pct=float(100 * np.sqrt(np.mean(d ** 2)) / dT),
            profile_pct=float(100 * np.sqrt(np.mean((Ta.mean(2) - Tb.mean(2)) ** 2)) / dT),
            Tout_pct=float(100 * np.sqrt(np.mean(To ** 2)) / dT),
            E_pct=float(100 * np.max(np.abs(Ea - Eb)) / max(np.max(np.abs(Eb - Eb[0])), 1e-30)),
            ymid_mm=float(1000 * np.mean(np.abs(ya[ok] - yb[ok]))) if ok.any() else None,
            nut_ratio_max=float(nr.max()) if nr is not None else None,
            nut_ratio_mean=float(nr.mean()) if nr is not None else None,
            nut_ratio_p99=float(np.percentile(nr, 99)) if nr is not None else None))
    print("A", c, round(rows[-1]["field_pct"], 2), flush=True)
# ---------- B: y+ of every SST run
K, B_ = 0.41, 5.2
def spalding_yplus(up, yp, nu):
    """solve y uτ/ν = u+ + e^-κB (e^κu+ - 1 - κu+ - (κu+)^2/2 - (κu+)^3/6), u+ = up/uτ, for uτ; return y+"""
    up = np.maximum(up, 1e-12); lo, hi = np.full(up.shape, -9.0), np.full(up.shape, 0.0)   # log10 uτ
    for _ in range(60):
        mid = (lo + hi) / 2; ut = 10 ** mid; upl = up / ut; ku = K * upl
        f = yp * ut / nu - (upl + np.exp(-K * B_) * (np.exp(np.minimum(ku, 50)) - 1 - ku - ku ** 2 / 2 - ku ** 3 / 6))
        lo = np.where(f < 0, mid, lo); hi = np.where(f >= 0, mid, hi)
    return yp * 10 ** ((lo + hi) / 2) / nu
yrows = []
for rid in sorted(r for r in loc if r.endswith("_sst")):
    with h5(rid) as f:
        cj = json.load(open(loc[rid][0] + "/case.json")); h = cj["mesh_h_m"]
        ux, uy, T = f["fields/ux"][1:], f["fields/uy"][1:], f["fields/T"][1:]
    ut = np.concatenate([np.abs(uy[:, :, 0]), np.abs(uy[:, :, -1]), np.abs(ux[:, 0, :]), np.abs(ux[:, -1, :])], axis=1)
    Tw = np.concatenate([T[:, :, 0], T[:, :, -1], T[:, 0, :], T[:, -1, :]], axis=1)
    yp = spalding_yplus(ut, h / 2, nu_w(Tw))
    yrows.append(dict(run=rid, Re=float(meta[rid]["Re_in"]), yplus_max=float(yp.max()), yplus_p99=float(np.percentile(yp, 99)),
        yplus_median=float(np.median(yp)), share_below5=float(np.mean(yp < 5)), share_5_30=float(np.mean((yp >= 5) & (yp < 30))),
        share_above30=float(np.mean(yp >= 30))))
    print("B", rid, round(yrows[-1]["yplus_max"], 1), flush=True)
json.dump(dict(pairs=rows, yplus=yrows), open(out, "w"), indent=1)
print("done", len(rows), "pairs", len(yrows), "SST runs")
