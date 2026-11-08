# PCM: all 108 release checkpoints rescored (8 November 2026)

**Scope:** every neural row of the PCM tables: FNO, U-Net and the 4x4-patch Transolver, each plain and
hybrid, 3 seeds, 6 splits. This completes the release check done for the tank in `repro_all_2026-11-08`.

**Method:**
- **Collection** (`collect_ckpt.sh`): each checkpoint was copied from the worker that produced its stored
  score (the `sources` field of the merged results) into `results_pcm_release/ckpt`. The worker and md5 of
  every file are in `ckpt_sources.tsv` (lab 29, pc3 17, laptop 16, pc6 16, pc7 16, pc4 14).
  - The 18 FNO hybrid checkpoints copied earlier to `results_pcm_merged/ckpt` are byte-identical to these.
- **Rescoring** (`repro_pcm.py <worker>`, merged by `merge.py` into `repro_pcm.json`):
  - each worker rescored the checkpoints it produced, after checking that its local file has the same md5
    as the release copy;
  - the input encoder was rebuilt from the split's training runs, using the frozen manifest
    (md5 19397b78... on all six machines);
  - scoring used the unchanged `pcm_train.Predictor` + `pcm_evaluate.evaluate` at stride 5, as in training;
  - every test run was compared with the per-run score stored by the training job.
- **Code:** identical on all six machines (md5 of models.py, pcm_train.py, pcm_evaluate.py, pcm_data.py,
  pcm_splits.py, pcm_metrics.py and the manifest checked before launch).

## Result

- **108 of 108 checkpoints reproduce their stored scores exactly.** That covers 16,056 per-run scores, and
  the maximum difference is 0.0 on every metric compared: field RMSE (`rmse_K`), liquid-fraction RMSE,
  liquid IoU, energy error, t90 crossing and t90 error.
- No missing files and no md5 mismatches.

## On different hardware (the first, stopped run)

- **The first attempt** rescored the release copies on the laptop alone (RTX 4060 Laptop). It was stopped by
  the session for low memory after 6 checkpoints (`stopped_run_laptop_*`).
- **Exact:** the three trained on RTX 4060-class GPUs (laptop, pc6, pc7).
- **Small differences:** the three trained on RTX 4070 Ti GPUs (lab, pc4) differed by at most 0.00016 K
  per run:

  | Checkpoint (random split) | Trained on | Largest per-run field RMSE difference |
  |---|---|---|
  | fno | lab | 0.00016 K |
  | fno_s1 | lab | 0.00008 K |
  | fno_hybrid | pc4 | 0.000002 K |

  Rescored on their own machines, all three are exact.
- **Reading:** this is floating-point variation between GPU models. It is far below any reported digit, and
  a user rescoring on other hardware should expect agreement to about 1e-4 K, not bit-identity.
- **The tank rescore differs:** it reproduced all 96 checkpoints bit-exactly on the laptop, including those
  trained on the 4070 Ti machines.

## What this establishes

- Every neural row of the PCM tables can be regenerated from the released data and checkpoints.
  - Bit-exactly on the training GPU type.
  - To about 1e-4 K across GPU types.
- Together with the tank (96 of 96), all 204 released checkpoints are verified, each from the worker that
  produced its score.
