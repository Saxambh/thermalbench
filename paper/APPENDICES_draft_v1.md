# Appendix A. Verification

## A.1 Pre-registered limits (tank)

The limits below were committed (`verification_criteria_2026-11-06.md`) before any comparison existed. A value between the two columns is borderline and is never reported as agreement; a quantity that passes over the whole run but exceeds its limit in any event window (before, around or after the outlet event) is borderline. The perturbation run (inlet velocity × 1.0001) measures the physical sensitivity of the unsteady solution and is never treated as a numerical noise floor. An observed order or grid convergence index (GCI) is reported only if three levels converge monotonically with an observed order between 0.5 and 3.

**Table A.1. Pre-registered agreement limits, test against production solution.**

| Quantity | Agreement | Clear disagreement |
|---|---|---|
| Field RMSE, all snapshots | ≤ 1.5 % of ΔT | > 3 % |
| Time-averaged field | ≤ 1.0 % | > 2 % |
| Horizontally averaged profile | ≤ 1.5 % | > 3 % |
| Stored energy | ≤ 0.5 % | > 2 % |
| Outlet temperature | ≤ 2 % of ΔT | > 5 % |
| Thermocline midpoint | ≤ 10 mm | > 25 mm |

The limits are engineering tolerances scaled to the size of the machine-learning errors the labels are used to judge. They do not guarantee that a ranking cannot change: a reference change of size d can move a two-model gap by up to 2d (Appendix C tests this directly).

## A.2 Tank mesh, iterations and time step

**Table A.2. Tank mesh (2.5 against 5 mm) and setting tests, field RMSE in % of ΔT against the production run.** rep: inlet × 1.0001; n4: four outer correctors; co25: maximum Courant number 0.25.

| Design | Re, Ri | Mesh 2.5 mm | rep | n4 | co25 |
|---|---|---|---|---|---|
| T0408, laminar | 2,014, 31 | 0.34 | ~0 | ~0 | ~0 |
| T0221, laminar | 678, 386 | 0.60 | 0.39 | 0.39 | 0.38 |
| T0243, SST | 18,626, 5.8 | 1.70 | ≤ 0.11 | ≤ 0.11 | ≤ 0.11 |
| T0551, laminar | 1,259, 55 | 2.76 | 1.85 | 2.14 | 1.96 |
| T0393, laminar | | | 0.50 | 0.67 | 0.78 |
| T0211, SST, discharge | 5,396, 3.9 | | 0.47 | 7.38 | 7.32 |

Integral quantities agree within their limits except one borderline energy difference (T0243, 0.96 %). In T0551 the mesh difference (2.76 %) is of the same order as the response to the 0.01 % inlet perturbation (1.85 %), so the two cannot be separated in that design. In T0243 the mesh difference lies on the thermocline interface and grows with time. A 10 mm grid does not converge monotonically with the other two levels, so no order or GCI is reported, and the 5 mm mesh is not called converged.

T0211 shows a numerical-setting dependence: n4 and co25 differ from the production run by 7.4 % but from each other by 2.49 %, so neither is shown to be converged, while the perturbation moves it by only 0.47 %. The difference is a phase error in the tilting of the thermocline after the cold jet reaches it. Two pre-registered tests asked whether this is a regime. The four nearest SST designs in (log Re, log Ri) gave no affected design under the first rule; T0052 missed it narrowly and is counted as affected under a ratio rule added afterwards (labelled post hoc). A second sample of ten wide, low-Ri SST designs, drawn by a fixed rule before any run, gave 0 of 10 affected (95 % interval 0 to 31 %), with all differences at most 0.05 % of ΔT. T0211 and T0052 are flagged (Appendix C); T0156, T0551 and T0393 are listed as sensitive.

Across the 192 design points run with both closures, laminar and SST fields differ by a median 3.9 % of ΔT (10th to 90th percentile 0.7 to 8.3 %), governed by stratification (Spearman correlation with Ri −0.62) rather than Reynolds number (+0.12). In the 588 SST runs, 60 % of wall cell-snapshots have y⁺ below 5, 38.5 % lie in the buffer layer and 1.6 % above 30.

## A.3 PCM mesh, time step and solver

