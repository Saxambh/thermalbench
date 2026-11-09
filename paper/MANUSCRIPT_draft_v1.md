# ThermalStorageBench: A CFD Benchmark for Machine Learning in Sensible and Latent Thermal Energy Storage

**Saxam Bhattarai** ᵃ · **Bivek Baral** ᵃ · **Henrik Davidsson** ᵇ

ᵃ Kathmandu University, Dhulikhel, Nepal · ᵇ Energy and Building Design, Lund University (LTH), Lund, Sweden

*Corresponding author: to be decided before submission.*

*E-mail addresses:* saxambhattarai1@gmail.com (S. Bhattarai), bivek@ku.edu.np (B. Baral), [TO CHECK] (H. Davidsson).

*Draft v1, 9 November 2026, for co-author reading; not for circulation. Every number is generated from the committed result files and checked by an independent script (477 checks pass). Items marked [TO CHECK] are open.*

---

## Abstract

Machine-learning surrogates for thermal energy storage are each trained and tested on their own small set of simulations, so their results cannot be compared. We present ThermalStorageBench, an open benchmark of transient two-dimensional OpenFOAM simulations for two storage families: 1,212 charging and discharging runs of stratified water tanks (sensible storage) and 500 melting runs of finned and tilted phase change material (PCM) cells with n-octadecane and lauric acid (latent storage). The release includes fixed design-level train/test splits that probe interpolation and five kinds of extrapolation, engineering metrics (temperature field, thermocline, outlet temperature, stored energy, melt fraction and melt time), baselines from one-dimensional storage models to three neural-operator architectures, pre-registered verification cases, and validation against four experiments. Neural operators reduce tank field error to 3.5 to 4.5 % of the charging temperature difference on interpolation, unseen widths and discharge, about half that of a calibrated multi-node model, and a change of frame using the charge/discharge symmetry is required for discharge prediction from charge-only training. For PCM melting, the best neural operator is 2 to 4 times more accurate than the best interpolation within a material, but inverse-distance interpolation has lower field error than every neural model when the material changes, in both directions. Which model is preferable depends on the predicted quantity: a one-dimensional model predicts outlet temperature better on discharge and high-flow cases, and the model with the lowest field error is not the one with the lowest melt-time error. All 204 released network checkpoints reproduce their reported scores.

**Keywords:** thermal energy storage; benchmark dataset; phase change material; stratified tank; neural operator; computational fluid dynamics

---

# 1. Introduction

Thermal energy storage is central to solar thermal systems, district heating and the flexible operation of heat pumps. Its design and control depend on transient models that resolve how a thermocline forms and decays in a water tank, or how a melt front advances through a phase change material (PCM). Computational fluid dynamics (CFD) resolves these processes but costs hours to days per case, which rules it out for design sweeps, control and system simulation. One-dimensional multi-node models are fast but cannot represent jet mixing, inlet effects or the convective structure of melting.

Machine-learning surrogates are proposed to close this gap, and studies for PCM storage have multiplied. Almost all of them train a model on a set of simulations produced for that study alone: for example, three simulations of a finned enclosure in the closest PCM study [1], or a few hundred CFD cases for one optimisation [2], or one system at a time [3,4]. Different studies use different geometries, inputs, metrics and test sets, so their accuracies cannot be compared, and it is unknown which methods generalise beyond the cases they were trained on. Other fields solved this problem with shared benchmarks: PDEBench [5], The Well [6], AirfRANS [7], CFDBench [8], BubbleML for boiling [9], and recently REALM for reactive flows [10] and IC-ThermBench for chip thermal prediction [11]. A recent review of open data for two-phase heat transfer makes the same case [12]. For thermal energy storage, our searches of Scopus and arXiv (October and November 2026) found no open, verified, multi-case simulation dataset with fixed out-of-distribution splits and machine-learning baselines.

This paper presents ThermalStorageBench: an open benchmark combining transient stratified-tank and PCM-melting fields with fixed design-level splits, engineering metrics, and released CFD verification cases. Its two families cover sensible and latent storage (Fig. 1, Table 1). Applying the benchmark gives four findings:

