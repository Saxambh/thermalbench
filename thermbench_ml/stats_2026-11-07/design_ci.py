"""Design-level 95 % intervals for the tank benchmark (review items on statistics, 7 Nov 2026).

Source: results_merged/<split>.json, the stored final per-run scores (every 10th snapshot, t > 0).
Neural models: mean of the 3 seeds per run ("seed mean", the basis of dossier 8.4); this is NOT the
3-seed ensemble of dossier 8.1, which scores the averaged prediction on all 120 snapshots.
Unit: the design (run_id prefix); runs of a design are averaged first; designs weighted equally.
Intervals: ordinary percentile bootstrap over designs, 10,000 resamples, seed 20261107, marginal (not
adjusted for the number of comparisons). Descriptive: these comparisons were not pre-registered, except
where noted (the discharge subset analysis is reported separately).
Writes design_ci.json and design_ci.md.
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
SPLITS = ("random", "ood_geom", "ood_mode", "ood_flow")
NEURAL = [f"{a}{v}" for a in ("fno", "unet") for v in ("", "_canon", "_hybrid", "_hybrid_canon")]
BASE = ["ideal_stratified", "rbf"]
PAIRS = [("fno_hybrid_canon", "unet_hybrid_canon", "FNO minus U-Net (hybrid + canonical)")] + \
        [(f"{a}{x}", f"{a}{y}", f"{a.upper() if a == 'fno' else 'U-Net'}: {lab}") for a in ("fno", "unet")
         for x, y, lab in (("", "_canon", "plain minus canonical"), ("", "_hybrid", "plain minus hybrid"),
                           ("_hybrid", "_hybrid_canon", "hybrid minus hybrid + canonical"),
                           ("_canon", "_hybrid_canon", "canonical minus hybrid + canonical"))] + \
        [("ideal_stratified", "fno_hybrid_canon", "ideal stratification minus FNO hybrid + canonical"),
         ("rbf", "fno_hybrid_canon", "RBF interpolation minus FNO hybrid + canonical")]
B, SEED = 10_000, 20261107


def per_run(res, model):
    names = [n for n in (model, f"{model}_s1", f"{model}_s2") if n in res] if model in NEURAL else [model]
    vals = [{p["run_id"]: 100 * p["rmse_theta"] for p in res[n]["per_run"]} for n in names]
    common = set.intersection(*(set(v) for v in vals))
    return {r: float(np.mean([v[r] for v in vals])) for r in common}, len(names)


def by_design(d, runs):
    g = {}
    for r in runs:
        g.setdefault(r.split("_")[0], []).append(d[r])
    return np.array([np.mean(v) for v in g.values()])


def ci(x):
    rng = np.random.default_rng(SEED)
    b = x[rng.integers(0, len(x), (B, len(x)))].mean(1)
    return [float(v) for v in np.percentile(b, [2.5, 97.5])]


out, md = {}, ["# Design-level 95 % intervals, tank benchmark (descriptive)", "",
               "Seed means per run (dossier 8.4 basis, every 10th snapshot), averaged per design, designs equally "
               "weighted; percentile bootstrap over designs, 10,000 resamples, marginal intervals. Field error in % of ΔT.", ""]
for split in SPLITS:
    res = json.load(open(os.path.join(ML, "results_merged", f"{split}.json")))["results"]
    pr = {m: per_run(res, m) for m in NEURAL + BASE if m in res or f"{m}_s1" in res}
    runs = sorted(set.intersection(*(set(v[0]) for v in pr.values())))
    o = {"n_runs": len(runs), "n_designs": len({r.split('_')[0] for r in runs}), "models": {}, "pairs": []}
    md += [f"## {split} ({o['n_runs']} runs, {o['n_designs']} designs)", "",
           "| Model | Seeds | Mean, run-weighted | Mean, design-weighted [95 %] |", "|---|---|---|---|"]
    for m, (d, ns) in pr.items():
        x = by_design(d, runs)
        o["models"][m] = {"seeds": ns, "mean_run_weighted": float(np.mean([d[r] for r in runs])),
                          "mean_design_weighted": float(x.mean()), "ci95": ci(x)}
        v = o["models"][m]
        md.append(f"| {m} | {ns} | {v['mean_run_weighted']:.2f} | {v['mean_design_weighted']:.2f} [{v['ci95'][0]:.2f}, {v['ci95'][1]:.2f}] |")
    md += ["", "| Paired difference (positive: second is better) | Mean, pp [95 %] | Designs where second is better |", "|---|---|---|"]
    for a, b, lab in PAIRS:
        if a not in pr or b not in pr:
            continue
        diff = by_design({r: pr[a][0][r] - pr[b][0][r] for r in runs}, runs)
        c = ci(diff)
        o["pairs"].append({"label": lab, "a": a, "b": b, "mean_pp": float(diff.mean()), "ci95": c,
                           "share_b_better": float((diff > 0).mean()), "excludes_zero": bool(c[0] > 0 or c[1] < 0)})
        md.append(f"| {lab} | {diff.mean():+.2f} [{c[0]:+.2f}, {c[1]:+.2f}]{'' if (c[0] > 0 or c[1] < 0) else ' (includes 0)'} | {100 * (diff > 0).mean():.0f} % |")
    md.append("")
    out[split] = o
json.dump(out, open(os.path.join(HERE, "design_ci.json"), "w"), indent=1)
open(os.path.join(HERE, "design_ci.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md))
print("\n".join(md))
