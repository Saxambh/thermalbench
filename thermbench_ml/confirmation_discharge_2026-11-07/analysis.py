"""Discharge subset analysis, run once as pre-registered in PROPOSAL.md (revision 3, commit 0334509).

Inputs: confirmation_set.json (259 run ids) and the stored final per-run scores in
results_merged/ood_mode.json (rmse_theta, every 10th snapshot). No new predictions.
Writes analysis_result.json and prints the result.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
B = 10_000
SEED_CI, SEED_P = 20261107, 20261108
SEEDS = ("", "_s1", "_s2")
MODELS = {f"{a}_{v}": [f"{a}_{v}{s}" for s in SEEDS] for a in ("fno", "unet") for v in ("hybrid", "hybrid_canon")}
MODELS["ideal_stratified"] = ["ideal_stratified"]
TESTS = [("H1", "fno", "fno_hybrid", "fno_hybrid_canon"), ("H1", "unet", "unet_hybrid", "unet_hybrid_canon"),
         ("H2", "fno", "ideal_stratified", "fno_hybrid_canon"), ("H2", "unet", "ideal_stratified", "unet_hybrid_canon")]
FLAGGED = "T0211_sst"

conf = json.load(open(os.path.join(HERE, "confirmation_set.json")))
subset = conf["run_ids"]
res = json.load(open(os.path.join(ML, "results_merged", "ood_mode.json")))["results"]
per = {}  # model -> run_id -> field error in % of dT (seed mean)
for m, entries in MODELS.items():
    vals = []
    for e in entries:
        if e not in res:
            sys.exit(f"missing entry {e}")
        vals.append({p["run_id"]: 100 * p["rmse_theta"] for p in res[e]["per_run"]})
    common = set.intersection(*(set(v) for v in vals))
    per[m] = {r: float(np.mean([v[r] for v in vals])) for r in common}
all_test = sorted(set.intersection(*(set(v) for v in per.values())))
missing = [r for r in subset if r not in all_test]
if missing:
    sys.exit(f"subset runs without scores for every model: {missing[:5]}")


def design_diffs(runs, comp, model):
    """One paired difference per design: comparison minus hybrid_canon, runs of a design averaged first."""
    by = {}
    for r in runs:
        by.setdefault(r.split("_")[0], []).append(r)
    return np.array([np.mean([per[comp][r] for r in rs]) - np.mean([per[model][r] for r in rs]) for rs in by.values()])


def test(d):
    n = len(d)
    rng = np.random.default_rng(SEED_CI)
    boot = d[rng.integers(0, n, (B, n))].mean(1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    e = d - d.mean()
    rng = np.random.default_rng(SEED_P)
    null = e[rng.integers(0, n, (B, n))].mean(1)
    p = (1 + int((null >= d.mean()).sum())) / (B + 1)
    return {"n_designs": n, "mean_improvement_pp": float(d.mean()), "ci95_marginal": [float(lo), float(hi)],
            "share_designs_improved": float((d > 0).mean()), "p_one_sided": p}


def holm(ps):
    order = np.argsort(ps)
    adj, run = np.empty(len(ps)), 0.0
    for k, i in enumerate(order):
        run = max(run, (len(ps) - k) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def family(runs):
    out = []
    for h, arch, comp, model in TESTS:
        out.append({"hypothesis": h, "arch": arch, "comparison": f"{comp} minus {model}"} | test(design_diffs(runs, comp, model)))
    adj = holm(np.array([o["p_one_sided"] for o in out]))
    for o, a in zip(out, adj):
        o["p_holm"] = float(a)
        o["supported"] = bool(a < 0.05)
    return out


def describe(runs, test_meta):
    return {m: {"mean": float(np.mean([per[m][r] for r in runs])), "median": float(np.median([per[m][r] for r in runs]))}
            for m in MODELS} | {"n_runs": len(runs), "n_designs": len({r.split('_')[0] for r in runs}),
                                "sst_share": float(np.mean([test_meta[r]["turb"] == "kOmegaSST" for r in runs])),
                                "Ri_below_5_share": float(np.mean([test_meta[r]["Ri"] < 5 for r in runs]))}


sys.path.insert(0, ML)
from data import index, DEFAULT_ROOTS
from splits import split_runs
test_runs = split_runs(index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_full_h5mm.json")), "ood_mode")["test"]
meta = {r.run_id: {"turb": r.meta["turbulence"], "Ri": r.meta["Ri_H"]} for r in test_runs}
rest = sorted(set(meta) - set(subset))

# sensitivity: remove the flagged run first, then recompute its design mean from a remaining sibling (if any)
sens_runs = [r for r in subset if r != FLAGGED]
result = {"protocol": "PROPOSAL.md revision 3, commit 0334509", "source": "results_merged/ood_mode.json",
          "B": B, "seed_ci": SEED_CI, "seed_p": SEED_P,
          "primary": family(subset), "sensitivity_without_T0211_sst": family(sens_runs),
          "descriptive": {"subset": describe(subset, meta), "remaining_ood_mode_test": describe(rest, meta)}}
json.dump(result, open(os.path.join(HERE, "analysis_result.json"), "w"), indent=1)

for name in ("primary", "sensitivity_without_T0211_sst"):
    print(f"\n{name}")
    for o in result[name]:
        print(f"  {o['hypothesis']} {o['arch']:4s} {o['comparison']:40s} n {o['n_designs']}  improvement {o['mean_improvement_pp']:+.2f} pp "
              f"[{o['ci95_marginal'][0]:+.2f}, {o['ci95_marginal'][1]:+.2f}]  improved in {100*o['share_designs_improved']:.0f} % of designs  "
              f"p {o['p_one_sided']:.4f}  Holm {o['p_holm']:.4f}  {'SUPPORTED' if o['supported'] else 'not supported'}")
print("\ndescriptive (field error, % of dT: mean / median)")
for g, d in result["descriptive"].items():
    print(f"  {g}: {d['n_runs']} runs, {d['n_designs']} designs, SST {100*d['sst_share']:.0f} %, Ri<5 {100*d['Ri_below_5_share']:.0f} %")
    for m in MODELS:
        print(f"     {m:20s} {d[m]['mean']:6.2f} / {d[m]['median']:6.2f}")