1. Within a storage family, neural operators clearly beat interpolation and one-dimensional models, but material transfer in PCM melting reverses the ranking: simple interpolation wins.
2. The charge/discharge symmetry of a stratified tank, applied as a change of frame, makes discharge predictable from charge-only training.
3. The preferred model depends on the predicted quantity: field against melt time, and vertical profile against outlet temperature.
4. Everything is reproducible from the release: all 204 network checkpoints reproduce their reported scores.

Section 2 describes the dataset, Section 3 its validation, Section 4 the benchmark tasks and models, Section 5 the results, and Section 6 what the benchmark does and does not test.

# 2. Dataset

## 2.1 Stratified water tank (sensible storage)

The tank family contains 1,212 transient simulations of 1,020 design points in a two-dimensional rectangular tank of height H = 1 m and width 0.25 to 1.0 m (Fig. 1a, Table 1). Water enters and leaves through slots either in the side walls (type A, 844 runs) or in the lid and bottom (type B, 368 runs), with slot height 20 to 80 mm and port offset 0 to 0.2 H. A run either charges the tank (hot water in at the top, 849 runs) or discharges it (cold water in at the bottom, 363 runs), from a uniform (853) or pre-stratified (359) initial state. Inlet velocity spans 0.005 to 0.2 m/s and the inlet-to-tank temperature difference ΔT spans 5 to 50 K. The design points are a Sobol sample, snapped to a 10 mm grid.

All runs use OpenFOAM v2606 (buoyantPimpleFoam) with temperature-dependent water properties rather than the Boussinesq approximation, a uniform 5 mm mesh, and PIMPLE with two outer and two pressure correctors and a maximum Courant number of 0.5. The flow model is set by the inlet Reynolds number: laminar below 1,500, k-ω SST above 3,000 [13], and both in between. This gives 432 laminar-only, 396 SST-only and 192 design points run with both closures; the 192 twin pairs differ by a median 3.9 % of ΔT in field, so the closure choice matters and the pairs form a closure-comparison subset. The SST runs use OpenFOAM's buoyancy production term; we found and reported a sign error in its Boussinesq branch, which these runs do not use.

Each run stores 121 snapshots of temperature, pressure and velocity (and the turbulence fields for SST) on the native grid, with stored energy, exergy, MIX number, thermocline midpoint and thickness and outlet temperature per snapshot, and dense outlet series.

## 2.2 PCM melting cell (latent storage)

The PCM family contains 500 melting runs in a two-dimensional enclosure of height 100 mm and width 20 to 60 mm, heated from one wall (Fig. 1b). Half use n-octadecane and half lauric acid, with constant properties and the enthalpy-porosity method [14]. The heated wall carries 0 to 5 conducting aluminium fins (length 0.2 to 0.8 of the width, thickness 1 to 4 mm). The cell is heated from the side (350 runs), tilted by 45° (75) or heated from below (75). Wall superheat is 8 to 30 K and initial subcooling 0.5 to 22.3 K, giving laminar natural convection at Ra_H 1.5 × 10⁸ to 9.0 × 10⁸ and Stefan numbers 0.07 to 0.37. The mushy-zone constant is 10⁶ for n-octadecane, taken from Vogel and Thess [15] before any run, and 5 × 10⁶ with a melting range of 43.5 to 48.2 °C for lauric acid, chosen after a comparison with the plain-wall experiment of Kamkari and Shokouhmand [16]; that experiment therefore informed the setting, and the finned and tilted experiments tested it afterwards. The mesh is uniform at 0.5 mm, and each run stops at a liquid fraction of 0.995. A run stores 88 to 204 snapshots of temperature and liquid fraction, with stored energy, Nusselt number and heat input.

[[TABLE1]]

## 2.3 Quality control and freeze

Quality-control rules were written before they were applied. In the tank family, 1,211 runs pass and one is kept with a warning; five planned runs were excluded by rules fixed in advance (an energy-balance failure and a discharge geometry in which no energy can leave). The median energy-conservation error is 7.4 × 10⁻⁵ of the exchanged energy. In the PCM family, 34 cases whose pressure solve failed were rerun with a different linear solver, and 39 cases with solver warnings were kept under a pre-registered rule; Section 5.2 shows that excluding them changes no conclusion. Both families are frozen in manifests that list every run with the md5 checksum of its file (Table 1).

