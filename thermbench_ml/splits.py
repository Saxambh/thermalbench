"""Fixed ThermBench splits. Assignment is by design point (case_id), so the laminar and SST
twins of one design point never sit on both sides of a split, and it does not depend on
which runs have finished: a case's side is decided by its parameters or a hash of its id.

  random    80 / 10 / 10 by hash of case_id                      (interpolation)
  ood_flow  test: Re_in above the design 90th percentile (9007)  (unseen faster inflow)
  ood_geom  test: W outside the design 10-90 % band [0.33, 0.93] (unseen tank shapes)
  ood_mode  test: all discharge cases, train on charging only    (unseen operation)
For the ood splits, validation is 10 % of the remaining cases by hash.
Thresholds are fixed from design_v2_full.csv (1024 cases), not recomputed.
"""
import hashlib

RE_Q90 = 9007.0
W_Q10, W_Q90 = 0.33, 0.93
SPLITS = ("random", "ood_flow", "ood_geom", "ood_mode")


def _u(case_id, salt=""):
    """Stable pseudo-random number in [0, 1) from the case id."""
    return int(hashlib.md5((salt + case_id).encode()).hexdigest()[:8], 16) / 2 ** 32


def side(run, split):
    """'train', 'val' or 'test' for one Run (see data.Run)."""
    m, cid = run.meta, run.case_id
    if split == "random":
        u = _u(cid)
        return "test" if u < 0.1 else "val" if u < 0.2 else "train"
    if split == "ood_flow":
        test = m["Re_in"] > RE_Q90
    elif split == "ood_geom":
        test = not (W_Q10 <= m["W_m"] <= W_Q90)
    elif split == "ood_mode":
        test = m["mode"] == "discharge"
    else:
        raise ValueError(f"unknown split {split}; one of {SPLITS}")
    if test:
        return "test"
    return "val" if _u(cid, "val") < 0.1 else "train"


def split_runs(runs, split):
    out = {"train": [], "val": [], "test": []}
    for r in runs:
        out[side(r, split)].append(r)
    return out
