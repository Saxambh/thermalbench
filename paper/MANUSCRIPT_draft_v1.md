# ThermalStorageBench: A CFD Benchmark for Machine Learning in Sensible and Latent Thermal Energy Storage

**Saxam Bhattarai** ᵃ · **Bivek Baral** ᵃ · **Henrik Davidsson** ᵇ

ᵃ Kathmandu University, Dhulikhel, Nepal · ᵇ Energy and Building Design, Lund University (LTH), Lund, Sweden

*Corresponding author: to be decided before submission.*

*E-mail addresses:* saxambhattarai1@gmail.com (S. Bhattarai), bivek@ku.edu.np (B. Baral), [TO CHECK] (H. Davidsson).

*Draft v1, 9 November 2026, for co-author reading; not for circulation. Every number is generated from the committed result files and checked by an independent script (477 checks pass). Items marked [TO CHECK] are open.*

---

## Abstract

Machine-learning surrogates for thermal energy storage are almost always trained and tested on a study's own small set of simulations, so their results cannot be compared. We present ThermalStorageBench, an open benchmark of transient two-dimensional OpenFOAM simulations for two storage families: 1,212 charging and discharging runs of stratified water tanks (sensible storage) and 500 melting runs of finned and tilted phase change material (PCM) cells (latent storage). The release includes fixed design-level train/test splits for interpolation and eight out-of-distribution tests, engineering metrics, baselines from one-dimensional storage models to three neural architectures, pre-registered verification cases, and validation against four experiments. The best neural models reach a tank field error of 3.5 to 4.5 % of the inlet-to-tank temperature difference on interpolation, unseen widths and discharge, about half that of a calibrated multi-node model; for the networks, a change of frame using the charge/discharge symmetry is needed to predict discharge from charge-only training. For PCM melting, the best neural model is 2 to 4 times more accurate than the best interpolation on random, fin-count and heating tests, but inverse-distance interpolation has lower field error than every neural model when the material changes, in both directions. Which model is preferable depends on the predicted quantity: a one-dimensional model predicts near-outlet temperature better on discharge and high-flow cases, and the model with the lowest field error is not the one with the lowest melt-time error. All 204 released network checkpoints reproduce their reported per-run scores when rescored from the deposited data.

**Keywords:** thermal energy storage; benchmark dataset; phase change material; stratified tank; neural operator; computational fluid dynamics

---

# 1. Introduction

Thermal energy storage is central to solar thermal systems, district heating and the flexible operation of heat pumps. Its design and control depend on transient models that resolve how a thermocline forms and decays in a water tank, or how a melt front advances through a phase change material (PCM). Computational fluid dynamics (CFD) resolves these processes but costs hours to days per case, which rules it out for design sweeps, control and system simulation. One-dimensional multi-node models are fast but cannot represent jet mixing, inlet effects or the convective structure of melting.

Machine-learning surrogates are proposed to close this gap, and studies for thermal storage have multiplied. Almost all of them train a model on a set of simulations produced for that study alone: for example, three simulations of a finned enclosure in the closest PCM study [1], CFD cases for one optimisation of a concrete store [2], or one PCM system at a time, including a Fourier neural operator for PCM walls [3,4,5]. Different studies use different geometries, inputs, metrics and test sets, so their accuracies cannot be compared, and it is unknown which methods generalise beyond the cases they were trained on. Other fields solved this problem with shared benchmarks: PDEBench [6], The Well [7], AirfRANS [8], CFDBench [9], BubbleML for boiling [10], and recently REALM for reactive flows [11] and IC-ThermBench for chip thermal prediction [12]. A recent review of open data for two-phase heat transfer makes the same case [13]. For thermal energy storage, our searches of Scopus and arXiv (October and November 2026) found no open, verified, multi-case simulation dataset with fixed out-of-distribution splits and machine-learning baselines.

This paper presents ThermalStorageBench: an open benchmark combining transient stratified-tank and PCM-melting fields with fixed design-level splits, engineering metrics, and released CFD verification cases. Its two families cover sensible and latent storage (Fig. 1, Table 1). The paper reports four results:

1. Within one material and on field and profile metrics, neural models clearly beat interpolation and one-dimensional models; when the PCM material changes, the ranking reverses and simple interpolation wins.
2. For the neural networks, the charge/discharge symmetry of a stratified tank, applied as a change of frame, makes discharge predictable from charge-only training.
3. The preferred model depends on the predicted quantity: field against melt time, and vertical profile against near-outlet temperature.
4. The release is auditable: all 204 network checkpoints reproduce their stored per-run scores when rescored from the deposited data.

Section 2 describes the dataset, Section 3 its validation, Section 4 the benchmark tasks and models, Section 5 the results, and Section 6 what the benchmark does and does not test.

# 2. Dataset

## 2.1 Stratified water tank (sensible storage)

The tank family contains 1,212 transient simulations of 1,020 design points in a two-dimensional rectangular tank of height H = 1 m and width 0.25 to 1.0 m (Fig. 1a, Table 1). Water enters and leaves through slots either in the side walls (type A, 844 runs) or in the lid and bottom (type B, 368 runs), with slot height 20 to 80 mm and port offset 0 to 0.2 H. A run either charges the tank (hot water in at the top, 849 runs) or discharges it (cold water in at the bottom, 363 runs), from a uniform (853) or pre-stratified (359) initial state. Inlet velocity spans 0.005 to 0.2 m/s and the inlet-to-tank temperature difference ΔT spans 5 to 50 K. The design points are a Sobol sample, snapped to a 10 mm grid. The slot Reynolds number Re = u s/ν spans 117 to 24,000 and the bulk Richardson number Ri = gβΔT H/u² spans 0.38 to 7,450. Runs end at a dimensionless time t* = tQ/V (inflow volume over tank volume, both per unit depth) between 0.32 and 1.2.