In six dataset cases compared at 0.5 and 0.25 mm, the time to 99 % melting (t99) is 1.0 to 8.7 % later on the finer mesh (median 4.9 %), always in the same direction. Melt curves agree within 0.036 in liquid fraction; the field differs by 4.2 to 7.6 % of ΔT, mostly in a band around the melt front. For case G131 (lauric acid, no fins; 1.0, 0.5 and 0.25 mm), the dense liquid-fraction series gives an observed order of 0.741 and a GCI of 13.06 % on the 0.5 mm and 7.50 % on the 0.25 mm grid; the 0.5 mm run melts about 9.5 % before the extrapolated t99. The time step is Courant-limited and halves with the mesh, so this is a combined space-time refinement. Case G301 (n-octadecane) has an observed order outside 0.5 to 3, so no GCI is given; its 0.5 mm run melts 6.76 % earlier than the 0.25 mm run.

The pressure solve failed to converge in some cases (the first was P0124). A solver-convergence check was added; 34 failed cases were rerun with a preconditioned conjugate-gradient solver, which changed the melt time by −2.1 to +0.9 % in the four cases compared. A pre-registered test reran the two most severe warning cases of each kind; one kind changed materially (P0075, 2.54 % of ΔT), so all 17 cases of that kind were rerun, and the 39 cases of the other two kinds were kept (sensitivity in Appendix C).

# Appendix B. Lou et al. tank details

**Case.** The three-dimensional run uses quarter symmetry (230,156 cells), buoyantPimpleFoam with k-ω SST and the corrected buoyancy source, real water properties and a maximum Courant number of 2, with baffle-hole open areas within 1 % of the target. It ran to 750 s for the jet comparison and was extended to 1,275 s (t* = 1.507) for the outlet. h_j is taken as the distance from the inlet port to the point on the centreline where the vertical velocity changes sign, averaged over ±6.25 s as in the PIV.

**Jet depth.** Against the mean of the two PIV tests over 14 times, the difference is −2.9 mm (50 to 300 s), −0.9 mm (350 to 450 s) and +10.8 mm (500 to 700 s). After 500 s the simulated jet is deeper than both tests separately, and it penetrates about 19 % faster than the PIV (0.180 against 0.151 mm/s, linear fits). The spread between the two PIV tests indicates repeatability and is not an uncertainty band. Refining the lower baffle region changed h_j by at most 0.1 mm up to 300 s.

**Outlet reconstruction.** The experimental outlet curve (Fig. 15a of [17], uniform baffle, 1 L/min, 333.15 K into 293.15 K) was digitised by curve colour from the publisher's image (about ±0.01). Because Ri_bulk is proportional to β(T)(T_in − T_out), it was converted back to T*_out in two ways: with constant β, T*_out = 1 − Ri/Ri_0 with Ri_0 the plateau before breakthrough; and with β evaluated at the mean of inlet and outlet temperature, solving for T_out. The second reconstruction crosses T* = 0.1 at about t* = 0.77 (interpolated across a gap in the digitised curve between t* = 0.768 and 0.788). Evaluating β at the outlet temperature gives two roots near the plateau and was not used.

**Charging efficiency.** The simulated σ(t*) is the integral of (1 − T*_out) over t*, the port energy balance at constant ρc_p. The published σ rises with a slope of 0.81 on the pre-breakthrough plateau, where a loss-free and perfectly measured tank gives 1.0, and stays below the simulation (0.750 against 0.919 at t* = 1.0; 0.850 against 0.985 at t* = 1.5). This supports a heat-loss explanation in sign, without separating wall loss, mixing and measurement.

# Appendix C. Label flags, alternative references and solver warnings

**Flags.** T0211_sst and T0052_sst carry a numerical-setting uncertainty of 7.4 and 6.8 % of ΔT (Appendix A.2) and are flagged in `label_flags_tank.json`; both are test runs (discharge and unseen width).

**Alternative references.** All held-out tank runs with an alternative CFD solution (18 runs, 23 run-split rows; nothing selected) were scored against each alternative with the same frozen predictions of the two hybrid canonical models. Across the four references (2.5 mm mesh, n4, co25, perturbation), the ensemble field error changes by at most 0.54 percentage points in any row and by at most 0.43 percentage points for the flagged runs; the mean FNO minus U-Net gap changes by at most 0.04 percentage points. One of 64 ensemble comparisons flips the ranking (T0221_lam against the 2.5 mm reference, where the two models differ by 0.11). Similar scalar errors against two CFD references cannot show how much error the two references share with the true solution.

**PCM solver warnings.** The 39 retained warning cases fall into the test sets as random 3, held-out fins 15, stronger heating 4, held-out lauric acid 24, held-out n-octadecane 15 and unseen tilt 11. Removing them from scoring changes neural field RMSE by at most 0.10 K and baseline RMSE by at most 0.60 K. The ordering of the neural models is unchanged on every split and metric, and every neural-against-baseline conclusion is unchanged. This tests exclusion from scoring, not retraining without these cases.

