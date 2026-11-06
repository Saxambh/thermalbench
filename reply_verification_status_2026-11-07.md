# Reply: verification and validation status (7 November 2026)

Thank you for the three notes. This reply lists only work that is complete, with its results, then what
remains. Each point is mapped to your recommendations.

## 1. Acceptance criteria fixed in advance

**You asked** for acceptance criteria defined before interpreting results, tied to the quantities the ML
models predict, and not adjusted afterwards.

**Done.** Before any comparison was run, we set and version-controlled limits for each quantity
separately. "Agree" and "clear disagreement" mean the result is at or below the first limit, or above the
second.

| Quantity | Agree | Clear disagreement |
|---|---|---|
| Field RMSE | ≤ 1.5 % of ΔT | > 3 % |
| Time-averaged field | ≤ 1.0 % | > 2 % |
| Horizontally averaged profile | ≤ 1.5 % | > 3 % |
| Stored energy | ≤ 0.5 % | > 2 % |
| Outlet temperature | ≤ 2 % of ΔT | > 5 % |
| Thermocline midpoint | ≤ 10 mm | > 25 mm |

The field limit is under half our best random-split ML error (3.4 % of ΔT).

Additional diagnostics added later at your request carry no pass limits and are recorded as such:
- thermocline thickness, MIX, stratification number, outlet backflow and solver indicators;
- error-field maps;
- PCM melt-front position.

## 2. Tank: completed verification case (T0408, laminar and SST)

**You asked** for:
- iteration and time-step sensitivity under production settings;
- a mesh comparison under the current setup;
- separating perturbation sensitivity from repeatability;
- time-resolved comparisons covering the outlet event;
- treating coarse grids as diagnostic.

**The case.** Discharge from a pre-stratified start, lid/bottom slots of 40 mm, tank width 0.28 m, Re
2,014, ΔT 18.3 K, 54 s.

**Mapping.** Finer fields are block-averaged onto the coarser grid by the exact integer ratio and
compared at matched physical times.

| Comparison | Field RMSE, % ΔT | Profile | Stored energy | Outlet T, % ΔT | Thermocline midpoint | Thickness |
|---|---|---|---|---|---|---|
| Rerun at production settings vs archived run | 0.00 | 0.00 | 0.00 % | 0.00 | 0.0 mm | |
| Inlet velocity × 1.0001 | 0.00 | 0.00 | 0.01 % | 0.01 | 0.0 mm | |
| 4 vs 2 outer iterations | 0.00 | 0.00 | 0.00 % | 0.05 | 0.0 mm | 0.0 mm |
| maxCo 0.25 vs 0.5 | 0.01 | 0.00 | 0.00 % | 0.18 | 0.0 mm | 0.0 mm |
| **2.5 mm vs 5 mm** | **0.34** | 0.27 | 0.17 % | **1.43** | 0.5 mm | 0.2 mm |
| 10 mm vs 5 mm (diagnostic) | 0.37 | 0.28 | 0.62 % | 1.60 | 0.9 mm | 2.2 mm |

**Results**
- **Reproducibility.** The archived run is reproduced exactly by the current code. Serial runs are
  deterministic, so a same-input repeat measures nothing. The 0.01 % inlet perturbation also produced no
  measurable change, and we report it as physical-perturbation sensitivity, not as a noise floor.
- **Iterations and time step.** No effect on the solution. Four outer iterations halve the mean pressure
  residual (0.0012 to 0.0006) without changing the result. The time step and Courant number behave as
  expected.
- **Mesh.**
  - The 2.5 mm difference is spatial: it is unchanged when the 5 mm reference also uses maxCo 0.25.
  - All pre-registered quantities are within their limits for the whole run.
  - **By time window, the outlet temperature reaches 2.03 % of ΔT around the outlet event** (15 to 25 s),
    just over the 2 % limit. Before the event it is 0.24 %, after it 1.45 %. We record this as a
    **borderline event-window result**, not a pass. The whole-run value (1.43 %) is reported alongside
    it.
  - The finer mesh gives a slightly sharper, later breakthrough (peak 0.6 K on an 18 K swing). The 10 mm
    mesh errs in the opposite direction. The convergence direction is consistent, but the magnitudes do
    not shrink fast enough for a formal order or GCI, so none is reported.