Two tank runs, T0211 and T0052, carry a numerical-setting uncertainty of about 7 % of ΔT, found in the verification below. They are flagged in the release rather than removed.

## 2.4 Verification

Agreement limits for the tank were committed before any comparison was run (Appendix A): for example, at most 1.5 % of ΔT in field RMSE between a test and a production solution, and at most 0.5 % in stored energy. Halving the mesh to 2.5 mm in four designs changes the field by 0.34 to 2.76 % of ΔT. The largest difference, in a laminar design, is of the same size as the response of that design to a 0.01 % change in inlet velocity, so the two cannot be separated; we do not claim mesh convergence. Integral quantities agree within their limits, with one borderline energy difference (0.96 %). Changing the number of outer iterations and the time step identified the low-Richardson SST regime of T0211 as sensitive, which led to the two flags above. On the 588 SST runs, 60 % of wall cells lie below y⁺ = 5 and 38.5 % in the buffer layer, a stated limitation at the highest Reynolds numbers.

For PCM, refining from 0.5 to 0.25 mm in six designs delays melting by 1.0 to 8.7 %, always in the same direction: the 0.5 mm labels melt early. Where three levels allow it (design G131), the grid convergence index of the time to 99 % melting is 13.06 % on the medium and 7.50 % on the fine grid (observed order 0.741). This bias is stated in the dataset card so that users can judge model differences smaller than it.

# 3. Validation against experiments

## 3.1 Tank: a buoyant jet in a real tank (Lou et al.)

No quasi-two-dimensional tank-charging experiment with field data was found, so the solver set-up of the tank family (same solver, closure and properties) was validated in three dimensions against the PIV and temperature measurements of Lou et al. [17] (Fig. 2a, b). Over 14 times, the simulated jet penetration h_j stays within the scatter of the two PIV tests up to 450 s (mean −2.9 mm over 50 to 300 s) but runs 7 to 13 mm deeper than both tests after 500 s (mean +10.8 mm); Lou et al.'s own CFD was 29.7 mm too shallow on average.

For the outlet temperature, the published curve is given as a bulk Richardson number, and its conversion back to temperature needs an assumption about the thermal expansion coefficient β that the paper does not state. With constant β in the reconstruction of Lou et al.'s experimental outlet curve, the 10 % breakthrough occurred at t* = 0.806 in the simulation and 0.796 in the experiment. The simulated outlet then warmed more rapidly, reaching 50 % at t* = 0.932, compared with approximately 0.97 to 1.045 under the two β assumptions examined. Over t* = 0.95 to 1.45, the simulated outlet was approximately 0.08 to 0.20 warmer in normalised temperature. Heat loss from the uninsulated experimental tank is consistent with the direction of this discrepancy; its contribution cannot be isolated from the published measurements. The reported charging efficiency, which needs no β assumption, points the same way: 0.750 in the experiment against 0.919 from the simulation's port energy balance at t* = 1.0 (Appendix B). This validates the solver set-up, not the two-dimensional labels directly.

## 3.2 PCM: plain, finned and tilted walls

For the plain wall of Kamkari and Shokouhmand [16], the model at the dataset settings stays within ±0.05 in liquid fraction at every time and melts fully at the measured 195 min (Fig. 2c). With one and three fins it melts about 0.1 too fast during the first hour and then converges; the one-fin full-melting time matches (161 against about 160 min) and the three-fin case melts 8 % early. The tilted cases of the same group [18] agree within ±0.08. For Vogel and Thess [15], our run matches their two-dimensional model within the ±0.02 digitising accuracy (mean absolute difference 0.009) and the experiment with a mean absolute difference of 0.030 (Fig. 2d). The remaining finned-wall difference combines residual discretisation, properties, boundary conditions, experimental uncertainty and model form, which these runs do not separate; the three-dimensional front and back walls of the experiment, which damp convection near the fins, are one candidate.

