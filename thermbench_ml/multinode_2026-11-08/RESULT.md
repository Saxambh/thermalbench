# Multi-node 1D tank model as a physics baseline: result (8 November 2026)

**Question.** Does a field surrogate beat the calibrated 1D tank model an engineer would use in a system
simulation? The earlier physics baseline, "ideal stratification", is an idealised limit, not a deployed model.

**Model** (`../multinode.py`):
- **Structure:** 200 layers, plug flow between each run's actual inlet and outlet rows, Ri-dependent
  inlet-entrainment diffusivity, and removal of inversions by mixing.
- **Fitting:** four parameters, fitted separately for laminar and SST on each split's train + val designs
  only.
- **Protocol:** committed in 60223ee before any test score was computed, then scored once on the test sets
  with the same metrics and snapshots as every other model (`../mn_eval.py`).
- **Run time:** about 0.05 s per run; fitting took 9 to 10 min per split on one CPU.

**Comparison** (`compare.py`, `compare.json`, full tables in `RESULT_tables.md`):
- per-run differences, other model minus multi-node, averaged per design (positive means multi-node is
  better);
- percentile bootstrap over designs, 10,000 resamples, marginal 95 % intervals;
- descriptive, not pre-registered tests;
- neural models are the mean of 3 seeds, scored on every 10th snapshot.

## Means (multi-node vs the two hybrid + canonical surrogates)

| Split | Field, % ΔT (MN / FNO / U-Net) | Profile, % ΔT | Energy, % of a charge | **Outlet T, K** | Midpoint, mm |
|---|---|---|---|---|---|
| random | 7.07 / 4.02 / 3.62 | 6.21 / 2.53 / 2.26 | 0.55 / 0.50 / 0.38 | **0.83** / 0.85 / 0.67 | 12.7 / 6.8 / 6.0 |
| ood_geom | 7.56 / 4.44 / 6.23 | 6.65 / 2.89 / 3.11 | 0.70 / 0.56 / 0.85 | **0.95** / 1.01 / 2.01 | 16.2 / 8.7 / 9.6 |
| ood_mode | 7.58 / 4.48 / 4.37 | 6.63 / 2.90 / 3.02 | 0.73 / 0.53 / 0.55 | **0.98** / 1.17 / 1.29 | 15.1 / 7.7 / 8.2 |
| ood_flow | 13.61 / 9.83 / 9.21 | 9.60 / 5.51 / 5.46 | 2.04 / 1.28 / 1.45 | **1.46** / 1.80 / 1.62 | 47.0 / 27.9 / 30.8 |

## Paired differences, design-level 95 % intervals

- **Field, profile and thermocline midpoint:** both surrogates are better than the multi-node model on
  **every split**, with every interval excluding zero.
  - Field: 1.46 to 4.40 pp of ΔT better. The smallest is U-Net on unseen widths, 1.46 pp [0.88, 2.04];
    corrected after review from "3.1 to 4.4".
  - Profile: 3.61 to 4.14 pp better. This is the most informative comparison, because the profile is the
    observable both model types are designed to predict.
  - Midpoint: 6.61 to 19.14 mm better. This is conditional on both fields having a defined crossing.
- **Outlet temperature** (area-averaged, the benchmark's outlet metric):

| Split | FNO minus MN | U-Net minus MN |
|---|---|---|
| random | +0.01 K [−0.09, +0.10], no clear difference | −0.16 K [−0.24, −0.07], U-Net better |
| ood_geom | +0.03 K [−0.06, +0.14], no clear difference | **+1.13 K [+0.75, +1.54], MN better** |
| ood_mode | **+0.17 K [+0.02, +0.34], MN better** | **+0.31 K [+0.12, +0.52], MN better** |
| ood_flow | **+0.33 K [+0.22, +0.44], MN better** | **+0.15 K [+0.04, +0.27], MN better** |

- **Stored-energy proxy:** small differences, generally favouring the surrogates. Seven of eight point
  estimates favour a surrogate; the largest is 0.76 pp (FNO, ood_flow). On unseen widths the 1D model leads
  U-Net by 0.12 pp [−0.06, +0.27], an interval spanning zero.
- **Intervals spanning zero** (FNO outlet on random and ood_geom) establish neither equivalence nor a
  negligible difference: "no clear difference".
- **Against the other baselines:** multi-node beats ideal stratification on every metric and split, and
  beats RBF interpolation on most metrics. On discharge it transfers without any special treatment (7.6 %
  field error), where RBF and the plain networks fail (64 to 67 %).

## What it shows (wording agreed after review, 8 November)

1. **Internal stratification:** both hybrid-canonical surrogates predict it more accurately than the
   calibrated 1D model on all four splits.
2. **Near-outlet temperature:** the 1D model is competitive. It has lower error than both surrogates on the
   held-out discharge (ood_mode) and high-flow (ood_flow) cases. This is the area-averaged port-adjacent
   cell temperature; usefulness for the delivered (flow-weighted) fluid temperature would need a
   flux-weighted comparison.
3. **Discharge is the clearest engineering example.** Calibrated on charging cases only, the 1D model has
   7.58 % field error on discharge against 4.48 % (FNO) and 4.37 % (U-Net). On the same designs it has lower
   near-outlet temperature error, by 0.17 K [0.02, 0.34] and 0.31 K [0.12, 0.52]. The preferred model
   changes with the quantity of interest.

**Manuscript wording:**
"Across four tank splits, both hybrid-canonical surrogates reduced vertical-profile error by 3.6–4.1
percentage points of ΔT and thermocline-midpoint error by 6.6–19.1 mm relative to the calibrated multi-node
model. The multi-node model achieved lower near-outlet temperature error than both surrogates on held-out
discharge and high-flow cases. For these benchmark conditions, the benefit of full-field prediction depended
on which thermal quantity was required."

## Limits

- **Simple fit:** Nelder-Mead from one start, 150 evaluations, on a 60-run subsample per closure. The
  laminar fits moved the mixing depth to the whole tank, which acts as Ri-dependent extra diffusion. The
  fit improved the training loss only modestly (0.059 to 0.054 laminar, 0.079 to 0.071 SST). This limits
  conclusions about the best attainable 1D performance. Better optimisation of the training-profile
  objective could improve or worsen held-out outlet error. No refit is needed for the stated comparison.
- **Outlet metric:** the 1D model's outlet value is the layer temperature at the outlet height, compared
  with the same area-averaged outlet metric as every model. It is not the flow-weighted temperature.
- **Statistics:** descriptive marginal intervals, no multiplicity correction. The tank surrogate results are
  seed means, not the ensemble.