# Appendix D. Models and training

**Architectures.** FNO: four Fourier layers, width 32, 16 retained modes in each direction, with pointwise skips (about 2.1 M parameters for the tank). U-Net: four levels, base width 32 (about 7.8 M). Transolver (PCM only): six layers of physics attention, width 128, 8 heads, 32 slices, on 4 × 4-cell patch tokens embedded by a patch convolution and decoded to their 16 cells (1.16 M). Inputs are the design parameters broadcast as channels, the time, two normalised coordinates and, for hybrid models, the physics-base field.

**Training.** AdamW (weight decay 10⁻⁴) with a one-cycle schedule, peak learning rate 10⁻³ (3 × 10⁻⁴ for Transolver, chosen on validation loss only between 10⁻³ and 3 × 10⁻⁴: 0.0456 against 0.0473), batch 16, bfloat16 autocast, 60 epochs for FNO and Transolver and 100 for U-Net (U-Net was still improving between 60 and 100 epochs in a test pass). The checkpoint with the best validation loss is scored once on the test set. Each model is trained with seeds 0, 1 and 2. Tank test scores use every 10th snapshot, PCM every 5th.

**Hybrid and canonical models.** A hybrid model predicts the correction to a physics base: the ideal-stratification field for the tank (plug flow with a sharp interface placed by the energy balance) and the conduction-then-convection front model for PCM. The canonical frame maps a discharge run to the charge frame by a 180° rotation and θ → 1 − θ, on input and back before scoring; the transform is its own inverse to 3 × 10⁻⁸.

**Transolver.** The plan, the analysis and the expectations were committed before training. Tokens of single cells cost 15 times FNO per step and fitted eight training samples no better, so 4 × 4 patches were used (amendment committed before any validation or test use). The tank was to be run only if the patch model fitted eight tank training samples to a masked RMSE of 0.01 within 1,600 steps; the best variant, with convolutional slice projections, reached 0.012, so the tank was not run. This is an implementation and resource decision; an eight-sample fit does not show how Transolver would generalise on tank data.

# Appendix E. Statistics

All intervals are descriptive 95 % percentile bootstrap intervals (10,000 resamples). Neural scores are the per-run mean of three seeds.

**Tank, design level.** Runs are averaged per design, and designs are resampled. On the random split, hybrid canonical U-Net is better than hybrid canonical FNO by 0.41 percentage points [0.34, 0.48]; on unseen widths FNO is better (Fig. 3). Full tables: `thermbench_ml/stats_2026-11-07/design_ci.md`.

**Discharge confirmation (pre-registered).** The protocol was committed before any subset score was computed. On the 259 discharge test runs from 215 designs with no identified exposure before the models were frozen, adding the canonical frame to the hybrid model improves field error by 9.17 percentage points [8.33, 10.02] (FNO; 96 % of designs) and 9.74 [8.84, 10.64] (U-Net; 95 %), and the hybrid canonical models beat ideal stratification by 12.53 and 12.61 percentage points. All four hypotheses are supported (Holm-adjusted p = 0.0004 each, the floor of the null-centred bootstrap). The subset was part of the ood_mode aggregate already reported, so this is a pre-registered subset analysis, not a prospective confirmation.

**PCM, run level.** Each PCM run is its own case, so runs are resampled with the seed means fixed. The interval therefore describes variation over cases for the fitted models, not over retraining; on the material splits the seed spread is reported separately (Fig. 4). The "best baseline" of a split is chosen on the test set, so headline comparisons use IDW by name. For t90, a paired comparison uses only runs where both models reach t90 in every seed; for example, the FNO hybrid t90 comparison with IDW on held-out n-octadecane uses 100 of 250 runs and cannot establish better melt-time performance over the whole split.

# Appendix F. Uncertainty from the seed spread

For the hybrid canonical FNO ensemble, the cell-wise spread of the three seeds ranks the error well: Spearman correlation between spread and error 0.86 (random), 0.86 (unseen width), 0.82 (discharge) and 0.94 (faster inflow). A bound error ≤ k × spread was calibrated on each split's validation runs and checked on its test runs.

**Table F.1. Calibrated error bound, coverage on test runs.**

| Split | k for 90 % | Coverage, 90 % / 95 % | Constant bound, 90 % / 95 % |
|---|---|---|---|
| Random | 4.0 | 91 / 96 % | 87 / 92 % |
| Unseen width | 3.5 | 88 / 93 % | 84 / 89 % |
| Faster inflow | 3.7 | 90 / 94 % | 19 / 37 % |
| Discharge | 3.2 | 71 / 84 % | 83 / 93 % |

