"""PCM: the 4x4-patch Transolver baseline (36 jobs) against FNO, U-Net and IDW (8 November 2026).

Analysis fixed in PLAN.md before launch (9294bcd):
1. Reconciliation: every Transolver entry's per-run test IDs equal the frozen split's test IDs
   (pcm_splits.split_runs on the frozen manifest), stored sizes equal the frozen sizes, all 36 jobs present.
2. Tables: the existing per-split PCM table rows (pcm_final_2026-11-08/analyse.py, same aggregation) with the
   Transolver rows added; per-seed field RMSE listed for every neural model (as asked in review).
3. Paired intervals, descriptive: other minus Transolver per test run (positive: Transolver better), neural
   scores the per-run mean of 3 seeds, 95 % percentile bootstrap over runs (10,000, seed 20261108), against
   FNO and U-Net in the same variant (plain vs plain, hybrid vs hybrid) and against IDW.
Inputs: results_pcm_merged/ (the 72 FNO/U-Net jobs and baselines) and results_pcm_ts_merged/ (Transolver).
Writes result_ts.json and RESULT_ts_tables.md.
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
NEURAL = ["fno", "unet", "transolver", "fno_hybrid", "unet_hybrid", "transolver_hybrid"]
KEYS = ["rmse_K", "alpha_rmse", "liquid_iou", "melt_frac_err", "energy_err", "t90_reached", "t90_err"]
SEEDS = ("", "_s1", "_s2")
B, SEED = 10_000, 20261108

runs = index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_pcm.json"))
inv = {r["case_id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "pcm_inventory_2026-11-07.csv")))}
warn = {c for c, r in inv.items() if r["solver_qc"] == "WARN"}
assert len(runs) == 500 and len(warn) == 39, (len(runs), len(warn))


def per_run(res, m):
    rows = [{p["run_id"]: p for p in res[m + sd]["per_run"]} for sd in SEEDS if m + sd in res]
    out = {}
    for rid in rows[0]:
        o = {k: float(np.mean([r[rid][k] for r in rows])) for k in ("rmse_K", "energy_err")}
        o["t90_err"] = float(np.mean([r[rid]["t90_err"] for r in rows])) if all(r[rid]["t90_reached"] > 0.5 for r in rows) else np.nan
        out[rid] = o
    return out


def ci(d):
    rng = np.random.default_rng(SEED)
    bt = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return float(d.mean()), [float(x) for x in np.percentile(bt, [2.5, 97.5])]


out, problems, md, pmd = {"splits": {}}, [], [], []
for split in SPLITS:
    s = split_runs(runs, split)
    test = sorted(r.run_id for r in s["test"])
    sizes = {k: len(v) for k, v in s.items()}
    R = json.load(open(os.path.join(ML, "results_pcm_merged", f"{split}.json")))
    T = json.load(open(os.path.join(ML, "results_pcm_ts_merged", f"{split}.json")))
    if T["sizes"] != sizes:
        problems.append(f"{split}: Transolver stored sizes {T['sizes']} differ from the frozen split {sizes}")
    for name, e in T["results"].items():
        ids = sorted(p["run_id"] for p in e["per_run"])
        if ids != test:
            problems.append(f"{split}/{name}: {len(ids)} test IDs, {len(set(ids) ^ set(test))} differ from the frozen split")
    for m in ("transolver", "transolver_hybrid"):
        for sd in SEEDS:
            if m + sd not in T["results"]:
                problems.append(f"{split}: {m + sd} missing")
    res = dict(R["results"]) | {k: v for k, v in T["results"].items() if k.startswith("transolver")}
    rows = {}
    for m in BASE + NEURAL:
        names = [m] if m in BASE else [m + sd for sd in SEEDS if m + sd in res]
        per = [{p["run_id"]: p for p in res[n]["per_run"]} for n in names]

        def agg(ids):
            o = {}
            for k in KEYS:
                if k == "t90_err":
                    v = [np.nanmean([d[i][k] for i in ids if d[i]["t90_reached"] > 0.5]) if any(d[i]["t90_reached"] > 0.5 for i in ids) else np.nan for d in per]
                else:
                    v = [np.nanmean([d[i][k] for i in ids]) for d in per]
                o[k] = float(np.nanmean(v)) if np.any(np.isfinite(v)) else float("nan")
            o["seed_rmse_K"] = [float(np.nanmean([d[i]["rmse_K"] for i in ids])) for d in per]
            o["seed_sd_rmse_K"] = float(np.std(o["seed_rmse_K"], ddof=1)) if len(per) > 1 else None
            o["n_crossed"] = float(np.mean([sum(d[i]["t90_reached"] > 0.5 for i in ids) for d in per]))
            o["n"] = len(ids)
            return o
        rows[m] = {"n_seeds": len(per), "all": agg(test), "without_warn": agg([i for i in test if i not in warn])}
    nw = sum(r in warn for r in test)
    md += [f"## {split}: {len(test)} test runs ({nw} solver-WARN)", "",
           "| Model | Field RMSE, K (seed mean ± SD) | per seed | Liquid IoU | Energy err | Crossed t90 (of n) | t90 err, crossed | RMSE without WARN |",
           "|---|---|---|---|---|---|---|---|"]
    for m, r in rows.items():
        a, w = r["all"], r["without_warn"]
        sd = f" ± {a['seed_sd_rmse_K']:.2f}" if a["seed_sd_rmse_K"] is not None else ""
        seeds = " / ".join(f"{x:.2f}" for x in a["seed_rmse_K"]) if r["n_seeds"] > 1 else ""
        name = f"**{m}**" if m.startswith("transolver") else m
        md.append(f"| {name} | {a['rmse_K']:.2f}{sd} | {seeds} | {a['liquid_iou']:.3f} | {100 * a['energy_err']:.1f} % | "
                  f"{a['n_crossed']:.1f} / {a['n']} | {100 * a['t90_err']:.1f} % | {w['rmse_K']:.2f} ({w['rmse_K'] - a['rmse_K']:+.2f}) |")
    md.append("")

    # paired
    pr = {m: per_run(res, m) for m in ["idw"] + NEURAL}
    prs = {}
    pmd += [f"## {split} ({len(test)} runs)", "", "| Transolver | vs | field RMSE, K | energy error, pp | t90 error, pp |", "|---|---|---|---|---|"]
    for ts, refs in (("transolver", ["fno", "unet", "idw"]), ("transolver_hybrid", ["fno_hybrid", "unet_hybrid", "idw"])):
        for ref in refs:
            cells, o = [], {}
            for k, sc in (("rmse_K", 1), ("energy_err", 100), ("t90_err", 100)):
                d = np.array([pr[ref][r][k] - pr[ts][r][k] for r in test if np.isfinite(pr[ref][r][k]) and np.isfinite(pr[ts][r][k])]) * sc
                if len(d) < 5:
                    cells.append("n/a"); continue
                mu, (lo, hi) = ci(d)
                o[k] = {"diff": mu, "ci95": [lo, hi], "n": len(d)}
                tag = "Transolver better" if lo > 0 else ("Transolver worse" if hi < 0 else "no clear difference")
                cells.append(f"{mu:+.2f} [{lo:+.2f}, {hi:+.2f}], {tag}" + (f" (n {len(d)})" if k == "t90_err" else ""))
            prs[f"{ts}_vs_{ref}"] = o
            pmd.append(f"| {ts} | {ref} | " + " | ".join(cells) + " |")
    pmd.append("")
    out["splits"][split] = {"sizes": sizes, "n_test": len(test), "models": rows, "paired": prs,
                            "transolver_sources": sorted(set(v for k, v in T["sources"].items()))}

out["problems"] = problems
head = ["# PCM with the 4x4-patch Transolver baseline: tables (8 November 2026)", "",
        f"Reconciliation: {'all 36 Transolver entries match the frozen test splits and sizes' if not problems else str(len(problems)) + ' problems, listed in result_ts.json'}.", "",
        "Neural rows: mean of the 3 seeds (± seed SD of the field RMSE), then the three seeds' field RMSE. t90 error is "
        "relative, conditional on the prediction crossing a liquid fraction of 0.9 within tau <= 3 t_ref. Last column: "
        "field RMSE without the 39 retained solver-WARN cases (change in brackets). FNO, U-Net and baseline rows are "
        "the same numbers as pcm_final_2026-11-08.", ""]
phead = ["# Paired differences: other model minus Transolver (descriptive)", "",
         "Positive: Transolver better. Mean over test runs with a 95 % percentile bootstrap interval over runs "
         "(10,000, seed 20261108). Neural scores are the per-run mean of 3 seeds. Plain Transolver is compared with plain "
         "FNO and U-Net, hybrid with hybrid. t90: runs where both models cross in every seed (n given).", ""]
json.dump(out, open(os.path.join(HERE, "result_ts.json"), "w"), indent=1)
open(os.path.join(HERE, "RESULT_ts_tables.md"), "w", encoding="utf-8", newline="\n").write("\n".join(head + md + [""] + phead + pmd))
print("\n".join(head + md + [""] + phead + pmd))
print("PROBLEMS:", problems)
