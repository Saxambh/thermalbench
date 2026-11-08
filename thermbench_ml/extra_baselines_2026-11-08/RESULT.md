# PCM: the 4x4-patch Transolver baseline, results (8 November 2026)

**Jobs:** 36 (plain and hybrid, 3 seeds, 6 splits), lr 3e-4 (chosen on validation, 9294bcd), batch 16,
60 epochs, trained on 6 GPUs, launched 09:24 UTC, last worker done 13:02 UTC.
**Analysis:** as fixed in `PLAN.md` before launch, by `analyse_ts.py`. Tables and all paired intervals are in
`RESULT_ts_tables.md`, numbers in `result_ts.json`. Merged entries: `results_pcm_ts_merged/<split>.json`
(checkpoints in `results_pcm_ts_merged/ckpt`, 36 files, each copied from the worker that trained it; not in
git). FNO, U-Net and baseline numbers are unchanged from `pcm_final_2026-11-08`.

## Reconciliation

- All 36 entries are present; every entry's test IDs equal the frozen split's test IDs; stored sizes equal the
  frozen sizes.
- No problems found.

## Field RMSE, K (seed mean ± SD; per seed in `RESULT_ts_tables.md`)

| Split | Transolver | FNO | U-Net | Transolver hybrid | FNO hybrid | U-Net hybrid | IDW |
|---|---|---|---|---|---|---|---|
| random | 0.66 ± 0.02 | 0.82 | **0.59** | 0.72 | 0.86 | 0.68 | 2.55 |
| ood_fins | 2.31 ± 0.06 | 3.79 | **1.76** | 2.70 | 3.05 | 1.82 | 4.90 |
| ood_drive | 1.11 ± 0.01 | 1.40 | **1.05** | 1.19 | 1.49 | 1.12 | 4.13 |
| ood_tilt | 6.41 ± 0.33 | **6.17** | 6.67 | 6.94 | 6.66 | 7.12 | 7.67 |
| ood_material (held-out lauric acid) | 6.11 ± 0.29 | 12.90 | 5.92 | 7.51 ± 0.22 | 8.82 | 5.61 | **5.35** |
| ood_material_r (held-out n-octadecane) | 16.66 ± 3.48 | 34.45 | 9.19 | 15.77 ± 3.33 | 11.61 | 7.48 | **3.55** |

## What it shows, against the expectations stated in advance

1. **In distribution and on held-out conditions within the same material (expectation 1: met).**
   - Transolver sits between U-Net and FNO in field error on random, fins and drive. Paired against U-Net,
     it is slightly worse (0.07 K on random, 0.55 K on fins, 0.07 K on drive); against FNO it is better on
     all three.
   - On melt time it is the best model on these splits: t90 error 0.7 to 0.8 % on random, 1.0 to 1.1 % on
     drive and 5.6 % (plain) on fins (every run crossed), against 1.1 %, 1.2 % and 7.9 % for the best
     FNO/U-Net. Paired
     against U-Net the t90 advantage is clear on random and fins and not clear on drive.
2. **Geometry (expectation 2: not met).** On unseen tilt, plain Transolver (6.41 K) is between FNO (6.17 K)
   and U-Net (6.67 K); paired, it is worse than FNO by 0.24 K [0.20, 0.28] and better than U-Net by 0.26 K
   [0.21, 0.31]. On unseen fin counts it is behind U-Net. The geometry-oriented design gives no geometry
   advantage on these splits. (The tank geometry split was not tested; see the plan.)
3. **Material transfer (expectation 3: none stated). The failure extends to Transolver.**
   - **Held-out lauric acid:** every Transolver seed is worse than IDW (plain 5.86 to 6.43 K, hybrid 7.28
     to 7.70 K, against 5.35 K). Paired: IDW better by 0.76 K [0.59, 0.93] (plain) and 2.16 K [1.94, 2.37]
     (hybrid). Plain Transolver has the smallest seed spread of the neural models here (± 0.29 K).
   - **Held-out n-octadecane:** much worse than IDW in every seed (12.52 to 20.52 K against 3.55 K) and
     worse than U-Net. The predictions rarely reach a liquid fraction of 0.9 within the horizon: 5 of 250
     runs (plain) and 16.7 of 250 (hybrid), seed mean. The t90 errors on those few runs (219 %, 282 %) are
     not interpretable and no paired t90 is given (too few runs cross in every seed).
   - Unlike FNO, the hybrid prior does not rescue Transolver on this direction (15.77 K against 16.66 K
     plain; FNO went from 34.45 to 11.61 K).
   - **Statement for the paper:** IDW had lower field RMSE than every seed of both Transolver variants in
     both transfer directions. The material-transfer limitation is therefore not specific to FNO and U-Net;
     it holds for all three evaluated architectures (scoped to these implementations).
4. **No new winner.** Transolver does not change any "best neural" entry for field error. It gives the
   lowest melt-time error on random, fins and drive.

## WARN sensitivity

- Removing the 39 solver-WARN cases changes Transolver field RMSE by at most 0.07 K.
- As before, this tests exclusion from scoring, not retraining.

## Limits

- One transformer operator, one configuration (4x4 patches, 1.16 M parameters), one tuned learning rate;
  the conclusion is about this implementation.
- PCM only. The tank was not run (overfit gate, see `PLAN.md`), so whether Transolver helps on unseen tank
  widths is open.
- Paired intervals hold the seed mean fixed (as in `pcm_final_2026-11-08`); seed results are listed
  alongside.