All runs use OpenFOAM v2606 (buoyantPimpleFoam) with temperature-dependent water properties rather than the Boussinesq approximation, a uniform 5 mm mesh, and PIMPLE with two outer and two pressure correctors and a maximum Courant number of 0.5. The flow model is set by the inlet Reynolds number: laminar below 1,500, k-ω SST above 3,000 [14], and both in between. This gives 432 laminar-only, 396 SST-only and 192 design points run with both closures; the 192 twin pairs differ by a median 3.9 % of ΔT in field, so the closure choice matters and the pairs form a closure-comparison subset. The SST runs use OpenFOAM's buoyancy production term; we found a sign error in its Boussinesq branch, which these runs do not use [TO CHECK: report the issue to the OpenFOAM developers before submission; a report is drafted].

Each run stores 121 snapshots of temperature, pressure and velocity (and the turbulence fields for SST) on the native grid, with stored energy, exergy, the MIX stratification number, thermocline midpoint and thickness and outlet temperature per snapshot, and dense outlet series.

## 2.2 PCM melting cell (latent storage)

The PCM family contains 500 melting runs in a two-dimensional enclosure of height 100 mm and width 20 to 60 mm, heated from one wall (Fig. 1b). Half use n-octadecane and half lauric acid, with constant properties and the enthalpy-porosity method [15]. The heated wall carries 0 to 5 conducting aluminium fins (length 0.2 to 0.8 of the width, thickness 1 to 4 mm). The cell is heated from the side (350 runs), tilted by 45° (75) or heated from below (75). Wall superheat is 8 to 30 K and initial subcooling 0.5 to 22.3 K, giving laminar natural convection at Rayleigh numbers (on the cell height) Ra_H = 1.5 × 10⁸ to 9.0 × 10⁸ and Stefan numbers Ste = c_p ΔT/L = 0.07 to 0.37. The mushy-zone constant is 10⁶ for n-octadecane, taken from Vogel and Thess [16] before any run, and 5 × 10⁶ with a melting range of 43.5 to 48.2 °C for lauric acid, chosen after a comparison with the plain-wall experiment of Kamkari and Shokouhmand [17]; that experiment therefore informed the setting, and the finned and tilted experiments tested it afterwards. The mesh is uniform at 0.5 mm, and each run stops at a liquid fraction of 0.995. A run stores 88 to 204 snapshots of temperature, liquid fraction and velocity, with stored energy, Nusselt number and heat input.

[[TABLE1]]

## 2.3 Quality control and freeze

Every run passed automated quality checks (energy balance, field bounds and, for PCM, solver convergence). In the tank family, 1,211 runs pass and one is kept with a warning. Five planned runs were excluded: one for an energy-balance failure, and four discharge runs whose hot layer lies entirely above the outlet, so that almost no energy leaves (a design rule fixed before the final training). The median energy-conservation error is 7.4 × 10⁻⁵ of the exchanged energy. In the PCM family, a solver-convergence check, added after the first non-converged case was found, led to 34 corrected reruns with a different linear solver: 13 whose pressure solve had failed and 21 rerun under a pre-registered rule for warning cases. Another 39 cases with milder warnings were kept under the same rule; Section 5.2 shows that excluding them changes no conclusion. Both families are frozen in manifests that list every run with the md5 checksum of its file (Table 1).

Two tank runs, T0211 and T0052, carry a numerical-setting uncertainty of about 7 % of ΔT, found in the verification below. They are flagged in the release rather than removed.

## 2.4 Verification

Agreement limits for the tank were committed before any comparison was run (Appendix A): for example, at most 1.5 % of ΔT in field RMSE between a test and a production solution, and at most 0.5 % in stored energy. Halving the mesh to 2.5 mm in four designs changes the field by 0.34 to 2.76 % of ΔT. The largest difference, in a laminar design, is of the same order as the response of that design to a 0.01 % change in inlet velocity (2.76 against 1.85 %): the unsteady solution itself moves that much, so the mesh effect cannot be separated from it, and we do not claim mesh convergence. Stored energy and thermocline position agree within their limits, with one borderline energy difference (0.96 %); the outlet temperature is borderline in some event windows (Appendix A). Doubling the outer iterations or halving the time step changed one low-Richardson SST discharge run (T0211) by 7.4 % of ΔT. Of 14 similar designs tested, one more (T0052) is affected under a rule added afterwards, and a pre-registered sample of ten found none (95 % interval 0 to 31 %), so the effect is not systematic across the regime; these two runs are the flags above. On the 588 SST runs, 60 % of wall cell-snapshots have a first-cell y⁺ below 5 (viscous sublayer) and 38.5 % lie in the buffer layer, a stated limitation at the highest Reynolds numbers.

For PCM, refining from 0.5 to 0.25 mm in six designs delays melting by 1.0 to 8.7 %, always in the same direction: the 0.5 mm labels melt early. Where three levels allow it (design G131), the grid convergence index of the time to 99 % melting is 13.06 % on the medium and 7.50 % on the fine grid (observed order 0.741). This bias is stated in the dataset card so that users can judge model differences smaller than it.

# 3. Validation against experiments

## 3.1 Tank: a buoyant jet in a real tank (Lou et al.)

No quasi-two-dimensional tank-charging experiment with field data was found, so the SST set-up of the tank family (same solver, closure, buoyancy source and properties) was tested in three dimensions against the PIV and temperature measurements of Lou et al. [18] (Fig. 2a, b). Over 14 times, the simulated jet penetration h_j stays within 9 mm of the mean of the two PIV tests up to 450 s (mean −2.9 mm over 50 to 300 s) but runs 7 to 13 mm deeper than both tests after 500 s (mean +10.8 mm); Lou et al.'s own CFD was 29.7 mm too shallow on average.