The bound holds in distribution and for unseen widths, and for faster inflow it keeps its coverage while a constant bound collapses. For discharge it under-covers, so for an operating mode never seen in training the seed spread is not a reliable warning. The raw spread is under-dispersed (about 0.38 of the error) and is used only through the calibrated factor.

# Appendix G. Multi-node one-dimensional model

The model has 200 layers with plug flow between each run's actual inlet and outlet rows, an inlet-entrainment diffusivity that depends on the Richardson number, and removal of inversions by mixing. Its four parameters are fitted separately for laminar and SST runs on each split's training and validation designs only. The protocol was committed before any test score; the model was then scored once with the same metrics and snapshots as every other model. It runs in about 0.05 s per case.

**Table G.1. Multi-node model against the hybrid canonical surrogates (means; positive differences favour the multi-node model).**

| Split | Field, % of ΔT: MN / FNO / U-Net | Profile, % of ΔT: MN / FNO / U-Net | Outlet, K: MN / FNO / U-Net |
|---|---|---|---|
| Random | 7.07 / 4.02 / 3.62 | 6.21 / 2.53 / 2.26 | 0.83 / 0.85 / 0.67 |
| Unseen width | 7.56 / 4.44 / 6.23 | 6.65 / 2.89 / 3.11 | 0.95 / 1.01 / 2.01 |
| Discharge | 7.58 / 4.48 / 4.37 | 6.63 / 2.90 / 3.02 | 0.98 / 1.17 / 1.29 |
| Faster inflow | 13.61 / 9.83 / 9.21 | 9.60 / 5.51 / 5.46 | 1.46 / 1.80 / 1.62 |

On discharge, calibrated on charging only, the multi-node model has 7.58 % field error against 4.48 and 4.37 %, but lower outlet error by 0.17 K [0.02, 0.34] and 0.31 K [0.12, 0.52]. The outlet metric is the area-averaged port-adjacent temperature; usefulness for the delivered (flow-weighted) temperature would need a flux-weighted comparison.

# Appendix H. Reproducibility audit

Each released checkpoint was copied from the machine that trained it (the `sources` field of the merged results) and rescored from the frozen data with the unchanged evaluation code; the code was md5-identical on all machines. All 96 tank checkpoints reproduce their 19,704 stored per-run field scores exactly. One tank checkpoint first released had come from an earlier attempt of the same job on a machine that later failed; it was replaced with the correct file, which then reproduced exactly, and no reported number changed. All 108 PCM checkpoints, rescored on their training machines, reproduce all 16,056 per-run scores exactly on every compared metric. The only metric that can be undefined (t90 error) is undefined exactly when t90 is not reached, and the reached flag matched on every run, so the defined and undefined entries also match. In a six-checkpoint spot check on a different GPU model (laptop RTX 4060 against RTX 4070 Ti training), the largest per-run field RMSE difference was 1.6 × 10⁻⁴ K; checkpoints trained on the same GPU type reproduced exactly. All six training machines used Python 3.12.3, PyTorch 2.14.1 with CUDA 12.6 and OpenFOAM v2606.

# Appendix I. Metric definitions and proxies

**Tank.** Field RMSE is the mean over scored snapshots of the per-snapshot RMS difference of θ over the fluid cells, in % of ΔT. The profile metric uses horizontally averaged θ. Stored-energy error is the mean-θ difference as a fraction of a full charge; it is a constant-ρc_p proxy whose weight varies by 0.990 to 1.009 over the temperature range, so a model's real-property energy error equals its proxy error within ±1 %. The outlet metric is the area-averaged temperature of the cells next to the outlet. It differs from the flow-weighted (mixing-cup) outlet temperature by a median 0.62 % of ΔT over all snapshots and 2.3 % in the breakthrough window, and by up to about 30 % in some very-high-Ri laminar runs where a sharp thermocline crosses the outlet slot. The thermocline midpoint is the height where the horizontally averaged θ crosses 0.5; snapshots where the label has no crossing (median 2.5 % per run, up to 51 %) are excluded from the midpoint error and counted separately.

**PCM.** Field RMSE is in K over PCM cells. The t90 error is |t90,pred − t90,true| / t90,true, where the prediction is evaluated on a fixed input-only time grid up to τ = 3 and the reference t90 is interpolated between field snapshots; on all six test sets the reference matches the dense liquid-fraction series within 0.10 %. The t90 error is reported only for runs whose prediction reaches 0.9, together with the share that do. The energy metric covers sensible and latent energy in the PCM cells, normalised by their full-charge capacity, and excludes energy stored in the fins.
