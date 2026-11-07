"""Fit and score the multi-node baseline (multinode.py) on the four tank splits, as committed in 60223ee.

  python mn_eval.py [split ...]
Fits on each split's train + val runs, scores the test runs with evaluate.evaluate (stride 10, the same
metrics and snapshots as every other model) and merges the entry "multinode" into results/<split>.json,
with the fitted parameters and fit losses. Also writes results/multinode_fit.json.
"""
import json, os, sys, time
import evaluate
from data import index, DEFAULT_ROOTS
from splits import SPLITS, split_runs
from multinode import MultiNode

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(HERE, "manifest_full_h5mm.json")
runs = index(DEFAULT_ROOTS, manifest=MAN)
log = {}
for split in (sys.argv[1:] or SPLITS):
    s = split_runs(runs, split)
    t0 = time.time()
    m = MultiNode().fit(s["train"] + s["val"])
    t1 = time.time()
    res, per_run = evaluate.evaluate(m, s["test"], 10)
    evaluate.save(split, {k: len(v) for k, v in s.items()}, len(runs), 10, "multinode", res, per_run,
                  {"fit": m.fit_info, "fit_min": round((t1 - t0) / 60, 1)})
    log[split] = {"fit": m.fit_info, "test": res}
    json.dump(log, open(os.path.join(HERE, "results", "multinode_fit.json"), "w"), indent=1)
    print(f"{split:8s} fit {(t1 - t0) / 60:.1f} min  " + "  ".join(f"{k} {v:.4f}" for k, v in res.items()) + "\n   " +
          "; ".join(f"{k}: start {v['start_loss']:.4f} -> {v['loss']:.4f}, params {[round(x, 3) for x in v['params']]}" for k, v in m.fit_info.items()), flush=True)