For the outlet temperature, the published curve is given as an outlet-based bulk Richardson number Ri_bulk, proportional to β(T)(T_in − T_out), and its conversion back to temperature needs an assumption about the thermal expansion coefficient β that the paper does not state. With constant β in the reconstruction of Lou et al.'s experimental outlet curve, the 10 % breakthrough occurred at t* = 0.806 in the simulation and 0.796 in the experiment. The simulated outlet then warmed more rapidly, reaching 50 % at t* = 0.932, compared with approximately 0.97 to 1.045 under the two β assumptions examined. Over t* = 0.95 to 1.45, the simulated outlet was approximately 0.08 to 0.20 warmer in normalised temperature. Heat loss from the uninsulated experimental tank is consistent with the direction of this discrepancy; its contribution cannot be isolated from the published measurements. The reported charging efficiency, which needs no β assumption, points the same way: 0.750 in the experiment against 0.919 from the simulation's port energy balance at t* = 1.0 (Appendix B). This tests the SST solver set-up against a three-dimensional experiment; it does not validate the two-dimensional labels directly, and the laminar closure and discharge are not validated against experiment (no suitable tank experiment was found).

## 3.2 PCM: plain, finned and tilted walls

For the plain wall of Kamkari and Shokouhmand [17], the model at the dataset settings stays within ±0.06 in liquid fraction and melts fully at 194.7 min against about 195 min measured (Fig. 2c). This agreement is partly by construction, because the same experiment set the lauric-acid mushy constant, and it may partly reflect cancellation between the early melting of the 0.5 mm mesh and model error. With one and three fins the model melts about 0.1 too fast during the first hour and then approaches the experiment; the one-fin full-melting time matches (161 against about 160 min) and the three-fin case melts 8 % early. The tilted cases of the same group [19] agree within ±0.08 (runs with a mushy constant of 10⁶ instead of 5 × 10⁶, which changes the plain-wall curve by about 0.01). For Vogel and Thess [16], our run matches their two-dimensional model within the ±0.02 digitising accuracy (mean absolute difference 0.009) and the experiment with a mean absolute difference of 0.030 (Fig. 2d). The remaining finned-wall difference combines residual discretisation, properties, boundary conditions, experimental uncertainty and model form, which these runs do not separate; the three-dimensional front and back walls of the experiment, which damp convection near the fins, are one candidate.

# 4. Benchmark tasks, splits, metrics and models

## 4.1 Tasks

Tank: given the design inputs (geometry, operation, temperatures, initial state, closure) and a dimensionless time t* = tQ/V, predict the normalised temperature field θ = (T − T_c)/(T_h − T_c) on the native grid. PCM: given the design inputs and τ = t/t_ref, predict the normalised temperature θ = (T − T_0)/(T_w − T_0), with T_w the wall and T_0 the initial temperature, and the liquid-fraction field. Here t_ref is an a priori melting time computed from the inputs only (energy over a laminar Nu ~ Ra^0.25 heat rate), so the true melting time is never an input. Both tasks query any time directly; an autoregressive rollout task is not part of this release.

## 4.2 Splits

Splits are assigned by design point, so laminar and SST twins of one design are never divided between training and test, and they are fixed by parameters or a hash of the case identifier (Fig. 1c). The tank has a random split (10 % of design points) and three out-of-distribution splits: unseen widths outside 0.33 to 0.93 m (the tails of one geometry family, not new geometry families), discharge (all discharging runs, training on charging only, an operating mode never seen), and faster inflow (Reynolds number above the design 90th percentile; all of its test runs are SST, so it tests Reynolds extrapolation and closure together). The PCM family has a random split and five out-of-distribution splits: held-out fin counts (4 and 5 fins, training on 0 to 3), stronger heating (superheat above the 90th percentile), unseen tilt (45° and heating from below, training on side heating), and material transfer in both directions (lauric acid tested after training on n-octadecane, and the reverse).

## 4.3 Metrics

The primary metric is the temperature-field RMSE (tank in % of ΔT, PCM in K). Engineering metrics are scored alongside it: the horizontally averaged vertical profile, the thermocline midpoint (with the share of snapshots where it is undefined reported separately), stored energy as a fraction of full charge, and the near-outlet temperature for the tank; liquid-fraction RMSE, liquid-region overlap, stored energy, and the time to 90 % melting (t90) for PCM. The t90 error is conditional on the prediction reaching 90 % within a fixed input-only horizon (τ ≤ 3), so the share of runs that reach it is always reported with it. Two metrics are proxies (Appendix I). Stored energy uses constant ρc_p, for which a model's real-property energy error equals its proxy error within ±1 %. The outlet metric is the area-averaged temperature of the cells next to the outlet; it differs from the flow-weighted (mixing-cup) outlet temperature by a median 0.6 % of ΔT but by up to about 30 % in some very-high-Ri laminar runs, so we call it the near-outlet temperature.

## 4.4 Baselines and neural models

Baselines span physics and interpolation: the initial field, a one-dimensional ideal stratification model (plug flow with a sharp interface), a calibrated multi-node one-dimensional model with Richardson-dependent inlet mixing whose protocol was fixed before any test score (four parameters fitted per closure by a limited search, so a reasonable rather than an optimal 1D model; Appendix G), and interpolation in standardised parameter space: k-nearest neighbours (k = 5), inverse-distance weighting (IDW; 8 neighbours, weights 1/d²) and radial basis functions (thin-plate spline over 40 neighbours). For PCM there are also a conduction model (the exact two-phase Stefan solution) and a front model that follows the Stefan solution early and then a melt fraction growing linearly in τ with a slope fitted on the training runs.

