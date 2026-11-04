"""Score predictors on a ThermBench PCM split.

  python pcm_evaluate.py --split random                       # roots: pcm_data.DEFAULT_ROOTS
  python pcm_evaluate.py --roots ~/of_runs/pcm_mini/runs --split ood_fins
Scores every stride-th snapshot (t > 0) of each test run and prints one row per model.
Results are merged into results_pcm/<split>.json (one entry per model, with per-run scores),
so neural results written by pcm_train.py are kept.
"""
import argparse
import json
import os
import time

import numpy as np

import pcm_baselines
import pcm_metrics
from pcm_data import DEFAULT_ROOTS, index
from pcm_splits import SPLITS, split_runs

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ["rmse_K", "alpha_rmse", "liquid_iou", "melt_frac_err", "energy_err", "t90_err"]


def evaluate(model, test, stride):
    """(aggregate, per_run) for one predictor on the test runs."""
    per_run = []
    for r in test:
        t = r.times()[0]
        idx = np.arange(stride, len(t), stride)
        p_th, p_a = model.predict(r, idx)
        m = r.meta
        S = m["props"]["cp"] * (m["T_wall_K"] - m["T_init_K"]) / m["props"]["L"]
        per_run.append(pcm_metrics.score(p_th, p_a, r.field("T", idx=idx, theta=True), r.field("alpha", idx=idx),
                                         r.mask(), r.Tw - r.T0, S, t[idx]) | {"run_id": r.run_id})
    return pcm_metrics.aggregate(per_run), per_run


def save(split, sizes, n_runs, stride, name, res, per_run, extra=None, outdir="results_pcm"):
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
    ap.add_argument("--stride", type=int, default=5)
    ap.add_argument("--models", nargs="+", default=list(pcm_baselines.MAKERS))
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--outdir", default="results_pcm")
    a = ap.parse_args()
    runs = index(a.roots, manifest=a.manifest)
    s = split_runs(runs, a.split)
    sizes = {k: len(v) for k, v in s.items()}
    print(f"{len(runs)} runs: {sizes}")
    if not s["test"] or not s["train"]:
        print("not enough runs for this split yet")
        return
    print(f"{'model':14s} " + " ".join(f"{c:>13s}" for c in COLS) + "     time")
    for name in a.models:
        t0 = time.time()
        model = pcm_baselines.MAKERS[name]().fit(s["train"] + s["val"])
        res, per_run = evaluate(model, s["test"], a.stride)
        print(f"{name:14s} " + " ".join(f"{res[c]:13.4f}" for c in COLS) + f"  {time.time() - t0:6.1f} s")
        save(a.split, sizes, len(runs), a.stride, name, res, per_run, outdir=a.outdir)


if __name__ == "__main__":
    main()
