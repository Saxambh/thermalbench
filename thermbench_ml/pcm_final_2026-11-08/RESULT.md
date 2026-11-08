# PCM benchmark: final evaluation (8 November 2026)

**Data:** frozen manifest `manifest_pcm.json` (md5 19397b78...), 500 runs, six splits.

**Models:**
- 4 neural models (FNO, U-Net, each plain and hybrid), 3 seeds each, trained on 6 GPUs: 72 jobs;
- 7 baselines.

**Processing:** merged with `results_all.sh pcm` into `results_pcm_merged/`; scored by `analyse.py`.
Full tables are in `RESULT_tables.md`, numbers in `result.json`.

## Reconciliation

- Every entry's per-run test IDs equal the frozen split's test IDs (`pcm_splits.split_runs` on the frozen
  manifest).
- The stored split sizes equal the frozen ones.
- All 72 neural jobs are present.
- No problems found.

## Main results (field RMSE in K; neural: mean of 3 seeds ± seed SD)

| Split (test runs) | Best neural | Best baseline | t90 error, best neural / best baseline |
|---|---|---|---|
| random (52) | U-Net 0.59 ± 0.01 | RBF 1.98 | 1.1 % / 9.1 % |
| ood_fins (139) | U-Net 1.76 ± 0.07 | IDW 4.90 | 7.9 % (FNO hybrid) / 26.2 % (front) |
| ood_drive (51) | U-Net 1.05 ± 0.06 | RBF 4.02 | 1.2 % / 8.4 % |
| ood_tilt (150) | FNO 6.17 ± 0.58 | IDW 7.67 | 13.5 % (FNO hybrid) / 20.7 % (IDW) |
| ood_material (250) | U-Net hybrid 5.61 ± 1.38 | **IDW 5.35** | 36.1 % (U-Net) / **16.9 % (IDW)** |
| ood_material_r (250) | U-Net hybrid 7.48 ± 1.42 | **IDW 3.55** | 30.4 % (U-Net hybrid) / **17.6 % (front)** |

t90 error is relative and conditional on the prediction crossing a liquid fraction of 0.9 within the
input-only horizon (tau ≤ 3 t_ref). Crossing counts are in `RESULT_tables.md`.

## What it shows

1. **Interpolation within the design space** (random, unseen fin counts, unseen drive): the neural models
   are clearly best.
   - Field error is 2 to 4 times lower than the best baseline.
   - Melt-time error is 1.1 to 1.2 % on random and drive, against 8 to 9 % for the best baseline.
   - U-Net leads FNO on these three splits.
2. **Unseen tilt:** the neural models are only modestly better (6.2 to 7.1 K against 7.7 K for IDW), and
   all models are much worse than in distribution.
3. **Unseen material:** the neural models do **not** beat simple interpolation.
   - Error: IDW 5.35 K vs U-Net hybrid 5.61 K on ood_material; IDW 3.55 K vs U-Net hybrid 7.48 K on
     ood_material_r.
   - Seeds disagree strongly: FNO 12.90 ± 8.72 K on ood_material and 34.45 ± 9.59 K on ood_material_r.
   - On ood_material_r, plain FNO crosses t90 in only 83 of 250 runs (seed mean) and U-Net in 195 of 250.
   - The hybrid variants are steadier, but they are still worse than IDW.
   - Material transfer is an open problem on this benchmark, not a solved one.
4. **No single architecture wins everywhere.** U-Net leads on random, fins, drive and material, FNO on tilt.
   The hybrid prior helps most where the plain models are unstable (FNO on both material splits).

## WARN sensitivity (review item 3.6)

- **Setup:** the 39 retained solver-WARN cases fall into the test sets as follows: random 3, fins 15,
  drive 4, material 24, material_r 15, tilt 11.
- **Effect of removing them:**
  - neural field RMSE changes by at most 0.10 K;
  - baseline field RMSE changes by at most 0.60 K (RBF, tilt).
- **Ordering:**
  - the ordering of the four neural models is unchanged on every split and metric;
  - every neural-versus-best-baseline conclusion above is unchanged;
  - the only order changes are swaps between near-tied baselines, e.g. kNN/IDW on random, IDW/front on tilt.
- **Conclusion:** the retained WARN cases do not influence the PCM conclusions.

## Limits

- **Statistics:** descriptive means; seed SD over 3 seeds; no design-level intervals yet. The material-split
  seed spread is large enough that single-seed rankings there would not be reliable.
- **Crossing:** "crossed" counts the prediction's crossing within the horizon. The t90 error is conditional
  on that, so a model that crosses less often is scored on an easier subset. Read the two columns together.
- **Scope:** two materials only. "Unseen material" is transfer between them in either direction, not to a
  third material.

## Housekeeping

- **Bug:** `run_final_pcm.sh` ended with a bare `wait`. This also waited for the `tee` log process
  substitution, so every worker hung after its last job and never logged "done".
- **Impact:** no effect on results (all jobs had finished and written their entries).
- **Fix:** the script now waits for the slot PIDs only.