The neural models are the Fourier neural operator (FNO) [20] and the U-Net convolutional network [21], co-equal baselines with no "main" model, each in up to four variants. *Hybrid* variants learn the correction to a physics base (ideal stratification for the tank, the front model for PCM). *Canonical* variants (tank only) map a discharge run into the charge frame by a 180° rotation with hot and cold exchanged (θ → 1 − θ) and map the prediction back before scoring; this symmetry is exact under the Boussinesq approximation and approximate with real water properties. Building symmetries into networks for fluids is established [22,23,24,25]; we found no prior use of the charge/discharge symmetry in machine learning for storage. A transformer operator, a 4 × 4-patch variant of Transolver [26], was added for PCM after the main results, under a plan fixed before training; it was not run on the tank because a pre-set check (fitting eight training samples to a masked RMSE of 0.01) failed narrowly (0.012), an implementation and resource decision rather than evidence about generalisation. Each network is trained with three seeds, at batch 16 with AdamW and a one-cycle schedule, for 60 epochs (FNO, Transolver) or 100 (U-Net). Learning rates were not tuned for FNO and U-Net; only Transolver's was chosen, between two values, on validation loss. Details are in Appendix D.

# 5. Results

## 5.1 Tank

Table 2 gives the field error of every model on the four tank splits, and Table 3 the engineering metrics.

[[TABLE2]]

[[TABLE3]]

**Surrogates against physics and interpolation.** On random, unseen-width and discharge test runs, the hybrid canonical networks reach 3.6 to 6.2 % of ΔT, against 7.1 to 7.6 % for the calibrated multi-node model, 8.7 to 10.8 % for the best interpolation (where it works at all) and 15 to 17 % for ideal stratification. Across the four splits, both hybrid-canonical surrogates reduced vertical-profile error by 3.6 to 4.1 percentage points of ΔT and thermocline-midpoint error by 6.6 to 19.1 mm relative to the calibrated multi-node model. Faster inflow is the hardest split for the hybrid canonical networks (9.2 and 9.8 %) and for the one-dimensional models.

**For the networks, discharge requires the symmetry** (Fig. 3a). Trained on charging only, the plain networks fail on discharge (65 to 67 %, as poor as interpolation), and the hybrid networks without the frame reach 13 %, between ideal stratification (16.5 %) and the multi-node model (7.6 %), which transfers to discharge without any special treatment. The canonical frame alone brings FNO to 12.4 % and U-Net to 9.9 %, and with the hybrid base both reach about 4.4 %, the same level as on charging. A pre-registered analysis on the 215 discharge designs with no identified exposure before the models were frozen supported the gain of adding the frame to the hybrid model: 9.2 percentage points for FNO and 9.7 for U-Net (Holm-adjusted p = 0.0004 each). These runs were part of the discharge result already reported, so this is a pre-registered subset analysis, not a prospective confirmation (Appendix E).

**Where the networks fail** (Fig. 3b). Error grows as the jet overcomes stratification (Spearman correlation with the bulk Richardson number −0.84 for FNO). All 80 test cases (run-split pairs) above 10 % for the FNO hybrid canonical model are SST runs with Ri below 9.5, where large coherent eddies and wall short-circuits are smoothed out. U-Net has the same regime dependence plus a second failure: 17 of its 18 laminar cases above 10 % are the widest unseen tanks (W > 0.93 m), which accounts for most of its higher error on unseen widths (6.2 against 4.4 % for FNO). No architecture wins everywhere: U-Net variants lead on random and faster inflow, FNO on unseen widths, and on discharge U-Net is ahead by 0.13 percentage points [0.01, 0.24]. Nor is one variant best: the hybrid canonical combination is clearly best only on discharge; the canonical-only models are slightly better on random and faster inflow, and for U-Net on unseen widths the hybrid or canonical model alone beats the combination (design-level intervals, Appendix E). The two flagged runs (Section 2.3) lie in this regime; replacing their labels by alternative CFD references changes the ensemble error by at most 0.43 percentage points and keeps the model ordering (Appendix C).

**The 1D model is competitive near the outlet** (Fig. 5b). For the near-outlet temperature, the multi-node model has lower error than both surrogates on discharge (by 0.17 and 0.31 K) and faster inflow, with paired intervals excluding zero, and a lower mean than U-Net on unseen widths (Table 3). The surrogates remain better on thermocline position on every split, and on stored energy except U-Net on unseen widths. The benefit of full-field prediction therefore depends on which thermal quantity is required.

## 5.2 PCM

Table 4 gives the field and melt-time errors of every model on the six PCM splits.

[[TABLE4]]

**The ranking changes with the generalisation task.** Across the random, fin-count, heating, and orientation splits, all neural variants had lower mean temperature-field RMSE than IDW. The best neural model is 2 to 4 times more accurate than the best baseline on random, held-out fins and stronger heating, while on unseen tilt every model is only modestly better than IDW (6.2 to 7.1 against 7.7 K). The ordering reversed for transfer between n-octadecane and lauric acid in either direction (Fig. 4). Against hybrid U-Net, IDW's mean advantage was 0.26 K [0.10, 0.43] on held-out lauric acid and 3.94 K [3.67, 4.21] on held-out n-octadecane (95 % intervals over test runs, seed means fixed; Appendix E). Individual training seeds reversed the first comparison: two of the three hybrid U-Net seeds beat IDW on lauric acid. On n-octadecane, IDW beats every seed of every model, and several networks rarely predict near-complete melting: only 2.0 % (Transolver) and 33 % (FNO) of their predictions reach 90 % melting within the horizon, against 100 % for hybrid U-Net. These results identify material transfer, particularly prediction of n-octadecane after training on lauric acid, as a limitation of the evaluated surrogates. The standard deviation of field RMSE across the three training seeds is large on these splits (FNO 8.7 and 9.6 K), so single-seed rankings there would not be reliable.

**A third architecture shares the limitation.** The Transolver baseline lies between U-Net and FNO in field error within a material and gives no geometry advantage on tilt or fins. IDW had lower field RMSE than every seed of both Transolver variants in both transfer directions, so the material-transfer limitation holds for all three evaluated architectures.

