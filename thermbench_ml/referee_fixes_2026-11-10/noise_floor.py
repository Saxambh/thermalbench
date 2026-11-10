"""Referee fix 1 (PLAN.md): the label noise floor from the 24 perturbation pairs.

Each pair: the dataset run against the same design rerun with the inlet velocity x (1 + 1e-4) (tank_verify.sh "rep"),
compared with scripts/cmp_tank.py exactly as in the 6 November mesh check (field RMS % of dT on the coarser grid at the
reference snapshot times, stored energy, outlet, midpoint, by window). Reference = dataset run.
The floor is set next to the per-run field error of the two hybrid-canonical networks (seed mean) on every split where
the run is a test run (results_merged), so the comparison is run by run.
Writes noise_floor.json and noise_floor.md.   python noise_floor.py <dir with the *_rep runs>
"""
import json, os, subprocess, sys
import numpy as np
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
R = os.path.dirname(ML)
sys.path.insert(0, ML)
from data import DEFAULT_ROOTS, index

D = os.path.expanduser(sys.argv[1])
sel = json.load(open(os.path.join(HERE, "selection_tank.json")))["pairs"]
runs = {r.run_id: r for r in index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_full_h5mm.json"))}
args = [f"{p['run_id']}:{os.path.join(D, p['run_id'] + '_rep', 'thermbench.h5')}:{os.path.join(runs[p['run_id']].path, 'thermbench.h5')}" for p in sel]
out_cmp = os.path.join(HERE, "noise_floor_cmp.json")
subprocess.run([sys.executable, os.path.join(R, "scripts", "cmp_tank.py"), os.path.join(R, "design_v2_full.csv"), out_cmp] + args, check=True)
cmp = {c["pair"].split("|")[0] if "|" in c["pair"] else c["pair"]: c for c in json.load(open(out_cmp))}

model_err = {}
for split in ("random", "ood_flow", "ood_geom", "ood_mode"):
    res = json.load(open(os.path.join(ML, "results_merged", f"{split}.json")))["results"]
    for m in ("fno_hybrid_canon", "unet_hybrid_canon"):
        rows = [{q["run_id"]: q["rmse_theta"] for q in res[n]["per_run"]} for n in (m, m + "_s1", m + "_s2")]
        for rid in rows[0]:
            model_err.setdefault(rid, {}).setdefault(m, []).append(100 * float(np.mean([r[rid] for r in rows])))
rows = []
for p in sel:
    c = cmp[p["run_id"]]
    me = model_err.get(p["run_id"], {})
    rows.append({"run_id": p["run_id"], "Ri": p["Ri"], "Re": p["Re"], "turb": p["turb"],
                 "floor_field_pct": c.get("field_rms_pct"), "floor_mean_field_pct": c.get("mean_field_pct"),
                 "floor_E_pct": c.get("E_pct"), "floor_Tout_pct": c.get("Tout_rms_pct"), "floor_ymid_mm": c.get("ymid_mm"),
                 "fno_hc_pct": float(np.mean(me["fno_hybrid_canon"])) if me else None,
                 "unet_hc_pct": float(np.mean(me["unet_hybrid_canon"])) if me else None})
f = np.array([r["floor_field_pct"] for r in rows], float)
ri = np.array([r["Ri"] for r in rows])
summ = {"n": len(rows), "floor_field_pct_median": float(np.median(f)), "floor_field_pct_max": float(f.max()),
        "rho_floor_logRi": float(spearmanr(f, np.log(ri))[0]),
        "by_closure": {t: {"median": float(np.median(f[[r["turb"] == t for r in rows]])), "max": float(f[[r["turb"] == t for r in rows]].max())}
                       for t in ("laminar", "kOmegaSST")}}
mod = np.array([np.nanmean([r["fno_hc_pct"], r["unet_hc_pct"]]) for r in rows], float)
summ["model_over_floor_median"] = float(np.median(mod / np.maximum(f, 1e-6)))
summ["share_runs_model_error_below_2x_floor"] = float(np.mean(mod < 2 * f))
json.dump({"summary": summ, "rows": rows}, open(os.path.join(HERE, "noise_floor.json"), "w"), indent=1)
md = ["# Label noise floor (inlet velocity x 1.0001) vs network error, 24 test-side tank runs", "",
      "| run | Ri | closure | floor field % dT | floor energy % | floor outlet % dT | FNO hc % dT | U-Net hc % dT |", "|---|---|---|---|---|---|---|---|"]
for r in sorted(rows, key=lambda r: r["Ri"]):
    g = lambda k, fmt="{:.2f}": "" if r[k] is None else fmt.format(r[k])
    md.append(f"| {r['run_id']} | {r['Ri']:.1f} | {r['turb']} | {g('floor_field_pct')} | {g('floor_E_pct')} | {g('floor_Tout_pct')} | {g('fno_hc_pct')} | {g('unet_hc_pct')} |")
md += ["", json.dumps(summ, indent=1)]
open(os.path.join(HERE, "noise_floor.md"), "w").write("\n".join(md))
print("\n".join(md))
