# Headline tank table reproduced from the frozen release (7 November 2026)

**Question** (independent review, milestone 3). Can a headline result be rebuilt from the frozen release alone,
without anything left over from training?

**Table reproduced:** the hybrid + canonical-frame rows of the all-models table (dossier §8.4: mean field
error, % of ΔT, seed means, every 10th snapshot), FNO and U-Net, all four splits, every seed.

**Inputs used, and nothing else** (`repro.py`):
- the frozen tank manifest `manifest_full_h5mm.json`, md5 `0e8b6d8ddfc9be4b882e25762c26b3ec`;
- the frozen h5 data the manifest lists;
- the released checkpoints in `results_merged/ckpt/` (md5 of each in `repro_headline.json`);
- the input scaling rebuilt from the manifest's training runs (the cached `.encoder.json` files were not
  used);
- the unchanged scoring path of training: `train.Predictor` and `evaluate.evaluate`, stride 10.

Every test run's score was compared with the score the training job stored on its worker (lab, pc3, pc4,
pc6; copies in `~/tb_verify/mljson`). The recomputation ran on a different machine (laptop GPU).

## Result

**23 of 24 model-split entries were reproduced exactly:** every test run's field error is identical to
the stored value at full floating-point precision (largest per-run difference 0.0), and the split sizes
match. The 24th (U-Net ood_flow seed 2) has no stored score in that copy; it is one of the seeds that
finished later the same day, and its recomputed value is given below.

| Model | random | ood_geom | ood_mode | ood_flow |
|---|---|---|---|---|
| fno_hybrid_canon, seeds | 4.017 / 4.116 / 3.935 | 4.468 / 4.454 / 4.414 | 4.416 / 4.473 / 4.556 | 9.707 / 9.928 / 9.840 |
| fno_hybrid_canon, seed mean | **4.02** | **4.44** | **4.48** | **9.83** |
| unet_hybrid_canon, seeds | 3.631 / 3.517 / 3.724 | 6.149 / 6.024 / 6.513 | 4.685 / 4.170 / 4.259 | 9.313 / 9.061 / 9.259 (new) |
| unet_hybrid_canon, seed mean | **3.62** | **6.23** | **4.37** | **9.21** (3 seeds; 9.19 on the 2 reported) |

Test runs: random 131, ood_geom 224, ood_mode 363, ood_flow 103.

Every seed mean in the dossier's §8.4 for these two rows is reproduced. The U-Net ood_flow entry becomes
9.21 with all three seeds (the dossier showed 9.19 from 2 seeds).

## Scope

- Only the two hybrid + canonical rows. The ablation rows (plain, hybrid-only, canonical-only) were not
  rebuilt, because their checkpoints are not part of the release folder.
- §8.1 (3-seed ensemble on all 120 snapshots) is a different aggregation and was not part of this check,
  although it uses the same checkpoints.