**Field accuracy and melt time rank models differently** (Fig. 5a). On held-out fin counts, plain U-Net has the lower field RMSE (1.76 against 2.31 K) but plain Transolver the lower t90 error (5.6 against 10.2 %, a paired reduction of 4.69 percentage points [3.43, 6.01]). All 139 runs reach t90 in every seed, so this is not an effect of dropped runs. Within a material, Transolver gives the lowest melt-time error on random, fins and stronger heating (0.7 to 0.8, 5.6 and 1.0 to 1.1 %), although on stronger heating the plain-against-plain difference from U-Net is within its paired interval.

**Solver warnings do not matter.** Removing the 39 retained solver-warning cases from scoring changes neural field RMSE by at most 0.10 K and baseline RMSE by at most 0.60 K, and changes no neural ordering or conclusion.

## 5.3 Reproducibility and cost

Every released checkpoint was taken from the machine that produced its stored score and rescored from the frozen data. All 96 tank checkpoints reproduce their 19,704 stored per-run field scores exactly, and all 108 PCM checkpoints their 16,056 per-run scores on every compared metric. PCM rescoring on the original training workers reproduced all compared finite metric values exactly; in a six-checkpoint laptop spot check, the largest observed cross-GPU discrepancy in per-run field RMSE was 1.6 × 10⁻⁴ K (Appendix H). One released tank checkpoint had come from an earlier attempt of the same job; the audit found and replaced it, and no reported number changed.

A three-seed tank prediction (120 snapshots) takes a median 1.45 s on a laptop RTX 4060 with the model loaded, against a median 2.64 h of single-core CFD: a latency ratio of about 6,500. The hardware differs, so this is not an equal-cost comparison. Generating the tank runs took about 3,200 core-hours at the median run time and the PCM runs about 3,100 core-hours [TO CHECK: planned estimate; replace by the measured total]; training all 96 tank networks took 146.6 GPU-hours. Fig. 6 shows typical predictions, chosen as the median-error test run of each family.

# 6. Discussion: what the benchmark tests and what it does not

**Scope of the labels.** The fields are two-dimensional with adiabatic walls. They test surrogates on realistic buoyant transients; they are not a design tool for a specific three-dimensional tank. The labels are themselves approximate. Tank mesh differences reach 2.76 % of ΔT against best model errors of 3.5 to 4.5 %, and PCM fields at 0.5 and 0.25 mm differ by 4.2 to 7.6 % of ΔT (about 1 to 2 K at a typical ΔT of 30 K), more than the best within-material PCM errors (0.59 to 1.76 K); the PCM labels also melt early by up to 8.7 %. Within-material scores therefore measure agreement with the 0.5 mm reference solutions rather than with the physical process, and model differences smaller than these label uncertainties should not be over-interpreted. Scoring the tank models against alternative CFD references did not change their ranking (Appendix C).

**Scope of the splits and physics.** Unseen widths are the tails of one rectangular geometry family; faster inflow mixes Reynolds-number extrapolation with the closure; discharge relies on an approximate symmetry; and material transfer involves two materials only, so it is transfer between them, not to a third. The PCM family covers melting only, without solidification or cycling, with constant properties, no volume change and a single cell height; fin counts above three appear only in the fin-count test, while the fin validation covers up to three fins. Heating from below at Ra_H up to 9 × 10⁸ is modelled as laminar at 0.5 mm. The tank has 2D slot ports and a fixed height of 1 m.

**Uncertainty.** For the FNO hybrid canonical ensemble, the spread of three seeds ranks the error well (Spearman 0.82 to 0.94 on the tank splits), and an error bound calibrated on validation runs holds close to its stated rate in distribution, for unseen widths and for faster inflow (88 to 91 % at a nominal 90 %), but under-covers on discharge (71 %; Appendix F). For a mode never seen in training, the seed spread is not a reliable warning.

**How to use the benchmark.** We recommend reporting results per seed and not only means, reporting the share of runs that reach t90 next to the t90 error, and reporting the flagged tank runs separately. The test splits are fixed; validation data come from the training side of each split.

**What we do not claim.** We do not claim mesh convergence, three-dimensional validity of the two-dimensional labels, that any architecture is best overall, that the seed spread is reliable for an unseen operating mode, or novelty of building symmetries into neural networks.

# 7. Conclusions

ThermalStorageBench provides 1,712 quality-controlled transient CFD simulations of sensible and latent thermal storage, with verification on representative designs, with fixed splits, engineering metrics, baselines and reproducible checkpoints. Applying it shows that neural models are clearly better than interpolation and one-dimensional models within a material on field and profile metrics, that a simple change of frame from the charge/discharge symmetry lets the networks predict discharge from charging data, and that the preferred model depends on the quantity needed. It also shows a clear open problem: when the PCM material changes, simple interpolation beats every evaluated neural model, most strongly for n-octadecane after training on lauric acid. The data, code, splits and checkpoints are released so that new models can be compared on equal terms.

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

Stored energy and thermocline position agree within their limits except one borderline energy difference (T0243, 0.96 %). The outlet temperature is borderline in the event window of T0408 (2.03 %) and in every variant of T0393 (2.85 to 3.40 %, the perturbation run included); T0052 with four outer correctors differs by 1.08 % in energy and 5.44 % in outlet temperature. In T0551 the mesh difference (2.76 %) is of the same order as the response to the 0.01 % inlet perturbation (1.85 %), so the two cannot be separated in that design. In T0243 the mesh difference lies on the thermocline interface and grows with time. A 10 mm grid does not converge monotonically with the other two levels, so no order or GCI is reported, and the 5 mm mesh is not called converged.

