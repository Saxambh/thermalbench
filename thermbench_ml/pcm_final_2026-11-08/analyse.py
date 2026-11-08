"""PCM benchmark, final evaluation of the 72 neural jobs plus the baselines (8 November 2026).

Inputs: results_pcm_merged/<split>.json (results_all.sh pcm), manifest_pcm.json (md5 19397b78...),
pcm_inventory_2026-11-07.csv (solver QC per case).
1. Reconciliation: every entry's per-run test IDs must equal the frozen split's test IDs (pcm_splits.split_runs
   on the frozen manifest); every expected neural job (4 models x 3 seeds x 6 splits) must be present.
2. Table per split and model (neural: mean over 3 seeds of the per-run scores): field RMSE (K), liquid IoU,
   energy error, melt-time crossing (runs whose predicted liquid fraction reaches 0.9 within the input-only
   horizon tau <= 3 t_ref, out of the test runs; seed-mean), t90 error conditional on crossing.
3. WARN sensitivity (review item 3.6): the same means without the 39 retained solver-WARN cases.
Writes result.json and RESULT_tables.md. Descriptive; no tests.
"""
import csv, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
ROOT = os.path.dirname(ML)
sys.path.insert(0, ML)
from pcm_data import DEFAULT_ROOTS, index
from pcm_splits import SPLITS, split_runs

BASE = ["initial", "stefan", "front", "knn", "nn", "idw", "rbf"]
NEURAL = ["fno", "unet", "fno_hybrid", "unet_hybrid"]
KEYS = ["rmse_K", "alpha_rmse", "liquid_iou", "melt_frac_err", "energy_err", "t90_reached", "t90_err"]

runs = index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_pcm.json"))
inv = {r["case_id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "pcm_inventory_2026-11-07.csv")))}
warn = {c for c, r in inv.items() if r["solver_qc"] == "WARN"}
assert len(runs) == 500 and len(warn) == 39, (len(runs), len(warn))

out, problems, md = {"n_runs": len(runs), "warn_cases": sorted(warn), "splits": {}}, [], []
for split in SPLITS:
    s = split_runs(runs, split)
    test = sorted(r.run_id for r in s["test"])
    R = json.load(open(os.path.join(ML, "results_pcm_merged", f"{split}.json")))
    res = R["results"]
    if R["sizes"] != {k: len(v) for k, v in s.items()}:
        problems.append(f"{split}: stored sizes {R['sizes']} differ from the frozen split")
    for name, e in res.items():
        ids = sorted(p["run_id"] for p in e["per_run"])
        if ids != test:
            problems.append(f"{split}/{name}: {len(ids)} test IDs, {len(set(ids) ^ set(test))} differ from the frozen split")
    for m in NEURAL:
        for sd in ("", "_s1", "_s2"):
            if m + sd not in res:
                problems.append(f"{split}: {m + sd} missing")
    nw = [r for r in test if r in warn]
    rows = {}
    for m in BASE + NEURAL:
        names = [m] if m in BASE else [m + sd for sd in ("", "_s1", "_s2") if m + sd in res]
        per = [{p["run_id"]: p for p in res[n]["per_run"]} for n in names if n in res]
        if not per:
            continue
        def agg(ids):
            o = {}
            for k in KEYS:
                if k == "t90_err":   # conditional on crossing, per seed, then mean over seeds
                    v = [np.nanmean([d[i][k] for i in ids if d[i]["t90_reached"] > 0.5]) if any(d[i]["t90_reached"] > 0.5 for i in ids) else np.nan for d in per]
                else:
                    v = [np.nanmean([d[i][k] for i in ids]) for d in per]
                o[k] = float(np.nanmean(v)) if np.any(np.isfinite(v)) else float("nan")
            o["seed_sd_rmse_K"] = float(np.std([np.nanmean([d[i]["rmse_K"] for i in ids]) for d in per], ddof=1)) if len(per) > 1 else None
            o["n_crossed"] = float(np.mean([sum(d[i]["t90_reached"] > 0.5 for i in ids) for d in per]))
            o["n"] = len(ids)
            return o
        allr, nowarn = agg(test), agg([i for i in test if i not in warn])
        rows[m] = {"n_seeds": len(per), "all": allr, "without_warn": nowarn,
                   "warn_delta": {k: nowarn[k] - allr[k] for k in KEYS}}
    out["splits"][split] = {"sizes": R["sizes"], "n_test": len(test), "n_warn_in_test": len(nw), "models": rows}
    md += [f"## {split}: {len(test)} test runs ({len(nw)} solver-WARN)", "",
           "| Model | seeds | Field RMSE, K | Liquid IoU | Energy err | Crossed t90 (of n) | t90 err, crossed | RMSE without WARN |",
           "|---|---|---|---|---|---|---|---|"]
    for m, r in rows.items():
        a, w = r["all"], r["without_warn"]
        sd = f" ± {a['seed_sd_rmse_K']:.2f}" if a["seed_sd_rmse_K"] is not None else ""
        md.append(f"| {m} | {r['n_seeds']} | {a['rmse_K']:.2f}{sd} | {a['liquid_iou']:.3f} | {100 * a['energy_err']:.1f} % | "
                  f"{a['n_crossed']:.1f} / {a['n']} | {100 * a['t90_err']:.1f} % | {w['rmse_K']:.2f} ({w['rmse_K'] - a['rmse_K']:+.2f}) |")
    md.append("")
out["problems"] = problems
head = ["# PCM benchmark: final evaluation (8 November 2026)", "",
        f"Reconciliation: {'all entries match the frozen test splits and all 72 neural jobs are present' if not problems else str(len(problems)) + ' problems, listed in result.json'}.", "",
        "Neural rows: mean of the 3 seeds (± seed SD of the field RMSE). t90 error is relative, conditional on the "
        "prediction crossing a liquid fraction of 0.9 within tau <= 3 t_ref. Last column: field RMSE without the "
        "39 retained solver-WARN cases (change in brackets).", ""]
json.dump(out, open(os.path.join(HERE, "result.json"), "w"), indent=1)
open(os.path.join(HERE, "RESULT_tables.md"), "w", encoding="utf-8", newline="\n").write("\n".join(head + md))
print("\n".join(head + md))
print("PROBLEMS:", problems)
