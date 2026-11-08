# Extra neural baseline: a transformer operator (Transolver) (plan, 8 November 2026)

Written and committed **before the model is trained or scored**, as for the multi-node baseline (60223ee).
Deferred until the main tank and PCM results existed (tank: 96 jobs, reproduced; PCM: 72 jobs, e9716a6 and
34decfe). Results will be reported as obtained, including where they are worse.

## Why, and why only this one (decision 8 November)

- **Main reason:** the main PCM finding is that FNO and U-Net do not transfer to an unseen material (both
  lose to IDW). A geometry-aware attention-based operator tests whether that failure is specific to these two
  architectures or common to current operator learners.
- **Secondary reason:** it also tests whether an architecture built for varying geometry does better on
  unseen tank widths (ood_geom), fin counts and tilt.
- **DeepONet was considered and dropped.**
  - Its linear decoder approximates moving sharp fronts poorly (Lanthaler, Molinaro, Hadorn, Mishra, ICLR
    2023; Seidman et al., NeurIPS 2022), and both families are front problems. Its failure would be
    predictable rather than informative.
  - The benchmark's code is released so others can add models.
- **Not required for the paper's validity:** precedent benchmarks ship with two or three neural architectures
  (PDEBench, The Well). This is an extension, run on otherwise idle GPUs.

## Model (added to `models.py` with the same interface as FNO and U-Net)

**Transolver** (`transolver`; Wu, Luo, Wang, Wang, Long, ICML 2024), a physics-attention transformer for
general geometries.
- **Tokens:** grid cells, carrying the input channels plus the same 2 normalised coordinates FNO uses.
- **Structure:**
  - 6 layers, width 128, 8 heads, 32 physics slices;
  - attention cost linear in the number of cells, which is needed at up to 80,000 cells (tank) and
    24,000 (PCM);
  - pre-norm, MLP ratio 4, as in the reference design.
- **Size:** targets 1 to 3 M parameters, within the range of FNO (2.1 M) and U-Net (7.8 M). The exact count is
  recorded at the first run and not tuned against scores.

**Interface:** the network maps the same input grid [C, ny, nx_max] (the unchanged tank and PCM encoders) to
one output field. The data, padding, masks, hybrid and canonical options, loss and evaluation are untouched.

**Code check before the pilot:** overfit a few training samples, on training data only. The loss must fall to
near zero.

## Training (identical to the existing jobs)

- `train.py` / `pcm_train.py` are unchanged apart from registering the model:
  - AdamW (weight decay 1e-4), OneCycle schedule;
  - best-validation checkpoint, test scored once with it;
  - batch 8, 60 epochs (as FNO);
  - same stride and test snapshots.
- **One allowed tuning step, on validation data only:**
  - peak learning rate in {1e-3, 3e-4};
  - chosen by validation loss on the random split, seed 0, separately for tank and PCM;
  - then frozen for every split and seed;
  - recorded in this folder before the full runs start.
  - Reason: transformers are often unstable at 1e-3, and choosing on test would bias the comparison.
- Batch size may be reduced to fit GPU memory (recorded if so). Nothing else is changed.

## Jobs

| Family | Variants | Seeds | Splits | Jobs |
|---|---|---|---|---|
| Tank | plain; hybrid + canonical (the headline variant) | 3 | 4 | 24 |
| PCM | plain; hybrid | 3 | 6 | 36 |

- **Total:** 60 jobs on the free GPUs (lab, pc3, pc4, pc6, pc7, laptop), distributed and supervised like the
  main runs (with the `wait` fix, e9716a6).
- **Not included:** the full 2 × 2 ablation. It was run for FNO and U-Net.
- **Cost:** from the measured FNO epoch times, about 2× FNO per epoch. That is about 90 GPU-hours (range 70
  to 130), about 13 to 20 h wall-clock on the 6 GPUs. The estimate is refined from the pilot's timing before
  launch.

## Analysis (same scripts, decided now)

- Scored by the unchanged `evaluate.py` / `pcm_evaluate.py`; merged by `results_all.sh`.
- **Reconciliation:** every entry's test IDs against the frozen splits.
- **Tables:** the existing per-split tables gain the Transolver rows (seed mean ± seed SD).
- **Paired intervals, descriptive, not pre-registered tests:**
  - against FNO and U-Net in the same variant;
  - against IDW on PCM;
  - design-level for the tank (as `stats_2026-11-07`), run-level for PCM (as `pcm_final_2026-11-08/paired.py`).
- **Reporting:** results reported as obtained. No re-runs or changes after scoring, except to fix a
  demonstrated code error. Any such fix is reported with before and after.

## Expectations stated in advance (to be checked, not defended)

1. Competitive with FNO and U-Net in distribution.
2. Possibly better on the geometry splits (ood_geom, ood_fins, ood_tilt).
3. No expectation either way on material transfer. Either outcome is reported as a finding.

## References to verify (DOIs before the paper)

- Wu, Luo, Wang, Wang, Long, "Transolver: A fast transformer solver for PDEs on general geometries",
  ICML 2024.
- Lanthaler, Molinaro, Hadorn, Mishra, ICLR 2023; Seidman, Kissas, Perdikaris, Pappas, NeurIPS 2022 (reason
  for dropping DeepONet).
- Takamoto et al., PDEBench (NeurIPS 2022 Datasets and Benchmarks); Ohana et al., The Well (NeurIPS 2024
  Datasets and Benchmarks).

## Amendment 1 (8 November, before any validation or test data was used)

Code check (`overfit_timing.py`, training data only: 8 fixed training samples; timing at the job batch of 16
on the largest grid; pc4 and lab, RTX 4070 Ti):

| Tokens | Tank: s per step (FNO 0.067) | Tank: overfit RMSE | PCM: s per step (FNO 0.037) | PCM: overfit RMSE |
|---|---|---|---|---|
| every cell (as planned) | 1.016 | 0.112 after 400 steps | 0.612 | 0.235 after 400 steps |
| 2 x 2 patches | 0.257 | 0.094 after 400 | 0.149 | 0.221 after 400 |
| **4 x 4 patches** | **0.055** | 0.093 (1e-3 OneCycle) / 0.053 (3e-4 OneCycle), 1600 steps | **0.048** | **0.033** (1e-3 OneCycle), 1600 steps |
| FNO, for reference | | 0.0042 after 400 | | 0.0167 after 400 |

**Changes:**
1. **Tokens are 4 x 4 cell patches.** They are embedded by a patch convolution and decoded per token to its
   16 cells, as in vision transformers (models.py, `patch=4`). Per-cell tokens cost 15 times FNO and fit no
   better.
2. **Scope:**
   - **PCM is run now.** It fits its training samples, and it is where the reason for this baseline lies:
     material transfer.
   - **The tank is run only if a tank overfit check passes,** with masked RMSE ≤ 0.01 on the same 8 samples
     within 1600 steps.
   - This allows at most 2 hours of architecture work, training data only. One candidate is local
     convolutions in the slice projections, as in the reference structured-mesh Transolver.
   - If the check fails, Transolver is reported for PCM only, with this table as the reason.
3. **Cost:** about the same as FNO per step, so 36 PCM jobs take about 20 GPU-hours (3 to 4 h on 6 GPUs).

**Unchanged:**
- The learning-rate rule: {1e-3, 3e-4}, chosen by best validation loss on the PCM random split, plain
  variant, seed 0. The test score that pcm_train.py also writes is not used for the choice.
- Everything else in this plan.