T0211 shows a numerical-setting dependence: n4 and co25 differ from the production run by 7.4 % but from each other by 2.49 %, so neither is shown to be converged, while the perturbation moves it by only 0.47 %. The difference is a phase error in the tilting of the thermocline after the cold jet reaches it. Two pre-registered tests asked whether this is a regime. The four nearest SST designs in (log Re, log Ri) gave no affected design under the first rule; T0052 missed it narrowly and is counted as affected under a ratio rule added afterwards (labelled post hoc). A second sample of ten wide, low-Ri SST designs, drawn by a fixed rule before any run, gave 0 of 10 affected (95 % interval 0 to 31 %), with all differences at most 0.05 % of ΔT. T0211 and T0052 are flagged (Appendix C); T0156, T0551 and T0393 are listed as sensitive.

Across the 192 design points run with both closures, laminar and SST fields differ by a median 3.9 % of ΔT (10th to 90th percentile 0.7 to 8.3 %), governed by stratification (Spearman correlation with Ri −0.62) rather than Reynolds number (+0.12). In the 588 SST runs, 60 % of wall cell-snapshots have y⁺ below 5, 38.5 % lie in the buffer layer and 1.6 % above 30.

## A.3 PCM mesh, time step and solver

In six dataset cases compared at 0.5 and 0.25 mm, the time to 99 % melting (t99) is 1.0 to 8.7 % later on the finer mesh (median 4.9 %), always in the same direction. Melt curves agree within 0.036 in liquid fraction; the field differs by 4.2 to 7.6 % of ΔT, mostly in a band around the melt front. For case G131 (lauric acid, no fins; 1.0, 0.5 and 0.25 mm), the dense liquid-fraction series gives an observed order of 0.741 and a GCI of 13.06 % on the 0.5 mm and 7.50 % on the 0.25 mm grid; the 0.5 mm run melts about 9.5 % before the extrapolated t99. The time step is Courant-limited and halves with the mesh, so this is a combined space-time refinement. Case G301 (n-octadecane) has an observed order outside 0.5 to 3, so no GCI is given; its 0.5 mm run melts 6.76 % earlier than the 0.25 mm run.

The pressure solve failed to converge in some cases (the first was P0124). A solver-convergence check was added; the 13 failed cases were rerun with a preconditioned conjugate-gradient solver, which changed the melt time by −2.1 to +0.9 % in the four cases compared. A pre-registered test reran the two most severe warning cases of each of three kinds (six cases); one kind changed materially (P0075, 2.54 % of ΔT), so all 17 cases of that kind were rerun. Together these are the 34 corrected reruns (13 failed, 6 tested and 15 further cases of the changed kind), and the 39 cases of the other two kinds were kept (sensitivity in Appendix C).

# Appendix B. Lou et al. tank details

