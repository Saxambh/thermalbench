# Reply: tank numerical verification and what the tank ML model can do (7 November 2026)

This reply covers only completed and tested work. Work in progress is listed under "Remaining".

## 1. Tank numerical verification

### Method

- **Designs.** Six dataset designs: T0408, T0221, T0551 and T0393 (laminar), and T0243 and T0211 (k-omega
  SST).
- **Reference.** Each was rerun at production settings (5 mm mesh, nOuterCorrectors 2, maxCo 0.5). In all
  six designs the rerun reproduces the dataset run exactly (difference 0.00).
- **Variations.** We then changed one thing at a time:

  | Run | Change |
  |---|---|
  | n4 | nOuterCorrectors 4 |
  | co25 | maxCo 0.25 |
  | 2.5 mm | finer mesh (four designs) |
  | rep | inlet velocity × 1.0001, a measure of the flow's own sensitivity |

- **Limits.** All limits were committed before any result was compared, as was the rule that a time window
  above its limit makes a result borderline (event window).

### Mesh, 2.5 vs 5 mm

Sent separately, summarised here:
- **Integral quantities** (stored energy, horizontally averaged profile, outlet temperature, thermocline
  height) agree on all four designs; stored energy is borderline for T0243 (0.96 %).
- **Full field.** It differs by 0.34 to 2.76 % of ΔT; T0243 (1.70 %) and T0551 (2.76 %) are borderline.
- **No GCI.** The three levels do not converge monotonically, so no GCI is reported, and the mesh is not
  described as converged.

### Outer iterations and time step (field RMSE, % of ΔT, against the production rerun)

| Design | rep | n4 | co25 | Verdict |
|---|---|---|---|---|
| T0408 lam | ~0 | ~0 | ~0 | agreement |
| T0221 lam | 0.39 | 0.39 | 0.38 | agreement |
| T0243 SST | ≤ 0.11 | ≤ 0.11 | ≤ 0.11 | agreement |
| T0393 lam | 0.50 | 0.67 | 0.78 | field agreement; outlet borderline (event window) |
| T0551 lam | 1.85 | 2.14 | 1.96 | field borderline |
| **T0211 SST** | **0.47** | **7.38** | **7.32** | **field clear disagreement** |

- **T0393.** The outlet temperature is borderline in every variant, rep included (2.87, 3.40 and 2.85 %;
  4.4 to 5.2 % in the window after breakthrough). The outlet passes through backflow events there. Since
  the 0.01 % inlet change produces the same effect, we report it as sensitivity of the solution, not as a
  numerical error.
- **T0551.** The n4 and co25 differences are about the size of the rep difference (1.85 %), so they cannot
  be distinguished from the sensitivity of the unsteady flow. All other quantities agree.
- **T0211 (Re 5,396, Ri 3.9, discharge) is a genuine numerical error of the production settings.**
  - n4 and co25 agree with each other (2.49 %) but both differ from production by 7.4 %, while rep differs
    by 0.47 %.
  - The error is a phase error in the tilting and sloshing of the thermocline interface after the cold jet
    reaches it.
  - Other quantities: profile 1.9 % and time-averaged field 1.0 % (borderline); stored energy 0.26 to
    0.43 % and thermocline height 5 mm (agreement); outlet 2.0 to 2.4 % overall, but 5.1 % in the window
    around breakthrough.
  - The pressure residual of the production run does not single this design out (T0551 has a higher one),
    so the logs cannot be used to screen the dataset for similar cases.

## 2. What the tank ML model can do

- **Model.** The main model, FNO hybrid in the canonical frame, as the mean of three seeds.
- **Test sets.** Every test run of the four fixed design-level splits: random 131, ood_geom 224, ood_mode
  363, ood_flow 103. The test sets were fixed before training; laminar and SST runs of one design point are
  never split across train and test.

### Accuracy

| Split | Field RMSE, median (mean), % ΔT | Stored energy, median | Outlet T, median | Best interpolation baseline (mean) | 1D ideal stratification (mean) |
|---|---|---|---|---|---|
| random | 3.3 (4.1) | 0.24 % | 0.54 K | 8.7 | 15.3 |
| ood_geom (unseen widths) | 3.5 (4.4) | 0.23 % | 0.63 K | 10.8 | 16.0 |
| ood_mode (discharge never trained) | 3.7 (4.5) | 0.28 % | 0.61 K | 64 (fails) | 16.5 |
| ood_flow (faster inflow) | 8.7 (9.5) | 0.70 % | 1.38 K | 15.1 | 22.8 |

- **Against the baselines.** The model halves the error of the best interpolation baseline and reduces that
  of a 1D ideal-stratification model about four times.
- **Transfer.** It carries over to tank widths outside the training range and to an operating mode never
  seen in training, where interpolation fails.
- **Speed.** A complete transient (120 snapshots) takes about 1.5 s on a laptop GPU, against a median 2.6 h
  of single-core CFD (10 to 90 %: 0.6 to 8.4 h). That is about 6,000 times faster in wall-clock time; the
  hardware differs, so we do not present it as an equal-cost comparison.

### Where it is weaker, and whether it knows

- **Error grows as the jet overcomes the stratification.** Spearman ρ with Ri is −0.75 to −0.80, and SST
  runs have about twice the error of laminar runs.
  - Every test run above 10 % error is an SST case with Ri below about 8.
  - For Ri ≥ 5 (88 % of the dataset) the median error is about 3 % on all splits except ood_flow.
- **What goes wrong in those cases.** The model smooths the large coherent vortices and wall short-circuits
  that govern mixing, and misplaces the outlet breakthrough.
- **The three-seed spread is a reliable warning.**
  - It ranks run-level error with Spearman ρ = 0.82 to 0.94 on all four test sets.
  - The 10 % most uncertain runs contain 68 of the 81 worst-10 % runs (84 %).
  - Every run above 10 % error lies in the more-uncertain half.
  - Within a run, the 10 % of cells with the largest spread hold about three quarters of the squared error.
- **But the spread is not yet an error bar.** It is about 0.38 times the actual error, so it ranks well but
  is under-dispersed. A scale factor will be fitted on validation runs, not test runs, before it is offered
  as one.

### Limits we state with this

- The weakest ML regime (fast turbulent jets, low Ri) overlaps the regime of the T0211 numerical error, so
  part of the measured ML error there may be label error.
- These results are for the main model only. U-Net and the ablations, design-level confidence intervals and
  the untouched confirmation set are not yet included.
- Horizontal stitching lines are visible in some predicted fields in the hardest cases. They are under
  investigation and are not yet explained.

## Remaining

- Tank:
  - whether the T0211 error extends to neighbouring SST designs (test pre-registered and running);
  - the consolidated verification verdict.
- ML:
  - the other architectures and ablations;
  - design-level confidence intervals;
  - spread calibration on validation runs;
  - the stitching lines;
  - then the confirmation set, after the models are frozen.
- PCM:
  - completion of the WARN reruns (the pre-registered test triggered reruns of one warning kind);
  - validation case 2;
  - the final inventory and manifest.
