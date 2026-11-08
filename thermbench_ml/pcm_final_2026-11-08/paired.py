"""PCM: paired 95 % intervals, neural models vs baselines (8 November 2026). Descriptive, not pre-registered.

Every PCM run is its own case (500 runs, 500 case IDs), so runs are the resampling unit.
Per split and neural model (per-run mean over its 3 seeds): difference baseline minus neural (positive =
neural better), percentile bootstrap over test runs (10,000 resamples, seed 20261108), for
  - IDW: a fixed reference, chosen because it is the most consistently strong baseline;
  - the split's best baseline by mean field RMSE, which is selected on the test set (flagged as such).
Metrics: field RMSE (K), energy error (%), t90 error (%) on runs where both models cross t90 in every seed.
Writes paired.json and PAIRED.md.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
SPLITS = ("random", "ood_fins", "ood_drive", "ood_tilt", "ood_material", "ood_material_r")
BASE = ["front", "knn", "nn", "idw", "rbf"]
NEURAL = ["fno", "unet", "fno_hybrid", "unet_hybrid"]
METRICS = (("rmse_K", 1, "field RMSE, K"), ("energy_err", 100, "energy error, pp"), ("t90_err", 100, "t90 error, pp"))
B, SEED = 10_000, 20261108


def per_run(res, m):
    names = [n for n in (m, m + "_s1", m + "_s2") if n in res]
    rows = [{p["run_id"]: p for p in res[n]["per_run"]} for n in names]
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


out, md = {}, ["# PCM: paired differences, neural vs baselines (descriptive)", "",
               "Baseline minus neural (positive: the neural model is better), mean over test runs with a 95 % percentile "
               "bootstrap interval over runs. Neural scores are the per-run mean of 3 seeds. 'Best baseline' is chosen on "
               "the test set by mean field RMSE. t90: runs where both models cross in every seed.", ""]
for split in SPLITS:
    res = json.load(open(os.path.join(ML, "results_pcm_merged", f"{split}.json")))["results"]
    pr = {m: per_run(res, m) for m in BASE + NEURAL}
    runs = sorted(pr["idw"])
    best = min(BASE, key=lambda b: np.mean([pr[b][r]["rmse_K"] for r in runs]))
    refs = ["idw"] + ([best] if best != "idw" else [])
    out[split] = {"best_baseline": best, "n_runs": len(runs), "rows": {}}
    md += [f"## {split} ({len(runs)} runs; best baseline: {best})", "", "| Neural | vs | " + " | ".join(l for _, _, l in METRICS) + " |",
           "|---|---|" + "---|" * len(METRICS)]
    for m in NEURAL:
        for ref in refs:
            cells, o = [], {}
            for k, sc, _ in METRICS:
                d = np.array([pr[ref][r][k] - pr[m][r][k] for r in runs if np.isfinite(pr[ref][r][k]) and np.isfinite(pr[m][r][k])]) * sc
                if len(d) < 5:
                    cells.append("n/a"); continue
                mu, (lo, hi) = ci(d)
                o[k] = {"diff": mu, "ci95": [lo, hi], "n": len(d)}
                tag = "neural better" if lo > 0 else ("baseline better" if hi < 0 else "no clear difference")
                cells.append(f"{mu:+.2f} [{lo:+.2f}, {hi:+.2f}], {tag}" + (f" (n {len(d)})" if k == "t90_err" else ""))
            out[split]["rows"][f"{m}_vs_{ref}"] = o
            md.append(f"| {m} | {ref} | " + " | ".join(cells) + " |")
    md.append("")
json.dump(out, open(os.path.join(HERE, "paired.json"), "w"), indent=1)
open(os.path.join(HERE, "PAIRED.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))
print("\n".join(md))