# 4. Benchmark tasks, splits, metrics and models

## 4.1 Tasks

Tank: given the design inputs (geometry, operation, temperatures, initial state, closure) and a dimensionless time t* = tQ/V, predict the normalised temperature field θ = (T − T_c)/(T_h − T_c) on the native grid. PCM: given the design inputs and τ = t/t_ref, predict the temperature and liquid-fraction fields. Here t_ref is an a priori melting time computed from the inputs only (energy over a laminar Nu ~ Ra^0.25 heat rate), so the true melting time is never an input.

## 4.2 Splits

Splits are assigned by design point, so laminar and SST twins of one design are never divided between training and test, and they are fixed by parameters or a hash of the case identifier (Fig. 1c). The tank has a random split (10 % of design points) and three out-of-distribution splits: unseen widths outside 0.33 to 0.93 m (the tails of one geometry family, not new geometry families), discharge (all discharging runs, training on charging only, an operating mode never seen), and faster inflow (Reynolds number above the design 90th percentile; all of its test runs are SST, so it tests Reynolds extrapolation and closure together). The PCM family has a random split and five out-of-distribution splits: held-out fin counts (4 and 5 fins, training on 0 to 3), stronger heating (superheat above the 90th percentile), unseen tilt (45° and heating from below, training on side heating), and material transfer in both directions (lauric acid tested after training on n-octadecane, and the reverse).

## 4.3 Metrics

The primary metric is the temperature-field RMSE (tank in % of ΔT, PCM in K). Engineering metrics are scored alongside it: the horizontally averaged vertical profile, the thermocline midpoint (with the share of snapshots where it is undefined reported separately), stored energy as a fraction of full charge, and the near-outlet temperature for the tank; liquid-fraction RMSE, liquid-region overlap, stored energy, and the time to 90 % melting (t90) for PCM. The t90 error is conditional on the prediction reaching 90 % within a fixed input-only horizon (τ ≤ 3), so the share of runs that reach it is always reported with it. The definitions and two proxies (a constant-property energy, within ±1 % of the real-property value; and an area-averaged outlet temperature, which differs from the flow-weighted one by a median 0.6 % of ΔT) are given in Appendix I.

## 4.4 Baselines and neural models

Baselines span physics and interpolation: the initial field, a one-dimensional ideal stratification model (plug flow with a sharp interface), a calibrated multi-node one-dimensional model with Richardson-dependent inlet mixing whose protocol was fixed before any test score (Appendix G), and k-nearest-neighbour, inverse-distance (IDW) and radial-basis-function interpolation in parameter space; for PCM also a conduction (Stefan) model and a conduction-then-convection front model.

The neural models are the Fourier neural operator (FNO) [19] and U-Net [20], co-equal baselines with no "main" model, each in up to four variants. *Hybrid* variants learn the correction to a physics base (ideal stratification for the tank, the front model for PCM). *Canonical* variants (tank only) map a discharge run into the charge frame by a 180° rotation with hot and cold exchanged (θ → 1 − θ) and map the prediction back before scoring; this symmetry is exact under the Boussinesq approximation and approximate with real water properties. Building symmetries into networks for fluids is established [21,22]; we found no prior use of the charge/discharge symmetry in machine learning for storage. A transformer operator, a 4 × 4-patch variant of Transolver [23], was added for PCM after the main results, under a plan fixed before training; it was not run on the tank because a pre-set check (fitting eight training samples to a masked RMSE of 0.01) failed narrowly (0.012), an implementation and resource decision rather than evidence about generalisation. Each network is trained with three seeds, at batch 16 with AdamW and a one-cycle schedule, for 60 epochs (FNO, Transolver) or 100 (U-Net); details are in Appendix D.

# 5. Results

## 5.1 Tank

Table 2 gives the field error of every model on the four tank splits.

[[TABLE2]]

