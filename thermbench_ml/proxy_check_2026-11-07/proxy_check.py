"""How well do the benchmark's proxy metrics track the CFD's real-property quantities? (review item, 7 Nov 2026)

On every run of the frozen tank manifest (CFD labels only, no model), per snapshot:
  energy   proxy: mean theta (constant rho*cp), the benchmark's energy_err basis
           real:  E_J / (e_h W H), the CFD's real-property stored energy as a fraction of a full charge
           (export_case.py: rho(T) and the integral of cp(T), relative to Tc)
           plus, per run, the range of the local weight rho(T) cp(T) over [Tc, Th] relative to its mean:
           a model's real-property energy error equals its proxy error weighted by this, so the range
           bounds how much the two errors can differ
  outlet   proxy: theta of the cells next to the outlet (data.port_maps), the basis of T_out_err_K
           real:  metrics/T_out_K, the area-averaged outlet-face temperature at the snapshot time
           also inside the breakthrough window (real outlet has completed 10 to 90 % of its change)
  y_mid    proxy (metrics.y_mid on theta) against metrics/y_mid_m (same definition), and how often the
           label has no 0.5 crossing (such snapshots are left out of y_mid_err_m)
Writes proxy_check.json and prints a summary.
"""
import json, os, sys
import numpy as np
import h5py

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
sys.path.insert(0, ML)
import metrics as M
from data import index, port_maps, DEFAULT_ROOTS

RHO_C = (2.1695153532e+02, 6.9673175536e+00, -1.9562261905e-02, 1.6666666667e-05)   # make_tank_case.py
CP_C = (8.7910736814e+03, -4.0168891060e+01, 1.1524691558e-01, -1.0858585859e-04)
poly = lambda cs, T: sum(c * T ** n for n, c in enumerate(cs))
h_int = lambda T: sum(c * T ** (n + 1) / (n + 1) for n, c in enumerate(CP_C))

runs = index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_full_h5mm.json"))
rows = []
for k, r in enumerate(runs):
    m = r.meta
    Th, Tc = r.Th, r.Tc
    dT = Th - Tc
    with h5py.File(os.path.join(r.path, "thermbench.h5")) as f:
        T = f["fields/T"][:].astype(np.float64)
        E = f["metrics/E_J"][:]
        Tout = f["metrics/T_out_K"][:]
        ymid = f["metrics/y_mid_m"][:]
        real = json.loads(f.attrs["case_json"]).get("props") == "real"
    th = (T - Tc) / dT
    W, H, h = m["W_m"], m["H_m"], m["mesh_h_m"]
    e_h = poly(RHO_C, Th) * (h_int(Th) - h_int(Tc)) if real else 992.0 * 4180.0 * dT
    e_real = E / (e_h * W * H)
    e_proxy = th.mean(axis=(1, 2))
    Tg = np.linspace(Tc, Th, 201)
    w = poly(RHO_C, Tg) * poly(CP_C, Tg) if real else np.ones_like(Tg)
    outlet = port_maps(m, m["ny"], m["nx"])[1]
    o_proxy = Tc + dT * (th * (outlet / outlet.sum())).sum(axis=(1, 2))
    s = slice(1, None)   # t > 0 (the benchmark never scores t = 0)
    d_out = (o_proxy - Tout)[s]
    c = np.abs(Tout - Tout[0]) / max(abs(Tout[-1] - Tout[0]), 1e-9)
    ev = ((c >= 0.1) & (c <= 0.9))[s] if abs(Tout[-1] - Tout[0]) > 0.02 * dT else np.zeros(len(d_out), bool)
    ym = M.y_mid(th, h)
    rows.append({"run_id": r.run_id, "turb": m["turbulence"], "mode": m["mode"], "Ri": m["Ri_H"], "dT": dT,
                 "energy_abs_diff": float(np.abs(e_proxy - e_real)[s].mean()),
                 "energy_abs_diff_max": float(np.abs(e_proxy - e_real)[s].max()),
                 "rhocp_weight_range": [float(w.min() / w.mean()), float(w.max() / w.mean())],
                 "outlet_abs_K": float(np.abs(d_out).mean()), "outlet_abs_pct": float(100 * np.abs(d_out).mean() / dT),
                 "outlet_event_abs_pct": float(100 * np.abs(d_out[ev]).mean() / dT) if ev.any() else None,
                 "n_event": int(ev.sum()),
                 "ymid_max_diff_m": float(np.nanmax(np.abs(ym - ymid)[s])) if np.isfinite(ym[s]).any() else None,
                 "ymid_label_missing": float((~np.isfinite(ym[s])).mean())})
    if k % 100 == 0:
        print(k, r.run_id, flush=True)

json.dump(rows, open(os.path.join(HERE, "proxy_check.json"), "w"), indent=1)
q = lambda a: f"median {np.median(a):.3g}, 90 % {np.percentile(a, 90):.3g}, max {np.max(a):.3g}"
print(len(rows), "runs")
print("energy |proxy - real| (fraction of full charge), run means:", q([x["energy_abs_diff"] for x in rows]))
print("rho*cp weight min / max over [Tc, Th], relative to mean:",
      f"{min(x['rhocp_weight_range'][0] for x in rows):.4f} / {max(x['rhocp_weight_range'][1] for x in rows):.4f}")
print("outlet |proxy - real| % of dT, run means:", q([x["outlet_abs_pct"] for x in rows]))
print("outlet in breakthrough window, % of dT:", q([x["outlet_event_abs_pct"] for x in rows if x["outlet_event_abs_pct"] is not None]))
print("y_mid max |proxy - h5| (m):", q([x["ymid_max_diff_m"] for x in rows if x["ymid_max_diff_m"] is not None]))
print("y_mid label missing (share of snapshots):", q([x["ymid_label_missing"] for x in rows]),
      f"; runs with any missing {sum(x['ymid_label_missing'] > 0 for x in rows)}")