- **Other diagnostics.** No outlet backflow on any grid. MIX differs by 0.004 against a range of 0.09
  over the run.
- **Closures.** In this case the laminar and SST solutions agree to 0.04 % of ΔT, so this pair does not
  test two closures.

**Limitation.** One mild, short, transitional design. It supports a case-specific claim only.

## 3. Tank: dataset-wide checks completed

**Laminar versus SST, all 192 design points run with both closures.**
- Field difference: median 3.9 % of ΔT, 10th to 90th percentile 0.7 to 8.3 %, maximum 17.8 %.
- Integral quantities: stored energy median 0.6 %, outlet temperature 2.4 % of ΔT, thermocline midpoint
  3.4 mm.
- The difference is governed by stratification, not Reynolds number: Spearman correlation with the
  Richardson number −0.62, with Re +0.12.
- The 14 near-identical pairs are strongly stratified (median Ri 324 against 66 overall). T0408 is one of
  them.
- The paired subset therefore tests genuinely different closures in most designs.

**Near-wall resolution, all 588 SST runs.** First-cell y+ from Spalding's law, over all wall cells and
snapshots:
- 60 % of wall cell-snapshots below 5, 38.5 % in the buffer layer (5 to 30), 1.6 % above 30;
- the per-run maximum has a median of 35, up to 113 at the highest Re;
- the buffer-layer share is stated as a limitation of the high-Re SST runs.

**ML scoring of undefined quantities.**
- The thermocline height is recomputed from predicted and true fields. Its error is averaged only where
  both define it, and definition mismatches are reported separately.
- Thickness and MIX, which can be undefined, are not used in training or scoring.

**Dataset description.**
- 1,212 runs of 1,020 design points: 432 laminar-only, 396 SST-only, 192 with both.
- Five planned runs excluded, with reasons documented:
  - T0073_lam: energy QC failure;
  - T0765_lam/_sst: energy QC failure and the design rule below;
  - T0191_sst and T0882_lam: design rule (discharge with the hot layer entirely above the outlet), fixed
    before final training.
- QC: 1,211 OK, 1 WARN (T0393_lam).
- Wording corrected:
  - ood_flow tests Reynolds-number extrapolation and the SST closure together (all of its test runs are
    SST);
  - ood_geom tests width and aspect-ratio extrapolation within the same rectangular 2D geometry.

**Disclosure.**
- Our verification inputs were first taken from a design list that differs from the one the dataset was
  built from (port offsets and widths on a 5 mm rather than 10 mm grid). This affects three pilot runs
  (T0243, T0393, T0211); their first verification sets are being repeated with the correct inputs.
- The T0408 results above are unaffected: its two design lists are identical.

## 4. PCM

**You asked** to:
- check both pressure-solver entries;
- compare corrected and original runs on solver behaviour and physical outputs;
- categorise WARN cases;
- check the validation parameters;
- consider thin fins.

**Pressure solver.**
- The rerun script now sets PCG + DIC for both p_rgh and p_rghFinal and verifies both before running.
- None of the completed reruns reached its 2,000-iteration limit (mean initial residual 0.007 to 0.026).

**Corrected reruns versus originals (4 of the failed cases complete).**

| Case | Melt time change | Melt curve, max diff | Field RMSE (% ΔT) | Melt-front shift, mean / p95 |
|---|---|---|---|---|
| P0181 (5 fins of 1.0 mm) | +0.9 % | 0.010 | 3.3 | 0.5 / 1.5 mm |
| P0371 (5 fins of 1.5 mm) | −0.9 % | 0.032 | 8.0 | 1.5 / 2.9 mm |
| P0228 (2 fins of 1.5 mm) | −0.9 % | 0.006 | 1.9 | 0.7 / 2.7 mm |
| P0273 (5 fins of 1.0 mm, 45°) | −2.1 % | 0.028 | 6.2 | 1.3 / 2.5 mm |

- Melt time and melt curve barely change.
- Local fields change because the melt front shifts by about a millimetre: 55 to 72 % of the squared
  temperature error lies in the front band, which covers 8 to 15 % of the cavity.
- The failed originals are replaced by their reruns.
- In a further case (P0124), a run with 8 % of final pressure solves at the iteration cap gave a melt curve
  identical to the fully corrected run (largest difference 0.0009).

