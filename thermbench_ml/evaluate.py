"""Score predictors on a ThermBench split.

  python evaluate.py --split random --stride 10            # all machines' runs (data.DEFAULT_ROOTS)
  python evaluate.py --roots ~/of_runs/full_h5mm --split random
Scores every stride-th snapshot (excluding t = 0) of each test run and prints one row per
model. Results are merged into results/<split>.json (one entry per model, with per-run scores),
so neural results written by train.py are kept.
"""
import argparse
import json
import os
import time

import numpy as np

import baselines
import metrics
from data import DEFAULT_ROOTS, index, port_maps
from splits import SPLITS, split_runs

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ["rmse_K", "rmse_theta", "profile_rmse", "y_mid_err_m", "energy_err", "T_out_err_K"]


def evaluate(model, test, stride):
    """(aggregate, per_run) for one predictor on the test runs."""
    per_run = []
    for r in test:
        n = len(r.times()[0])
        idx = np.arange(stride, n, stride)
        true = r.field("T", idx=idx, theta=True)
        pred = model.predict(r, idx)
        outlet = port_maps(r.meta, r.meta["ny"], r.meta["nx"])[1]
        per_run.append(metrics.score(pred, true, r.Th - r.Tc, r.meta["mesh_h_m"], outlet)
                       | {"run_id": r.run_id})
    return metrics.aggregate(per_run), per_run


def save(split, sizes, n_runs, stride, name, res, per_run, extra=None, outdir="results"):
    """Merge one model's result into <outdir>/<split>.json (default results/)."""
    os.makedirs(os.path.join(HERE, outdir), exist_ok=True)
    out = os.path.join(HERE, outdir, f"{split}.json")
    allres = json.load(open(out)) if os.path.exists(out) else {"split": split, "results": {}}
    allres.update({"stride": stride, "n_runs": n_runs, "sizes": sizes,
                   "updated": time.strftime("%Y-%m-%d %H:%M")})
    allres["results"][name] = res | (extra or {}) | {"per_run": per_run}
    json.dump(allres, open(out, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", default=DEFAULT_ROOTS)
    ap.add_argument("--split", default="random", choices=SPLITS)
    ap.add_argument("--stride", type=int, default=10)
    ap.add_argument("--models", nargs="+", default=["initial", "ideal_stratified", "knn", "nn", "idw", "rbf"])
    ap.add_argument("--manifest", default=None, help="frozen run list (freeze_manifest.py)")
    ap.add_argument("--outdir", default="results", help="results folder (merged into <outdir>/<split>.json)")
    a = ap.parse_args()
    runs = index(a.roots, manifest=a.manifest)
    s = split_runs(runs, a.split)
    sizes = {k: len(v) for k, v in s.items()}
    print(f"{len(runs)} runs: {sizes}")
    if not s["test"]:
        print("no test runs yet for this split")
        return
    makers = {"initial": baselines.Initial, "ideal_stratified": baselines.IdealStratified,
              "knn": baselines.KNN, "nn": baselines.NN, "idw": baselines.IDW, "rbf": baselines.RBF}
    print(f"{'model':18s} " + " ".join(f"{c:>12s}" for c in COLS) + "     time")
    for name in a.models:
        t0 = time.time()
        model = makers[name]().fit(s["train"] + s["val"])
        res, per_run = evaluate(model, s["test"], a.stride)
        print(f"{name:18s} " + " ".join(f"{res[c]:12.4f}" for c in COLS) + f"  {time.time() - t0:6.1f} s")
        save(a.split, sizes, len(runs), a.stride, name, res, per_run, outdir=a.outdir)


if __name__ == "__main__":
    main()
