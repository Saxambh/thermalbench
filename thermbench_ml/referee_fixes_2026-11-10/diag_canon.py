"""Referee fix 3b (PLAN.md): why does the canonical frame alone not reach charge-level error on discharge?

For ood_mode (train: charge only; test: discharge), with the canonical encoder exactly as train.Encoder(canon=True):
1. per input parameter, the share of test runs whose value (after the frame change) lies outside the training range,
   and how far (in training standard deviations);
2. the standardised nearest-neighbour distance of each test run to the training runs, against the same distance of
   validation runs (charge, same encoder) as the in-distribution reference;
3. the inputs the frame change does not map: y_init (pre-stratified interface height, a parameter that is not
   mirrored with the field), and the property-dependent groups log_Re and log_Ri (cold inlet water is more viscous);
4. Spearman correlation of the per-run error of fno_canon / unet_canon (seed means, results_merged/ood_mode.json)
   with the NN distance, with pre-stratification, and with the number of out-of-range parameters; and the mean
   error of pre-stratified vs uniform-start runs.
Writes diag_canon.json and prints a summary. Reads parameters and stored scores only (no fields).
"""
import json, os, sys
import numpy as np
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
sys.path.insert(0, ML)
from data import DEFAULT_ROOTS, PARAMS, index
from splits import split_runs

runs = index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_full_h5mm.json"))
s = split_runs(runs, "ood_mode")
names = list(PARAMS)
I_D = names.index("discharge")


def p(r):
    v = r.params()
    if r.meta["mode"] == "discharge":
        v[I_D] = 0.0
    return v


Ptr = np.array([p(r) for r in s["train"]])
mu, sd = Ptr.mean(0), np.where(Ptr.std(0) < 1e-6, 1.0, Ptr.std(0))
Ztr = (Ptr - mu) / sd
lo, hi = Ztr.min(0), Ztr.max(0)


def describe(rs):
    Z = (np.array([p(r) for r in rs]) - mu) / sd
    out = (Z < lo - 1e-9) | (Z > hi + 1e-9)
    dist = np.where(Z < lo, lo - Z, np.where(Z > hi, Z - hi, 0.0))
    nn = np.array([np.sqrt(((Ztr - z) ** 2).sum(1)).min() for z in Z])
    return Z, out, dist, nn


Zte, out_te, dist_te, nn_te = describe(s["test"])
_, out_va, _, nn_va = describe(s["val"])
res = {"n_train": len(s["train"]), "n_test": len(s["test"]), "n_val": len(s["val"]), "params": {}}
for k, n in enumerate(names):
    res["params"][n] = {"share_test_out_of_range": float(out_te[:, k].mean()), "share_val_out_of_range": float(out_va[:, k].mean()),
                        "max_sd_outside": float(dist_te[:, k].max())}
res["nn_distance"] = {"test_median": float(np.median(nn_te)), "test_p90": float(np.percentile(nn_te, 90)),
                      "val_median": float(np.median(nn_va)), "val_p90": float(np.percentile(nn_va, 90))}
# property-dependent groups at equal design inputs: Re and Ri of test runs vs a charge run with the same u, dT, slot
res["prestrat_share_test"] = float(np.mean([r.meta["init"] != "uniform" for r in s["test"]]))
res["prestrat_share_train"] = float(np.mean([r.meta["init"] != "uniform" for r in s["train"]]))
merged = json.load(open(os.path.join(ML, "results_merged", "ood_mode.json")))["results"]
corr = {}
for m in ("fno_canon", "unet_canon", "fno_hybrid_canon", "unet_hybrid_canon"):
    rows = [{q["run_id"]: q["rmse_theta"] for q in merged[n]["per_run"]} for n in (m, m + "_s1", m + "_s2") if n in merged]
    err = np.array([np.mean([row[r.run_id] for row in rows]) for r in s["test"]])
    pre = np.array([r.meta["init"] != "uniform" for r in s["test"]])
    corr[m] = {"mean_error_pct": float(100 * err.mean()),
               "rho_nn_distance": float(spearmanr(err, nn_te)[0]),
               "rho_n_out_of_range": float(spearmanr(err, out_te.sum(1))[0]),
               "mean_error_prestrat_pct": float(100 * err[pre].mean()), "mean_error_uniform_pct": float(100 * err[~pre].mean()),
               "rho_log_Ri": float(spearmanr(err, Zte[:, names.index("log_Ri")])[0])}
res["error_vs_inputs"] = corr
json.dump(res, open(os.path.join(HERE, "diag_canon.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "params"}, indent=1))
for n, v in res["params"].items():
    if v["share_test_out_of_range"] > 0:
        print(f"{n:12s} test outside training range: {100 * v['share_test_out_of_range']:5.1f} % (val {100 * v['share_val_out_of_range']:.1f} %), "
              f"up to {v['max_sd_outside']:.2f} sd")
