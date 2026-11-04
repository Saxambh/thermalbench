"""Fixed ThermBench PCM splits. A case's side depends only on its parameters or a hash of its
id, never on which runs have finished.

  random        80 / 10 / 10 by hash of case_id                      (interpolation)
  ood_fins      test: 4 or 5 fins, train on 0-3                       (unseen geometry)
  ood_drive     test: superheat above the design 90th percentile      (stronger heating:
                (27.81 K; 50 of 500 cases, both materials)             faster, more convective)
  ood_material  test: lauric acid, train on n-octadecane              (Pr 97 vs 56, melting
  ood_material_r  the reverse                                          range vs point)
  ood_tilt      test: tilted 45 deg and heated from below; train on   (regime shift: plumes
                side heating                                           and Benard cells)
For the ood splits, validation is 10 % of the remaining cases by hash. The superheat
threshold is fixed from pcm_full.csv (the Ste threshold would have put only lauric acid in
the test set, mixing material transfer into this split).
"""
from splits import _u

SH_Q90 = 27.81
SPLITS = ("random", "ood_fins", "ood_drive", "ood_material", "ood_material_r", "ood_tilt")


def side(run, split):
    """'train', 'val' or 'test' for one PCMRun."""
    m, cid = run.meta, run.case_id
    if split == "random":
        u = _u(cid, "pcm")
        return "test" if u < 0.1 else "val" if u < 0.2 else "train"
    if split == "ood_fins":
        test = m.get("nfins", 0) >= 4
    elif split == "ood_drive":
        test = m["T_wall_K"] - m["Tmelt_K"] > SH_Q90
    elif split == "ood_material":
        test = m["material"] == "lauric"
    elif split == "ood_material_r":
        test = m["material"] == "octadecane"
    elif split == "ood_tilt":
        test = abs(m.get("tilt_deg", 0.0)) > 1e-9
    else:
        raise ValueError(f"unknown split {split}; one of {SPLITS}")
    if test:
        return "test"
    return "val" if _u(cid, "pcmval") < 0.1 else "train"


def split_runs(runs, split):
    out = {"train": [], "val": [], "test": []}
    for r in runs:
        out[side(r, split)].append(r)
    return out
