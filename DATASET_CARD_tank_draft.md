# ThermalStorageBench: tank dataset (draft dataset card, 2026-11-06)

Draft for the release. Every number below was checked against the frozen manifest
(`thermbench_ml/manifest_full_h5mm.json`, created 2026-11-05 05:14 UTC), the design list
(`design_h5mm_full.csv`) and the code named. Verification results that are still running are marked.

## Contents

- **1,212 simulations of 1,020 distinct design points** (2D rectangular water tanks, charging and
  discharging).
- **Turbulence treatment, assigned by inlet Reynolds number** (`scripts/make_design.py`, line 54):
  laminar if Re < 1,500; k-omega SST if Re > 3,000; both models between.

  | Design points | Runs |
  |---|---|
  | laminar only: 432 | 432 |
  | SST only: 396 | 396 |
  | both laminar and SST: 192 | 384 |
  | **total 1,020** | **1,212** |

  So the dataset is not "606 designs run with both models"; only 192 design points have both.
- **Design:** Sobol sample of 1,024 design points, 1,217 planned runs. **The dataset was built from
  `design_v2_full.csv`**, with geometry snapped to a 10 mm grid; all 1,212 runs match it exactly.
  `design_h5mm_full.csv` is an unsnapped variant: it differs from the dataset in 613 port offsets and
  184 widths and must not be used to regenerate runs (found 2026-11-06).
  - Inlet velocity 0.005 to 0.2 m/s (log), ΔT 5 to 50 K, slot height 20 to 80 mm, port offset 0 to 0.2 H,
    tank width 0.25 to 1.0 m (H = 1 m).
  - Inlet type: A, side-wall slots (844 runs) or B, lid and bottom slots (368).
  - Operation: charging (849) or discharging (363).
  - Initial state: uniform (853) or pre-stratified with a tanh thermocline (359).
- **Numerics:** buoyantPimpleFoam (OpenFOAM v2606), real water properties, uniform 5 mm mesh,
  PIMPLE nOuterCorrectors 2, nCorrectors 2, maxCo 0.5, maxDeltaT 0.5 s, serial runs. SST runs use
  OpenFOAM's buoyancyTurbSource.
- **Per run:** one `thermbench.h5` (about 18 to 40 MB) with:
  - 121 snapshots of T, p_rgh, ux and uy (plus k, omega, nut for SST) on the native grid;
  - stored energy, exergy, MIX number, stratification number, thermocline midpoint and thickness,
    mean T and outlet T per snapshot;
  - dense outlet and mean-T time series;
  - `case.json` with all inputs.

## Runs excluded from the planned 1,217

| Run | Reason | Rule |
|---|---|---|
| T0073_lam | QC energy check FAIL (energy balance error 5.86 % of exchanged energy) | QC filter in `data.index`: only OK or WARN runs enter the manifest |
| T0765_lam, T0765_sst | Discharge with the hot layer entirely above the outlet: almost no energy leaves (0.034 % of stored energy), so the energy check cannot judge them; QC FAIL (energy) | design rule plus QC filter |
| T0191_sst, T0882_lam | Same design rule (QC OK, excluded by the rule) | design rule `yi > H - off` for discharge, fixed 2026-11-04 before final training (`freeze_manifest.py`) |

Design points removed entirely: T0073 (its only run), T0191, T0765, T0882. That gives 1,024 − 4 =
1,020 design points.

## Quality control

- **QC verdicts** in the manifest: 1,211 OK, 1 WARN.
- **The WARN run: T0393_lam**, velocity growth 2.064 against a limit of 2.0. It is kept and is in the
  ood_mode test set. Stage 1A (iteration, time-step and perturbation reruns) checks whether its
  behaviour is numerical; result pending.
- **Energy conservation:** median error 7.4e-5 of exchanged energy (audit, 2026-11-06).
- **File integrity:** all 1,212 h5 files pass the integrity scan and match the manifest md5 sums.
- **Reproducibility:** a production rerun of T0408 (laminar and SST) with today's code reproduced
  the archived runs exactly. More runs follow from stage 1A.

## Splits (by design point, so twins never straddle a split; `thermbench_ml/splits.py`)

| Split | Test set | What it tests |
|---|---|---|
| random | 10 % of design points by hash | interpolation |
| ood_flow | Re_in > 9,007 (design 90th percentile) | higher inflow. **All ood_flow test runs are SST** (Re > 3,000), so this tests Reynolds-number extrapolation and the turbulence model together |
| ood_geom | W outside 0.33 to 0.93 m | **width / aspect-ratio extrapolation within the same rectangular 2D geometry**, not new geometry families. The docstring in `splits.py` says "unseen tank shapes"; the paper should use the narrower wording |
| ood_mode | all discharge runs (train on charging) | unseen operation mode |

## Verification status (see `verification_criteria_2026-11-06.md`, `response_mesh_verification_2026-11-06.md`)

- **Mesh, 2.5 vs 5 mm.** T0408 (both closures) is within all pre-registered limits: field 0.34 % of
  ΔT, energy 0.17 %, outlet 1.43 % of ΔT, thermocline midpoint 0.5 mm. Around the outlet event the
  outlet error is 2.03 % of ΔT. T0243_sst, T0221_lam and T0551_lam are running.
- **Outer iterations (2 vs 4) and Courant limit (0.5 vs 0.25).** Negligible for T0408; 6 more designs
  running.
- **Experiment (3D, Lou et al. 2023).** Bias +2.4 mm, RMS 7.2 mm.

## Known limitations (to state in the release)

- One uniform mesh (5 mm) and one numerical setup. Inter-grid discrepancies are reported for the
  verification cases; dataset-wide mesh convergence is not claimed.
- 2D: no 3D effects; experimental validation is indirect, through the 3D Lou et al. case.
- The SST runs model turbulence with RANS. Across the 192 design points run with both models, the
  laminar and SST solutions differ by a median 3.9 % of ΔT in field RMSE (10th to 90th percentile
  0.7 to 8.3 %, maximum 17.8 %). Only 14 differ by less than 0.5 %, mostly strongly stratified
  cases (median Ri 324 against 66 overall; Spearman correlation of the difference with Ri −0.62).
  Integral quantities differ less: stored energy median 0.6 %, outlet temperature median 2.4 % of
  ΔT, thermocline midpoint median 3.4 mm (`verification_data/lam_sst_yplus.json`).
- Wall resolution of the SST runs (first-cell y+ from Spalding's law, all 588 runs, all wall cells
  and snapshots): 60 % of wall cell-snapshots have y+ < 5, 38.5 % lie in the buffer layer
  (5 to 30) and 1.6 % above 30. The largest y+ per run has a median of 35, reaching 113 at the
  highest Re. The buffer-layer share is where wall treatment is least accurate. The 2.5 mm mesh
  check of the high-Re SST case T0243 halves y+ and so tests this directly.

## Still missing for the release

LICENSE, environment specification (OpenFOAM and Python versions, pip freeze), README with loading
example, version tag and DOI, manifest and its md5 in the repository.
