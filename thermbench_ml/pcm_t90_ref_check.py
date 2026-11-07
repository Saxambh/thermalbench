"""Reference t90 sampling check (review, 8 November 2026).

pcm_evaluate.py takes the reference t90 from the PCM-cell mean liquid fraction at the saved field snapshots,
linearly interpolated (pcm_metrics._t_cross). The h5 also holds series/liquid_fraction every 10 solver steps
(the series used for the revised mesh study). On the test runs of a split, compare:
  t90_snap   evaluator's reference (snapshot alpha mean over the PCM mask)
  t90_dense  crossing of series/liquid_fraction
and, to confirm the two liquid fractions are the same quantity, the series value interpolated to the
snapshot times against the snapshot mask mean.
  python pcm_t90_ref_check.py [split ...]      (default: all six)
Writes pcm_t90_ref_check.json.
"""
import json, os, sys
import numpy as np
import h5py
from pcm_data import index
from pcm_splits import SPLITS, split_runs
from pcm_metrics import _t_cross

HERE = os.path.dirname(os.path.abspath(__file__))
runs = index(["~/tb_data/pcm_frozen"], manifest=os.path.join(HERE, "manifest_pcm.json"))
out = {}
for split in (sys.argv[1:] or SPLITS):
    rows = []
    for r in split_runs(runs, split)["test"]:
        t = r.times()[0]
        w = r.mask() > 0
        f_snap = r.field("alpha")[:, w].mean(1)
        with h5py.File(os.path.join(r.path, "thermbench.h5")) as f:
            ts, lf = f["series/t_s"][:], f["series/liquid_fraction"][:]
        a, b = _t_cross(t, f_snap), _t_cross(ts, lf)
        rows.append({"run_id": r.run_id, "t90_snap_s": float(a), "t90_dense_s": float(b),
                     "rel_diff": float((a - b) / b),
                     "snap_interval_s": float(np.median(np.diff(t))),
                     "lf_definition_maxdiff": float(np.max(np.abs(np.interp(t, ts, lf) - f_snap)))})
    d = np.array([x["rel_diff"] for x in rows])
    out[split] = {"n": len(rows), "rel_diff_median": float(np.median(d)), "abs_rel_diff_mean": float(np.mean(np.abs(d))),
                  "abs_rel_diff_max": float(np.max(np.abs(d))),
                  "lf_definition_maxdiff_max": float(max(x["lf_definition_maxdiff"] for x in rows)), "rows": rows}
    print(f"{split:15s} n {len(rows):3d}  t90 snapshot vs dense: median {100*np.median(d):+.3f} %, mean |.| {100*np.mean(np.abs(d)):.3f} %, "
          f"max |.| {100*np.max(np.abs(d)):.3f} %  | liquid-fraction definitions differ by at most {out[split]['lf_definition_maxdiff_max']:.4f}", flush=True)
json.dump(out, open(os.path.join(HERE, "pcm_t90_ref_check.json"), "w"), indent=1)
