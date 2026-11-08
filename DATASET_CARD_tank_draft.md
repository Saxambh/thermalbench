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
  - stored energy (real properties), exergy, MIX number, stratification number, thermocline midpoint
    and thickness, mean T and area-averaged outlet T per snapshot;
  - dense time series of the area-averaged outlet T, mean T, and outlet mass and enthalpy flow (from
    which the flow-weighted outlet temperature follows);
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

Completed 2026-11-07. Limits were committed before results; `reply_tank_mesh_2026-11-07.md` and
`reply_tank_ml_verification_2026-11-07.md` give the full tables.

- **Mesh, 2.5 vs 5 mm (T0408, T0221, T0551, T0243).** Integral quantities (stored energy, horizontal
  profile, outlet temperature, thermocline height) agree on all four; stored energy borderline for T0243
  (0.96 %). Full field differs by 0.34 to 2.76 % of ΔT (T0243 1.70 % and T0551 2.76 % borderline). The
  three levels do not converge monotonically, so no GCI is given and the mesh is not called converged.
- **Outer iterations (2 vs 4), Courant limit (0.5 vs 0.25) and inlet × 1.0001.** Agreement for T0408,
  T0221 and T0243; T0393 outlet and T0551 field borderline, both at the size of the flow's own
  sensitivity. T0211_sst differs by 7.4 % of ΔT: numerical-setting dependence of the production
  solution. n4 and co25 still differ from each other by 2.49 %, so neither setting is shown to be converged.
- **Regime test.** Of 10 further wide, low-Ri SST designs, none shows the T0211 error (all ≤ 0.05 %;
  0 of 10, 95 % interval 0 to 31 %). Including four earlier neighbours, 2 of 15 wide low-Ri SST designs
  show it: T0211_sst and T0052_sst (the latter under a rule added after its result).
- **Experiment (3D, Lou et al. 2023).** Bias +2.4 mm, RMS 7.2 mm.

**Flagged labels.** T0211_sst and T0052_sst stay in the dataset and are listed in
`thermbench_ml/label_flags_tank.json` (n4 vs production 7.4 and 6.8 % of ΔT) so users can exclude or
down-weight them. The flag file is separate from the frozen manifest, whose md5 is unchanged. Production
residuals do not single these runs out, so similar runs elsewhere cannot be identified from the logs; the
regime test bounds how common they are.

## Known limitations (to state in the release)

- One uniform mesh (5 mm) and one numerical setup. Inter-grid discrepancies are reported for the
  verification cases; dataset-wide mesh convergence is not claimed.
- Label uncertainty in the fast-jet regime (SST, Ri below about 5): two known runs differ by about 7 % of
  ΔT with tighter numerical settings (flagged above). Scoring the same frozen predictions against the
  alternative solutions moved the ML field error on these runs by at most 0.43 pp of ΔT and kept the model
  ordering (`thermbench_ml/altref_2026-11-07/RESULT.md`).
- **Metric definitions.**
  - The benchmark's energy metric is mean θ (constant ρcp); it matches the real-property energy error
    within ±1 %.
  - The outlet metric is the **area-averaged** outlet temperature, not the flow-weighted (mixing-cup)
    temperature a system model receives. The two differ by a median 0.6 % of ΔT, 2.3 % around breakthrough,
    and up to about 30 % in very-high-Ri laminar runs, where the thermocline crosses the outlet slot. The h5
    files keep the outlet mass and enthalpy flow series for computing the mixing-cup temperature
    (`thermbench_ml/proxy_check_2026-11-07/RESULT.md`).
  - The thermocline midpoint is undefined (no θ = 0.5 crossing) in a median 2.5 % of snapshots; these are
    excluded from the midpoint error and reported as `y_mid_missing`.
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