**Surrogates against physics and interpolation.** On random, unseen-width and discharge test runs, the hybrid canonical networks reach 3.6 to 6.2 % of ΔT, against 7.1 to 7.6 % for the calibrated multi-node model, 8.7 to 10.8 % for the best interpolation (where it works at all) and 15 to 17 % for ideal stratification. Across the four splits, both hybrid-canonical surrogates reduced vertical-profile error by 3.6 to 4.1 percentage points of ΔT and thermocline-midpoint error by 6.6 to 19.1 mm relative to the calibrated multi-node model. Faster inflow is the hardest split for every model (9.0 to 10.4 % for the networks).

**Discharge requires the symmetry** (Fig. 3a). Trained on charging only, every model without the canonical frame fails on discharge: 65 to 67 % for the plain networks, as poor as interpolation, and 13 % for the hybrid networks. The canonical frame alone brings FNO to 12.4 % and U-Net to 9.9 %, and with the hybrid base both reach about 4.4 %, the same level as on charging. A pre-registered analysis on the 215 discharge designs with no exposure before the models were frozen confirmed the gain of adding the frame to the hybrid model: 9.2 percentage points for FNO and 9.7 for U-Net (Holm-adjusted p = 0.0004 each; Appendix E).

**Where the networks fail** (Fig. 3b). Error grows as the jet overcomes stratification (Spearman correlation with the bulk Richardson number −0.84 for FNO). All 80 test runs above 10 % for the FNO hybrid canonical model are SST runs with Ri below 9.5, where large coherent eddies and wall short-circuits are smoothed out. U-Net has the same regime dependence plus a second failure: 17 of its 18 laminar runs above 10 % are the widest unseen tanks (W > 0.93 m), which explains its higher error on unseen widths (6.2 against 4.4 % for FNO). No architecture wins everywhere: U-Net variants lead on random and faster inflow, FNO on unseen widths, and the two are equal on discharge. The two flagged runs (Section 2.3) lie in this regime; replacing their labels by alternative CFD references changes the ensemble error by at most 0.43 percentage points and keeps the model ordering (Appendix C).

**The 1D model is competitive near the outlet** (Fig. 5b). For the near-outlet temperature, the multi-node model has lower error than both surrogates on discharge (by 0.17 and 0.31 K) and faster inflow. The benefit of full-field prediction therefore depends on which thermal quantity is required.

## 5.2 PCM

Table 3 gives the field and melt-time errors of every model on the six PCM splits.

[[TABLE3]]

**The ranking changes with the generalisation task.** Across the random, fin-count, heating, and orientation splits, all neural variants had lower mean temperature-field RMSE than IDW. The best neural model is 2 to 4 times more accurate than the best baseline on random, held-out fins and stronger heating, while on unseen tilt every model is only modestly better than IDW (6.2 to 7.1 against 7.7 K). The ordering reversed for transfer between n-octadecane and lauric acid in either direction (Fig. 4). Against hybrid U-Net, IDW's mean advantage was 0.26 K [0.10, 0.43] on held-out lauric acid and 3.94 K [3.67, 4.21] on held-out n-octadecane (95 % intervals over test runs, seed means fixed; Appendix E). Individual training seeds reversed the first comparison: two of the three hybrid U-Net seeds beat IDW on lauric acid. On n-octadecane, IDW beats every seed of every model, and the networks often fail to melt the PCM at all: only 2.0 % (Transolver) and 33 % (FNO) of their predictions reach 90 % melting within the horizon. These results identify material transfer, particularly prediction of n-octadecane after training on lauric acid, as a limitation of the evaluated surrogates. Seed spread is large on these splits (FNO ± 8.7 and ± 9.6 K), so single-seed rankings there would not be reliable.

**A third architecture shares the limitation.** The Transolver baseline lies between U-Net and FNO in field error within a material and gives no geometry advantage on tilt or fins. IDW had lower field RMSE than every seed of both Transolver variants in both transfer directions, so the material-transfer limitation holds for all three evaluated architectures.

**Field accuracy and melt time rank models differently** (Fig. 5a). On held-out fin counts, plain U-Net has the lower field RMSE (1.76 against 2.31 K) but plain Transolver the lower t90 error (5.6 against 10.2 %, a paired reduction of 4.69 percentage points [3.43, 6.01]). All 139 runs reach t90 in every seed, so this is not an effect of dropped runs. Within a material, Transolver gives the lowest melt-time error on random, fins and stronger heating (0.7 to 0.8, 5.6 and 1.0 to 1.1 %).

