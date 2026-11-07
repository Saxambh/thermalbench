"""Outlet proxy against the flow-weighted (mixing-cup) outlet temperature (7 Nov 2026).

The benchmark's outlet metric uses the cells next to the outlet, which equals the area-averaged outlet-face
temperature (zero-gradient outlet; proxy_check.py: difference < 1e-4 % of dT). A system model receives the
mixing-cup temperature: h_mix = sum(phi h) / sum(phi) over the outlet (series outlet_Hdot / outlet_mdot,
real-property runs), inverted with the cp polynomial of make_tank_case.py. OpenFOAM's sensible enthalpy is
relative to Tstd = 298.15 K; the inversion is checked on the first snapshot, where the outlet sits at T_init.
Per run: |T_mix - T_area| at the scored snapshot times (t > 0), overall and in the breakthrough window.
Writes outlet_mixcup.json and prints a summary.
"""
import json, os, sys
import numpy as np
import h5py

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
sys.path.insert(0, ML)
from data import index, DEFAULT_ROOTS

CP_C = (8.7910736814e+03, -4.0168891060e+01, 1.1524691558e-01, -1.0858585859e-04)
h_int = lambda T: sum(c * T ** (n + 1) / (n + 1) for n, c in enumerate(CP_C))
TSTD = 298.15
Tg = np.linspace(260.0, 380.0, 12001)
hg = h_int(Tg) - h_int(TSTD)
T_of_h = lambda h: np.interp(h, hg, Tg)

rows, skipped = [], {"no_flux_series": 0}
for r in index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_full_h5mm.json")):
    with h5py.File(os.path.join(r.path, "thermbench.h5")) as f:
        if "series/outlet_Hdot" not in f or "series/outlet_mdot" not in f:
            skipped["no_flux_series"] += 1
            continue
        tH, H = f["series/outlet_Hdot_t_s"][:], f["series/outlet_Hdot"][:]
        tm, md = f["series/outlet_mdot_t_s"][:], f["series/outlet_mdot"][:]
        t, Ta = f["times_s"][:], f["metrics/T_out_K"][:]
    dT = r.Th - r.Tc
    s = t > 0
    ts = t[s]
    Hs, ms = np.interp(ts, tH, H), np.interp(ts, tm, md)
    # only snapshots with a well-defined net outflow: at least half the run's median outflow
    ok = ms > 0.5 * np.median(md[np.abs(md) > 0])
    Tmix = np.full(len(ts), np.nan)
    Tmix[ok] = T_of_h(Hs[ok] / ms[ok])
    d = np.abs(Tmix - Ta[s])
    c = np.abs(Ta[s] - Ta[0]) / max(abs(Ta[-1] - Ta[0]), 1e-9)
    ev = (c >= 0.1) & (c <= 0.9) & np.isfinite(d) if abs(Ta[-1] - Ta[0]) > 0.02 * dT else np.zeros(len(d), bool)
    # inversion check: the earliest outflow carries the initial tank temperature
    # (uniform initial field only: a pre-stratified start has no single initial outlet temperature)
    j = int(np.argmax(np.abs(md) > 1e-12))
    T0 = T_of_h(H[j] / md[j]) if np.abs(md[j]) > 1e-12 and r.meta.get("init", "uniform") == "uniform" else np.nan
    rows.append({"run_id": r.run_id, "turb": r.meta["turbulence"], "Ri": r.meta["Ri_H"], "dT": dT,
                 "init": r.meta.get("init", "uniform"), "n_scored": int(ok.sum()), "n_snap": int(len(ts)),
                 "inversion_check_K": float(T0 - r.meta["T_init_K"]),
                 "mean_abs_pct": float(100 * np.nanmean(d) / dT), "max_abs_pct": float(100 * np.nanmax(d) / dT),
                 "event_mean_abs_pct": float(100 * d[ev].mean() / dT) if ev.any() else None,
                 "net_inflow_share": float((ms < 0).mean()) if ms.size else None})
json.dump({"skipped": skipped, "rows": rows}, open(os.path.join(HERE, "outlet_mixcup.json"), "w"), indent=1)
q = lambda a: f"median {np.median(a):.3g}, 90 % {np.percentile(a, 90):.3g}, max {np.max(a):.3g}" if len(a) else "none"
print(len(rows), "runs with flux series; skipped", skipped)
inv = [abs(x["inversion_check_K"]) for x in rows if np.isfinite(x["inversion_check_K"])]
print("inversion check, uniform starts, |T(first outflow) - T_init| K:", q(inv), f"({len(inv)} runs; > 0.5 K: {sum(v > 0.5 for v in inv)})")
print("snapshots kept (well-defined outflow):", q([x["n_scored"] / x["n_snap"] for x in rows]))
print("|T_mix - T_area|, % of dT, run means:", q([x["mean_abs_pct"] for x in rows]))
print("  run maxima:", q([x["max_abs_pct"] for x in rows]))
print("  breakthrough window, run means:", q([x["event_mean_abs_pct"] for x in rows if x["event_mean_abs_pct"] is not None]))
for g in ("laminar", "kOmegaSST"):
    print(f"  {g}:", q([x["mean_abs_pct"] for x in rows if x["turb"] == g]))