**Case.** The three-dimensional run uses quarter symmetry (230,156 cells), buoyantPimpleFoam with k-ω SST and the same buoyancy source term as the dataset runs (OpenFOAM's buoyancyTurbSource in the compressible solver), real water properties and a maximum Courant number of 2, with baffle-hole open areas within 1 % of the target. It ran to 750 s for the jet comparison and was extended to 1,275 s (t* = 1.507) for the outlet. h_j is taken as the distance from the inlet port to the point on the centreline where the vertical velocity changes sign, averaged over ±6.25 s as in the PIV.

**Jet depth.** Against the mean of the two PIV tests over 14 times, the difference is −2.9 mm (50 to 300 s), −0.9 mm (350 to 450 s) and +10.8 mm (500 to 700 s). After 500 s the simulated jet is deeper than both tests separately, and it penetrates about 19 % faster than the PIV (0.180 against 0.151 mm/s, linear fits). The spread between the two PIV tests indicates repeatability and is not an uncertainty band. Refining the lower baffle region changed h_j by at most 0.1 mm up to 300 s.

**Outlet reconstruction.** The experimental outlet curve (Fig. 15a of [18], uniform baffle, 1 L/min, 333.15 K into 293.15 K) was digitised by curve colour from the publisher's image (about ±0.01). Because Ri_bulk is proportional to β(T)(T_in − T_out), it was converted back to T*_out in two ways: with constant β, T*_out = 1 − Ri/Ri_0 with Ri_0 the plateau before breakthrough; and with β evaluated at the mean of inlet and outlet temperature, solving for T_out. The second reconstruction crosses T* = 0.1 at about t* = 0.77 (interpolated across a gap in the digitised curve between t* = 0.768 and 0.788). Evaluating β at the outlet temperature gives two roots near the plateau and was not used.

**Charging efficiency.** The simulated σ(t*) is the integral of (1 − T*_out) over t*, the port energy balance at constant ρc_p. The published σ rises with a slope of 0.81 on the pre-breakthrough plateau, where a loss-free and perfectly measured tank gives 1.0, and stays below the simulation (0.750 against 0.919 at t* = 1.0; 0.850 against 0.985 at t* = 1.5). This supports a heat-loss explanation in sign, without separating wall loss, mixing and measurement.

# Appendix C. Label flags, alternative references and solver warnings

**Flags.** T0211_sst and T0052_sst carry a numerical-setting uncertainty of 7.4 and 6.8 % of ΔT (Appendix A.2) and are flagged in `label_flags_tank.json`; both are test runs (discharge and unseen width).

**Alternative references.** All held-out tank runs with an alternative CFD solution (18 runs, 23 run-split rows; nothing selected) were scored against each alternative with the same frozen predictions of the two hybrid canonical models. Across the four references (2.5 mm mesh, n4, co25, perturbation), the ensemble field error changes by at most 0.54 percentage points in any row and by at most 0.43 percentage points for the flagged runs; the mean FNO minus U-Net gap changes by at most 0.04 percentage points. One of 64 ensemble comparisons flips the ranking (T0221_lam against the 2.5 mm reference, where the two models differ by 0.11). Similar scalar errors against two CFD references cannot show how much error the two references share with the true solution.

**PCM solver warnings.** The 39 retained warning cases fall into the test sets as random 3, held-out fins 15, stronger heating 4, held-out lauric acid 24, held-out n-octadecane 15 and unseen tilt 11. Removing them from scoring changes neural field RMSE by at most 0.10 K and baseline RMSE by at most 0.60 K. The ordering of the neural models is unchanged on every split and metric, and every neural-against-baseline conclusion is unchanged. This tests exclusion from scoring, not retraining without these cases.

# Appendix D. Models and training

**Architectures.** FNO: four Fourier layers, width 32, 16 retained modes in each direction, with pointwise skips (4.2 M real-valued parameters, counting each complex spectral weight as two). U-Net: four levels, base width 32 (7.8 M). The counts are the same for both families (from the released checkpoints). Transolver (PCM only): six layers of physics attention, width 128, 8 heads, 32 slices, on 4 × 4-cell patch tokens embedded by a patch convolution and decoded to their 16 cells (1.16 M). Inputs are the design parameters broadcast as channels, the time, two normalised coordinates and, for hybrid models, the physics-base field.

**Training.** AdamW (weight decay 10⁻⁴) with a one-cycle schedule, peak learning rate 10⁻³ (3 × 10⁻⁴ for Transolver, chosen on validation loss only between 10⁻³ and 3 × 10⁻⁴: 0.0456 against 0.0473), batch 16, bfloat16 autocast, 60 epochs for FNO and Transolver and 100 for U-Net (U-Net was still improving between 60 and 100 epochs in a trial run). The checkpoint with the best validation loss is scored once on the test set. Each model is trained with seeds 0, 1 and 2. Tank test scores use every 10th snapshot, PCM every 5th. The epoch counts were fixed before the final training from pipeline trial runs on earlier subsets of the data (one with 629 tank runs); those trials recorded validation and test scores of preliminary models on those subsets, which we disclose. FNO hybrid canonical at 150 epochs was not better than at 60 on validation loss (0.0378 against 0.0374). Interpolation settings (k = 5; IDW with 8 neighbours and weights 1/d²; thin-plate-spline RBF over 40 neighbours) were set once and not tuned.

**Hybrid and canonical models.** A hybrid model predicts the correction to a physics base: the ideal-stratification field for the tank (plug flow with a sharp interface placed by the energy balance) and the conduction-then-convection front model for PCM. The canonical frame maps a discharge run to the charge frame by a 180° rotation and θ → 1 − θ, on input and back before scoring; the transform is its own inverse to 3 × 10⁻⁸.

**Transolver.** The plan, the analysis and the expectations were committed before training. Tokens of single cells cost 15 times FNO per step and fitted eight training samples no better, so 4 × 4 patches were used (amendment committed before any validation or test use). The tank was to be run only if the patch model fitted eight tank training samples to a masked RMSE of 0.01 within 1,600 steps; the best variant, with convolutional slice projections, reached 0.012, so the tank was not run. This is an implementation and resource decision; an eight-sample fit does not show how Transolver would generalise on tank data.

# Appendix E. Statistics

All intervals are descriptive 95 % percentile bootstrap intervals (10,000 resamples). Neural scores are the per-run mean of three seeds.

**Tank, design level.** Runs are averaged per design, and designs are resampled. On the random split, hybrid canonical U-Net is better than hybrid canonical FNO by 0.41 percentage points [0.34, 0.48]; on unseen widths FNO is better (Table 2). Full tables: `thermbench_ml/stats_2026-11-07/design_ci.md`.

**Discharge confirmation (pre-registered).** The protocol was committed before any subset score was computed. On the 259 discharge test runs from 215 designs with no identified exposure before the models were frozen, adding the canonical frame to the hybrid model improves field error by 9.17 percentage points [8.33, 10.02] (FNO; 96 % of designs) and 9.74 [8.84, 10.64] (U-Net; 95 %), and the hybrid canonical models beat ideal stratification by 12.53 and 12.61 percentage points. All four hypotheses are supported (Holm-adjusted p = 0.0004 each, the floor of the null-centred bootstrap). The subset was part of the discharge result already reported, so this is a pre-registered subset analysis, not a prospective confirmation.

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

**Data availability.** [TO CHECK before submission: repository and DOI.] The data (1,712 runs, 64.7 GB of run files; about 69 GB with checkpoints), frozen manifests with md5 checksums, split definitions, training and evaluation code, all 204 checkpoints and the verification cases will be deposited in a public repository and cited here.

**Funding.** [TO CONFIRM] (RP2 acknowledged the SOLARFOOD project, Research Council of Norway, project 352437, and Erasmus+ ICM; whether either applies here is for the authors to decide.)

---

## References

[1] S. Shen, C. Wu, F. Duan, Machine learning for predicting the PCM melting process in a rectangular enclosure energy storage, AI Thermal Fluids 1 (2025) 100001. https://doi.org/10.1016/j.aitf.2024.100001

[2] H. Ma, Y. Liu, X. Zhang, S. Fan, H. Shu, X. Zhao, S. Tian, Multi-objective optimization of fin-embedded concrete thermal energy storage systems using computational fluid dynamics and machine learning, Journal of Energy Storage 180 (2026) 124366. https://doi.org/10.1016/j.est.2026.124366

[3] M. Hassanzadeh, E. Ghaderi, F. Fatahi, M.A. Bijarchi, An adaptive physics-driven deep learning framework for a two-phase Stefan problem, arXiv:2512.01011 (2025).

[4] W. Chen, Y. He, Z. Song, Novel prediction model for solid-liquid phase change in latent thermal energy storage based on physics-informed neural networks, Journal of Energy Storage 146 (2026) 120035. https://doi.org/10.1016/j.est.2025.120035

[5] M.-H. Benzaama, A. Boudenne, K. Benzarti, Physics-guided artificial intelligence for latent heat transfer in phase-change material walls: comparison between universal differential equations and the Fourier neural operator, Journal of Energy Storage 175 (2026) 123309. https://doi.org/10.1016/j.est.2026.123309

[6] M. Takamoto, T. Praditia, R. Leiteritz, D. MacKinlay, F. Alesiani, D. Pflüger, M. Niepert, PDEBench: an extensive benchmark for scientific machine learning, Advances in Neural Information Processing Systems 35, Datasets and Benchmarks Track (2022). arXiv:2210.07182

[7] R. Ohana, M. McCabe, L. Meyer, R. Morel, F.J. Agocs, M. Beneitez, et al., The Well: a large-scale collection of diverse physics simulations for machine learning, Advances in Neural Information Processing Systems 37, Datasets and Benchmarks Track (2024). arXiv:2412.00568

[8] F. Bonnet, A.J. Mazari, P. Cinnella, P. Gallinari, AirfRANS: high fidelity computational fluid dynamics dataset for approximating Reynolds-averaged Navier-Stokes solutions, Advances in Neural Information Processing Systems 35, Datasets and Benchmarks Track (2022). arXiv:2212.07564

[9] Y. Luo, Y. Chen, Z. Zhang, CFDBench: a large-scale benchmark for machine learning methods in fluid dynamics, arXiv:2310.05963 (2023).

[10] S.M.S. Hassan, A. Feeney, A. Dhruv, J. Kim, Y. Suh, J. Ryu, Y. Won, A. Chandramowlishwaran, BubbleML: a multiphase multiphysics dataset and benchmarks for machine learning, Advances in Neural Information Processing Systems 36, Datasets and Benchmarks Track (2023). arXiv:2307.14623

[11] R. Mao, R. Zhang, X. Bai, T. Wu, T. Zhang, Z. Chen, et al., Benchmarking neural surrogates on realistic spatiotemporal multiphysics flows, arXiv:2512.18595 (2025).

[12] D. Hang, W. Yang, K. Ding, H. Xin, J. Wei, IC-ThermBench: an open, progressive benchmark for generalizable 2.5D/3D-IC thermal learning, arXiv:2608.23977 (2026).

[13] C. Dunlap, R. Olabiyi, F. Al-Hindawi, H. Pandey, S. Pierson, D. Curl, et al., Open datasets and machine learning for two-phase heat transfer: a review following a spatial-temporal taxonomy, Transport Phenomena 1 (2026) 20260081. https://doi.org/10.1515/tp-2026-0081

[14] F.R. Menter, Two-equation eddy-viscosity turbulence models for engineering applications, AIAA Journal 32 (1994) 1598-1605. https://doi.org/10.2514/3.12149

[15] V.R. Voller, C. Prakash, A fixed grid numerical modelling methodology for convection-diffusion mushy region phase-change problems, International Journal of Heat and Mass Transfer 30 (1987) 1709-1719. https://doi.org/10.1016/0017-9310(87)90317-6

[16] J. Vogel, A. Thess, Validation of a numerical model with a benchmark experiment for melting governed by natural convection in latent thermal energy storage, Applied Thermal Engineering 148 (2019) 147-159. https://doi.org/10.1016/j.applthermaleng.2018.11.032

[17] B. Kamkari, H. Shokouhmand, Experimental investigation of phase change material melting in rectangular enclosures with horizontal partial fins, International Journal of Heat and Mass Transfer 78 (2014) 839-851. https://doi.org/10.1016/j.ijheatmasstransfer.2014.07.056

[18] W. Lou, N. Baudin, S. Roux, Y. Fan, L. Luo, Impact of buoyant jet entrainment on the thermocline behavior in a single-medium thermal energy storage tank, Journal of Energy Storage 71 (2023) 108017. https://doi.org/10.1016/j.est.2023.108017

[19] B. Kamkari, H. Shokouhmand, F. Bruno, Experimental investigation of the effect of inclination angle on convection-driven melting of phase change material in a rectangular enclosure, International Journal of Heat and Mass Transfer 72 (2014) 186-200. https://doi.org/10.1016/j.ijheatmasstransfer.2014.01.014

[20] Z. Li, N. Kovachki, K. Azizzadenesheli, B. Liu, K. Bhattacharya, A. Stuart, A. Anandkumar, Fourier neural operator for parametric partial differential equations, International Conference on Learning Representations (2021). arXiv:2010.08895

[21] O. Ronneberger, P. Fischer, T. Brox, U-Net: convolutional networks for biomedical image segmentation, in: Medical Image Computing and Computer-Assisted Intervention (MICCAI 2015), Lecture Notes in Computer Science 9351, Springer, 2015, pp. 234-241. https://doi.org/10.1007/978-3-319-24574-4_28

[22] R. Wang, R. Walters, R. Yu, Incorporating symmetry into deep dynamics models for improved generalization, International Conference on Learning Representations (2021). arXiv:2002.03061

[23] R. Wang, R. Walters, R. Yu, Approximately equivariant networks for imperfectly symmetric dynamics, Proceedings of the 39th International Conference on Machine Learning, PMLR 162 (2022). arXiv:2201.11969

[24] B. Siddani, S. Balachandar, R. Fang, Rotational and reflectional equivariant convolutional neural network for data-limited applications: multiphase flows, Physics of Fluids 33 (2021) 103323. https://doi.org/10.1063/5.0066049

[25] M. Lino, S. Fotiadis, A.A. Bharath, C.D. Cantwell, Multi-scale rotation-equivariant graph neural networks for unsteady Eulerian fluid dynamics, Physics of Fluids 34 (2022) 087110. https://doi.org/10.1063/5.0097679

[26] H. Wu, H. Luo, H. Wang, J. Wang, M. Long, Transolver: a fast transformer solver for PDEs on general geometries, Proceedings of the 41st International Conference on Machine Learning, PMLR 235 (2024). arXiv:2402.02366