**Solver warnings do not matter.** Removing the 39 retained solver-warning cases from scoring changes neural field RMSE by at most 0.10 K and baseline RMSE by at most 0.60 K, and changes no neural ordering or conclusion.

## 5.3 Reproducibility and cost

Every released checkpoint was taken from the machine that produced its stored score and rescored from the frozen data. All 96 tank and 108 PCM checkpoints reproduce their stored per-run scores (19,704 and 16,056 run scores). PCM rescoring on the original training workers reproduced all compared finite metric values exactly; in a six-checkpoint laptop spot check, the largest observed cross-GPU discrepancy in per-run field RMSE was 1.6 × 10⁻⁴ K (Appendix H). One released tank checkpoint had come from an earlier attempt of the same job; the audit found and replaced it, and no reported number changed.

A three-seed tank prediction (120 snapshots) takes a median 1.45 s on a laptop RTX 4060 with the model loaded, against a median 2.64 h of single-core CFD: a latency ratio of about 6,500. The hardware differs, so this is not an equal-cost comparison. Fig. 6 shows typical predictions, chosen as the median-error test run of each family.

# 6. Discussion: what the benchmark tests and what it does not

**Scope of the labels.** The fields are two-dimensional with adiabatic walls. They test surrogates on realistic buoyant transients; they are not a design tool for a specific three-dimensional tank. The tank labels carry the mesh and setting uncertainties of Section 2.4 and are not mesh-converged; the PCM labels melt early by up to 8.7 % relative to a finer mesh. Model differences smaller than these should be read with care.

**Scope of the splits.** Unseen widths are the tails of one rectangular geometry family; faster inflow mixes Reynolds-number extrapolation with the closure; discharge relies on an approximate symmetry; and material transfer involves two materials only, so it is transfer between them, not to a third.

**Uncertainty.** The spread of three seeds ranks the error well (Spearman 0.82 to 0.94 on the tank splits), and an error bound calibrated on validation runs holds at its stated rate in distribution, for unseen widths and for faster inflow, but under-covers on discharge (71 % at a nominal 90 %; Appendix F). For a mode never seen in training, the seed spread is not a reliable warning.

**How to use the benchmark.** We recommend reporting results per seed and not only means, reporting the share of runs that reach t90 next to the t90 error, and reporting the flagged tank runs separately. The test splits are fixed; validation data come from the training side of each split.

**What we do not claim.** We do not claim mesh convergence, three-dimensional validity of the two-dimensional labels, that any architecture is best overall, that the seed spread is reliable for an unseen operating mode, or novelty of building symmetries into neural networks.

# 7. Conclusions

ThermalStorageBench provides 1,712 verified transient CFD simulations of sensible and latent thermal storage with fixed splits, engineering metrics, baselines and reproducible checkpoints. Applying it shows that neural operators are clearly better than interpolation and one-dimensional models within a storage family, that a simple change of frame from the charge/discharge symmetry is what makes discharge predictable from charging data, and that the preferred model depends on the quantity needed. It also shows a clear open problem: when the PCM material changes, simple interpolation beats every evaluated neural operator, most strongly for n-octadecane after training on lauric acid. The data, code, splits and checkpoints are released so that new models can be compared on equal terms.

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

---

## Declarations

**CRediT authorship contribution statement.** [TO AGREE with all authors.] Saxam Bhattarai: Conceptualization, Methodology, Software, Investigation, Data curation, Formal analysis, Validation, Visualization, Writing: original draft. Bivek Baral: [roles]. Henrik Davidsson: [roles].

**Declaration of competing interest.** [TO CONFIRM] The authors declare no competing interests.

**Declaration of generative AI and AI-assisted technologies in the manuscript preparation process.** [TO AGREE with all authors; the journal requires this section.] During the preparation of this work the authors used Claude (Anthropic) to assist with code, data analysis and drafting of the text. After using this tool, the authors reviewed and edited the content as needed and take full responsibility for the content of the published article.