**Mesh, 0.25 vs 0.5 mm, six dataset cases.**
- Melt time is 1.0 to 8.7 % later on the finer mesh (median 4.9 %), the same sign in all six.
- Melt curves within 0.036. Field RMSE 4.2 to 7.6 % of ΔT.
- The melt front shifts by 0.3 to 0.8 mm on average. 36 to 76 % of the squared error lies in the front
  band, which covers 5 to 16 % of the area.
- The bias is not specific to thin fins: it is largest in an unfinned case and a 3.5 mm-fin case.
- We report this as an inter-grid discrepancy relative to the 0.5 mm numerical reference, not as a
  converged uncertainty.

**WARN cases.** Of the 46 WARN cases at the first scan, 27 are flagged only for capped iterations, 11 for
capped iterations with a high residual, and 8 for a high residual only. Given the P0124 result, a WARN
alone is not treated as a reason to rerun.

**Problems found and corrected while checking.**
- **41 resumed cases.** Their postProcessing series were split across restart folders, and the exporter
  read only the part before the first restart. This left them with no melt time and spurious
  energy-balance errors of 1 to 99 %.
  - The fields were complete and correct: every melt curve rises monotonically to 0.995.
  - The series were merged and the summary metrics recomputed; backups were kept.
  - Energy-balance errors are now 0.01 to 0.5 %.
- **QC rerun on all machines.** 514 checks: 495 OK, 16 WARN, 3 FAIL. Of the failures:
  - two are originals already replaced by corrected reruns;
  - one, P0495, was physically corrupted after a resume (temperatures above the wall temperature), and is
    being rerun from t = 0.

**Validation parameters.**
- **Octadecane (Vogel 2019).** Validated with the dataset's mushy-zone constant (1e6): mean deviation 0.009
  in liquid fraction, within the ±0.02 digitising accuracy.
- **Lauric acid (Kamkari 2014),** at the frozen dataset settings (5e6):
  - plain wall within ±0.05 at all times, with the same full-melt time;
  - finned walls about 0.1 too fast in the first hour, converging later; 3-fin full melt 8 % early.
- A later rerun with the final solver fix used 1e6 instead. It showed that the fix moves the melt curve by
  less than 0.005, and 1e6 against 5e6 by about 0.01.

## 5. Experimental validation, tank

- Lou et al. 2023 (3D, charging, Re 1,368 to 6,831), same solver, water properties and turbulence
  treatment as the 2D dataset.
- Jet penetration against PIV: bias +2.4 mm, RMS 7.2 mm. Lou et al.'s own CFD had a bias of −29.7 mm.
- Refining the lower-baffle region changed the jet penetration by at most 0.1 mm.
- The 2D validation is indirect, and we state this.

## 6. What remains

**Tank verification**
- Iteration, time-step and mesh comparisons for the remaining pilot designs, under the same
  pre-registered limits and time windows:
  - T0243 (high-Re SST jet);
  - T0221 and T0551 (long laminar runs; outlet events at 36 % and 79 % of the run);
  - T0211 and T0393, including the latter's backflow.
- A decision on wider coverage (a wide tank, additional high-Re SST cases) once these are evaluated.

**PCM**
- A three-level comparison (1.0, 0.5 and 0.25 mm) to establish whether an observed order or GCI is
  justified.
- Kamkari validation at exactly the dataset settings, and a finer-mesh run of the 3-fin case, to separate
  mesh error from model error in the early fin deviation.
- Replacement of the five remaining failed cases and P0495 by their reruns; final QC and freeze.
- A thin-fin (1.0 mm) sensitivity case and an intermediate mesh level. The 0.354 mm level you suggested
  cannot be built with our grid-aligned geometry; 0.333 mm can.

**Tank validation**
- Whether the laminar regime and the outlet temperature can be compared with Lou et al.'s data. A second
  tank experiment with discharge (Shah and Furbo 2003) is an option if needed.

**ML benchmark**
- Final results with statistics by independent design point, recorded inference times, a decision on
  matched training budgets, and an untouched confirmation set after the models are frozen.

**Release**
- Licence, environment specification, README with scoring instructions, version tag and DOI.
