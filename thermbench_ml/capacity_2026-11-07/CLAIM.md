# Tank ML capacity: claim (2026-11-07)

Main model: FNO hybrid in the canonical frame, mean of 3 seeds. Every test run of the four fixed design-level
splits was predicted (random 131, ood_geom 224, ood_mode 363, ood_flow 103). Data: ml_spread.json
(spread.py, analysed with an.py); CFD times: cfdt_all.txt (285 dataset solver logs).

## Claim

The model predicts the full transient temperature field of an unseen tank case (120 snapshots) in about
1.5 s on a laptop GPU, where the CFD needs a median of 2.6 h on one core. It reaches a median field error of
3.3 % of ΔT on held-out designs, with stored energy within 0.24 % and outlet temperature within 0.54 K
(medians). That is half the error of the best interpolation baseline and about a quarter of the error of a 1D
ideal-stratification model. The accuracy carries over to tank widths outside the training range (3.5 %) and to
discharge operation never seen in training (3.7 %), where the interpolation baselines fail entirely. The
ensemble also indicates when it should not be trusted. Across all four test sets, the disagreement between
the three trained models ranks the error of a run with Spearman ρ = 0.82 to 0.94. The 10 % most uncertain
runs contain 68 of the 81 worst-10 % runs (84 %), and every run with an error above 10 % lies in the
more-uncertain half. Within a run, the 10 % of cells with the highest disagreement hold about three quarters
of the squared error, so the spread also shows where the prediction is wrong. The hard cases are fast
turbulent jets in weakly stratified tanks (Ri < 5, 12 % of the dataset), and they are the cases the ensemble
flags.

## Numbers

| Split | Field RMSE, median (mean) % ΔT | Energy, median % | Outlet, median K | Best interpolation (RBF), mean | 1D ideal stratification, mean |
|---|---|---|---|---|---|
| random | 3.3 (4.1) | 0.24 | 0.54 | 8.7 | 15.3 |
| ood_geom | 3.5 (4.4) | 0.23 | 0.63 | 10.8 | 16.0 |
| ood_mode | 3.7 (4.5) | 0.28 | 0.61 | 64 (fails) | 16.5 |
| ood_flow | 8.7 (9.5) | 0.70 | 1.38 | 15.1 | 22.8 |

| Split | ρ(spread, error), runs | Worst 10 % caught by top-10 % spread | Error > 10 % in upper-spread half | Error share in top-10 % spread cells | Median error, lower vs upper spread half |
|---|---|---|---|---|---|
| random | 0.86 | 11 / 13 | 4 / 4 | 74 % | 2.4 vs 4.8 |
| ood_geom | 0.86 | 19 / 22 | 13 / 13 | 79 % | 2.2 vs 5.3 |
| ood_mode | 0.82 | 29 / 36 | 20 / 20 | 78 % | 2.7 vs 5.4 |
| ood_flow | 0.94 | 9 / 10 | 35 / 35 | 55 % | 6.9 vs 11.0 |

Speed: 1.45 s median per run for 3 seeds on the laptop RTX 4060, against a 2.6 h median CFD (10 to 90 %:
0.6 to 8.4 h) on one CPU core, about 6,000 times faster. The hardware differs (one GPU against one CPU core),
so this is stated as a wall-clock comparison, not as equal-hardware cost.

## Spread calibration (fitted on validation runs only, checked on test runs)

The bound is error ≤ k × spread, with k fitted on each split's validation runs (calib.py, calib_an.py,
ml_calib_summary.json). The constant bound is the same quantile of the validation errors, applied to every
case regardless of spread.

| Split | k for 90 % (run) | Test coverage, 90 % / 95 % | Constant bound coverage, 90 % / 95 % | Median 90 % bound, spread vs constant |
|---|---|---|---|---|
| random | 4.0 | 91 % / 96 % | 87 % / 92 % | 5.2 vs 7.9 % ΔT |
| ood_geom | 3.5 | 88 % / 93 % | 84 % / 89 % | 5.1 vs 7.5 |
| ood_flow | 3.7 | 90 % / 94 % | 19 % / 37 % | 10.5 vs 6.9 |
| ood_mode | 3.2 | **71 % / 84 %** | 83 % / 93 % | 4.5 vs 7.7 |

Per-snapshot calibration gives the same picture: random 90 % / 95 %, ood_geom 88 / 94, ood_flow 84 / 93,
ood_mode 77 / 86.

- **In distribution and for unseen widths,** "error ≤ about 4 × spread" holds at the stated rate. It is about
  a third tighter than a constant bound and adapts to the case: about 4.3 % ΔT for easy runs, 6.5 % for hard
  ones.
- **For faster inflow than in training,** the spread bound keeps its coverage (90 %) while a constant bound
  collapses (19 %). The spread grows with the extrapolation.
- **For an operating mode never trained (discharge),** the spread under-covers: 71 % against 90 %. The
  spread does not grow enough for a change of operation, so for ood_mode the bound is not reliable.

## Limits, stated with the claim

- **Spread is under-dispersed (about 0.38 of the error)** and is used only through the calibrated factor above; it does not cover the change to an unseen operating mode (ood_mode 71 % at 90 %).
- **Faster inflow than in training (ood_flow).** The median error rises to 8.7 %; the spread flags this but
  does not remove it.
- **Label uncertainty in the hard regime.** In the fast-jet, low-Ri regime the CFD labels have their own
  uncertainty: T0211 changed by 7.4 % of ΔT with tighter time stepping. A test of neighbouring designs is
  running, so part of the error there may be label error.
- **Not yet checked:**
  - horizontal stitching lines visible in the predicted fields of the hard cases;
  - the other architectures (U-Net and the ablations);
  - design-level confidence intervals.