**Data availability.** [TO CHECK before submission: repository and DOI.] The data (1,712 runs, 63 GB), frozen manifests with md5 checksums, split definitions, training and evaluation code, all 204 checkpoints and the verification cases will be deposited in a public repository and cited here.

**Funding.** [TO CONFIRM] (RP2 acknowledged the SOLARFOOD project, Research Council of Norway, project 352437, and Erasmus+ ICM; whether either applies here is for the authors to decide.)

---

## References

[References are numbered in order of first citation. Details and DOIs of every entry are to be verified before submission; none is final.]


[1] Shen, Wu, Duan, Machine learning for predicting the PCM melting process in a rectangular enclosure energy storage, AI Thermal Fluids 1 (2025) 100001.

[2] Ma et al., Multi-objective optimization of fin-embedded concrete thermal energy storage systems using CFD and machine learning, J. Energy Storage 180 (2026) 124366.

[3] An adaptive physics-driven deep learning framework for a two-phase Stefan problem, arXiv:2512.01011 (2025). [authors TO CHECK]

[4] Chen, He, Song, J. Energy Storage 146 (2026) 120035. [title TO CHECK]

[5] Takamoto et al., PDEBench: an extensive benchmark for scientific machine learning, NeurIPS Datasets and Benchmarks (2022).

[6] Ohana et al., The Well: a large-scale collection of diverse physics simulations for machine learning, NeurIPS Datasets and Benchmarks (2024).

[7] Bonnet et al., AirfRANS: high fidelity computational fluid dynamics dataset for approximating Reynolds-averaged Navier-Stokes solutions, NeurIPS Datasets and Benchmarks (2022).

[8] Luo et al., CFDBench: a large-scale benchmark for machine learning methods in fluid dynamics, arXiv:2310.05963 (2023).

[9] Hassan et al., BubbleML: a multiphase multiphysics dataset and benchmarks for machine learning, NeurIPS Datasets and Benchmarks (2023).

[10] Benchmarking neural surrogates on realistic spatiotemporal multiphysics flows (REALM), arXiv:2512.18595 (2025). [authors TO CHECK]

[11] IC-ThermBench: an open, progressive benchmark for generalizable 2.5D/3D-IC thermal learning, arXiv:2608.23977 (2026). [authors TO CHECK]

[12] Open datasets and machine learning for two-phase heat transfer: a review following a spatial-temporal taxonomy, arXiv:2605.23037 (2026). [authors TO CHECK]

[13] Menter, Two-equation eddy-viscosity turbulence models for engineering applications, AIAA J. 32 (1994) 1598-1605.

[14] Voller, Prakash, A fixed grid numerical modelling methodology for convection-diffusion mushy region phase-change problems, Int. J. Heat Mass Transf. 30 (1987) 1709-1719.

[15] Vogel, Thess, Validation of a numerical model with a benchmark experiment for melting governed by natural convection in latent thermal energy storage, Appl. Therm. Eng. (2019). [volume and pages TO CHECK]

[16] Kamkari, Shokouhmand, Experimental investigation of phase change material melting in rectangular enclosures with horizontal partial fins, Int. J. Heat Mass Transf. (2014). [volume and pages TO CHECK]

[17] Lou et al., J. Energy Storage 71 (2023) 108017. [title TO CHECK]

[18] Kamkari, Shokouhmand, Bruno, Experimental investigation of the effect of inclination angle on convection-driven melting of phase change material in a rectangular enclosure, Int. J. Heat Mass Transf. (2014). [volume and pages TO CHECK]

[19] Li et al., Fourier neural operator for parametric partial differential equations, ICLR (2021).

[20] Ronneberger, Fischer, Brox, U-Net: convolutional networks for biomedical image segmentation, MICCAI (2015).

[21] Wang, Walters, Yu, Incorporating symmetry into deep dynamics models for improved generalization, ICLR (2021).

[22] Wang, Walters, Yu, Approximately equivariant networks for imperfectly symmetric dynamics, ICML, PMLR 162 (2022).

[23] Wu, Luo, Wang, Wang, Long, Transolver: a fast transformer solver for PDEs on general geometries, ICML (2024).

