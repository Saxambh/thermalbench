"""Multi-node 1D baseline vs the other tank models: design-level paired intervals (8 November 2026).

Sources: results/<split>.json entry "multinode" (mn_eval.py, protocol committed in 60223ee before scoring) and
results_merged/<split>.json for the other models (neural: mean of 3 seeds per run, every 10th snapshot).
For each split, metric and comparison model: per-run difference (other model minus multinode; positive =
multinode better), averaged per design, design-level percentile bootstrap (10,000 resamples, seed 20261108),
marginal 95 % intervals. Descriptive, not a pre-registered test. Also stores the per-run multinode scores.
Writes compare.json and RESULT_tables.md.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
SPLITS = ("random", "ood_geom", "ood_mode", "ood_flow")
OTHERS = ("ideal_stratified", "rbf", "fno_hybrid_canon", "unet_hybrid_canon")
METRICS = (("rmse_theta", 100, "field, % dT"), ("profile_rmse", 100, "profile, % dT"), ("energy_err", 100, "energy, % of charge"),
           ("T_out_err_K", 1, "outlet T, K"), ("y_mid_err_m", 1000, "midpoint, mm"))
B, SEED = 10_000, 20261108


def per_run(res, model):
    names = [n for n in (model, f"{model}_s1", f"{model}_s2") if n in res]
    rows = [{p["run_id"]: p for p in res[n]["per_run"]} for n in names]
    common = set.intersection(*(set(r) for r in rows))
    return {rid: {k: float(np.nanmean([r[rid][k] for r in rows])) for k, _, _ in METRICS} for rid in common}


out, md = {}, ["# Multi-node 1D baseline vs the field surrogates (design-level, descriptive)", "",
               "Mean per model (runs weighted equally), and the paired difference other minus multinode averaged per design "
               "(positive: multinode better) with a marginal 95 % bootstrap interval over designs.", ""]
for split in SPLITS:
    mn = {p["run_id"]: p for p in json.load(open(os.path.join(ML, "results", f"{split}.json")))["results"]["multinode"]["per_run"]}
    merged = json.load(open(os.path.join(ML, "results_merged", f"{split}.json")))["results"]
    pr = {m: per_run(merged, m) for m in OTHERS}
    runs = sorted(set(mn).intersection(*(set(v) for v in pr.values())))
    designs = sorted({r.split("_")[0] for r in runs})
    out[split] = {"n_runs": len(runs), "n_designs": len(designs), "metrics": {}}
    md += [f"## {split} ({len(runs)} runs, {len(designs)} designs)", "",
           "| Metric | multinode | " + " | ".join(OTHERS) + " |", "|---|---|" + "---|" * len(OTHERS)]
    rng_seed = SEED
    for k, sc, lab in METRICS:
        mvals = np.array([mn[r][k] for r in runs])
        cells, o = [], {"multinode_mean": float(sc * np.nanmean(mvals))}
        for m in OTHERS:
            d_run = {r: pr[m][r][k] - mn[r][k] for r in runs if np.isfinite(pr[m][r][k]) and np.isfinite(mn[r][k])}
            g = {}
            for r, v in d_run.items():
                g.setdefault(r.split("_")[0], []).append(v)
            d = sc * np.array([np.mean(v) for v in g.values()])
            rng = np.random.default_rng(rng_seed)
            bt = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
            lo, hi = np.percentile(bt, [2.5, 97.5])
            mean_other = float(sc * np.nanmean([pr[m][r][k] for r in runs]))
            o[m] = {"mean": mean_other, "diff_mean": float(d.mean()), "ci95": [float(lo), float(hi)],
                    "share_designs_multinode_better": float((d > 0).mean()), "n_designs": len(d)}
            flag = "MN better" if lo > 0 else ("MN worse" if hi < 0 else "n.s.")
            cells.append(f"{mean_other:.2f} ({d.mean():+.2f} [{lo:+.2f}, {hi:+.2f}], {flag})")
        out[split]["metrics"][k] = o
        md.append(f"| {lab} | **{o['multinode_mean']:.2f}** | " + " | ".join(cells) + " |")
    md.append("")
out["multinode_per_run"] = {s: json.load(open(os.path.join(ML, "results", f"{s}.json")))["results"]["multinode"]["per_run"] for s in SPLITS}
out["multinode_fit"] = {s: json.load(open(os.path.join(ML, "results", f"{s}.json")))["results"]["multinode"].get("fit") for s in SPLITS}
json.dump(out, open(os.path.join(HERE, "compare.json"), "w"), indent=1)
open(os.path.join(HERE, "RESULT_tables.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))
print("\n".join(md).encode("ascii", "replace").decode())
