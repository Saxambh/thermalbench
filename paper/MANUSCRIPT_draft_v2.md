# ThermalStorageBench: A CFD Benchmark for Machine Learning in Sensible and Latent Thermal Energy Storage

**Saxam Bhattarai** ᵃ · **Bivek Baral** ᵃ · **Henrik Davidsson** ᵇ

ᵃ Kathmandu University, Dhulikhel, Nepal · ᵇ Energy and Building Design, Lund University (LTH), Lund, Sweden

*Corresponding author: to be decided before submission.*

*E-mail addresses:* saxambhattarai1@gmail.com (S. Bhattarai), bivek@ku.edu.np (B. Baral), [TO CHECK] (H. Davidsson).

*Draft v2, 10 November 2026, revised after an external referee read (log: paper/REVISION_v2_2026-11-10.md); for co-author reading, not for circulation. Table numbers are generated from the committed result files and checked by an independent script. Items marked [TO CHECK] are open; items marked [PENDING] await runs in progress.*

---

## Abstract

Machine-learning surrogates for thermal energy storage are almost always trained and tested on a study's own small set of simulations, so their results cannot be compared. We present ThermalStorageBench, an open benchmark of transient two-dimensional OpenFOAM simulations for two storage families: 1,212 charging and discharging runs of stratified water tanks (sensible storage) and 500 melting runs of finned and tilted phase change material (PCM) cells (latent storage). The release includes fixed design-level splits for interpolation and eight out-of-distribution tests, engineering metrics, baselines from one-dimensional models and scalar regressors to three neural architectures, verification cases, and comparisons with four published experiments. The best neural models reach a tank field error of 3.5 to 4.5 % of the inlet-to-tank temperature difference on interpolation, unseen widths and discharge, about half that of a calibrated multi-node model; for the networks, a change of frame using the charge/discharge symmetry is needed to predict discharge from charge-only training. For PCM melting, the best neural model has 3 to 4 times lower field error than inverse-distance interpolation on random, fin-count and heating tests. When the material changes, no neural model beats interpolation on held-out lauric acid, and interpolation is clearly better on held-out n-octadecane. The preferred model depends on the predicted quantity: the lowest field and melt-time errors come from different models, and for melt time under material transfer a gradient-boosting regressor is the most accurate. All 204 released network checkpoints reproduce their reported per-run scores when rescored from the deposited data.

**Keywords:** thermal energy storage; machine learning; surrogate model; benchmark dataset; phase change material; stratified tank; computational fluid dynamics

---

# 1. Introduction

Thermal energy storage is central to solar thermal systems, district heating and the flexible operation of heat pumps. Its design and control depend on transient models that resolve how a thermocline forms and decays in a water tank, or how a melt front advances through a phase change material (PCM). Computational fluid dynamics (CFD) resolves these processes [1] but costs hours to days per case, which rules it out for design sweeps, control and system simulation. One-dimensional multi-node models [2,3] are fast but cannot represent jet mixing, inlet effects or the convective structure of melting; stratification quality itself is usually summarised by indicators such as the MIX number [4,5].

Machine-learning surrogates are proposed to close this gap, and studies for thermal storage have multiplied. Almost all of them train a model on data produced for that study alone. For water tanks, neural networks predict tank temperatures or performance indicators from one system's operating data or a few simulations [6,7,8]. For latent storage, examples are three simulations of a finned enclosure in the closest PCM study [9], CFD cases for one optimisation of a concrete store [10], regressors for the melting time of one triplex-tube design [11], fin-design studies [12,13], and models of one PCM system at a time, including a Fourier neural operator for PCM walls [14,15,16]. Different studies use different geometries, inputs, metrics and test sets, so their accuracies cannot be compared, and it is unknown which methods generalise beyond the cases they were trained on. Other fields solved this problem with shared benchmarks: PDEBench [17], The Well [18], AirfRANS [19], CFDBench [20], BubbleML for boiling [21], and recently REALM for reactive flows [22] and IC-ThermBench for chip thermal prediction [23]. A recent review of open data for two-phase heat transfer makes the same case [24]. For thermal energy storage, our searches of Scopus and arXiv (October and November 2026) found no open, verified, multi-case simulation dataset with fixed out-of-distribution splits and machine-learning baselines.

This paper presents ThermalStorageBench: an open benchmark combining transient stratified-tank and PCM-melting fields with fixed design-level splits, engineering metrics, and released CFD verification cases. Its two families cover sensible and latent storage (Fig. 1, Table 1). The paper reports four results:

1. Within one material and on field and profile metrics, neural models clearly beat interpolation and one-dimensional models; when the PCM material changes, the ranking reverses, and interpolation and low-dimensional regressors match or beat every network.
2. For the neural networks, the charge/discharge symmetry of a stratified tank, applied as a change of frame, makes discharge predictable from charge-only training.
3. The preferred model depends on the predicted quantity: networks for fields, profiles and thermocline position; a one-dimensional model matches them on the delivered outlet temperature; and a scalar regressor is competitive for melt time.
4. The release is auditable: all 204 network checkpoints reproduce their stored per-run scores when rescored from the deposited data.

Section 2 describes the dataset, Section 3 its validation, Section 4 the benchmark tasks and models, Section 5 the results, and Section 6 what the benchmark does and does not test.

# 2. Dataset

## 2.1 Stratified water tank (sensible storage)

The tank family contains 1,212 transient simulations of 1,020 design points in a two-dimensional rectangular tank of height H = 1 m and width 0.25 to 1.0 m (Fig. 1a, Table 1). Water enters and leaves through slots either in the side walls (type A, 844 runs) or in the lid and bottom (type B, 368 runs), with slot height 20 to 80 mm and port offset 0 to 0.2 H. A run either charges the tank (hot water in at the top, 849 runs) or discharges it (cold water in at the bottom, 363 runs), from a uniform (853) or pre-stratified (359) initial state. Inlet velocity spans 0.005 to 0.2 m/s and the inlet-to-tank temperature difference ΔT spans 5 to 50 K. The design points are a Sobol sample [25], snapped to a 10 mm grid. The slot Reynolds number Re = u s/ν spans 117 to 24,000 and the bulk Richardson number Ri = gβΔT H/u² spans 0.38 to 7,450. Runs end at a dimensionless time t* = tQ/V (inflow volume over tank volume, both per unit depth) between 0.32 and 1.2.

All runs use OpenFOAM v2606 [26] (buoyantPimpleFoam) with temperature-dependent water properties rather than the Boussinesq approximation, a uniform 5 mm mesh, and PIMPLE with two outer and two pressure correctors and a maximum Courant number of 0.5. The flow model is set by the inlet Reynolds number: laminar below 1,500, k-ω SST above 3,000 [27], and both in between. This gives 432 laminar-only, 396 SST-only and 192 design points run with both closures; the 192 twin pairs differ by a median 3.9 % of ΔT in field, so the closure choice matters and the pairs form a closure-comparison subset. The SST runs use OpenFOAM's buoyancy production term; we found a sign error in its Boussinesq branch, which these runs do not use, and reported it to the developers (OpenFOAM issue 3645) [TO CHECK: status before submission].

Each run stores 121 snapshots (t = 0 and 120 later times) of temperature, pressure and velocity (and the turbulence fields for SST) on the native grid, with stored energy, exergy, the MIX stratification number, thermocline midpoint and thickness and outlet temperature per snapshot, and dense outlet series.

## 2.2 PCM melting cell (latent storage)

The PCM family contains 500 melting runs in a two-dimensional enclosure of height 100 mm and width 20 to 60 mm, heated from one wall (Fig. 1b). Half use n-octadecane and half lauric acid, with constant properties (Table D.2) and the enthalpy-porosity method [28,29]. The heated wall carries 0 to 5 conducting aluminium fins (length 0.2 to 0.8 of the width, thickness 1 to 4 mm). The cell is heated from the side (350 runs), tilted by 45° (75) or heated from below (75). Wall superheat is 8 to 30 K and initial subcooling 0.5 to 22.3 K, giving laminar natural convection at Rayleigh numbers (on the cell height) Ra_H = 1.5 × 10⁸ to 9.0 × 10⁸ and Stefan numbers Ste = c_p ΔT/L = 0.07 to 0.37. The mushy-zone constant is 10⁶ for n-octadecane, taken from Vogel and Thess [30] before any run, and 5 × 10⁶ with a melting range of 43.5 to 48.2 °C for lauric acid, chosen after a comparison with the plain-wall experiment of Kamkari and Shokouhmand [31]; that experiment therefore informed the setting, and the finned and tilted experiments tested it afterwards. The mesh is uniform at 0.5 mm, and each run stops at a liquid fraction of 0.995. A run stores 88 to 204 snapshots of temperature, liquid fraction and velocity, with stored energy, Nusselt number and heat input.

[[TABLE1]]

## 2.3 Governing equations and boundary conditions

**Tank.** The tank runs solve the variable-density mass, momentum and energy equations of the buoyantPimpleFoam solver,

$$\frac{\partial \rho}{\partial t} + \nabla\cdot(\rho\mathbf{u}) = 0, \qquad \frac{\partial (\rho\mathbf{u})}{\partial t} + \nabla\cdot(\rho\mathbf{u}\mathbf{u}) = -\nabla p_{rgh} - (\mathbf{g}\cdot\mathbf{x})\nabla\rho + \nabla\cdot\boldsymbol{\tau}_{\mathrm{eff}},$$

$$\frac{\partial (\rho h)}{\partial t} + \nabla\cdot(\rho\mathbf{u}h) + \frac{\partial (\rho K)}{\partial t} + \nabla\cdot(\rho\mathbf{u}K) - \frac{\partial p}{\partial t} = \nabla\cdot(\alpha_{\mathrm{eff}}\nabla h),$$

with p_rgh = p − ρ g·x, K = |u|²/2, and effective stress and diffusivity that include the eddy viscosity and an eddy diffusivity (turbulent Prandtl number 0.85) in SST runs. Density, specific heat, viscosity and conductivity of water are polynomials in temperature fitted to IAPWS reference values over 10 to 80 °C (largest error 0.31 %, viscosity), so buoyancy comes from the real density rather than the Boussinesq approximation. At the inlet slot, velocity and temperature are uniform and fixed (SST: turbulence intensity 5 %, mixing length 0.07 times the slot height). At the outlet, temperature has zero gradient, velocity follows from the pressure (inflow allowed, so backflow carries the adjacent tank temperature), and p_rgh has a fixed mean so that the pressure across the slot follows the stratification. All walls are no-slip and adiabatic. SST runs use wall functions for k, ω and ν_t and a thermal wall function for the eddy diffusivity; their y⁺ is reported in Section 2.5.

**PCM.** The PCM runs use the same solver with constant density and properties (Table D.2), the enthalpy-porosity method [28,29] and Boussinesq buoyancy added as a source:

$$\rho\frac{\partial \mathbf{u}}{\partial t} + \rho\nabla\cdot(\mathbf{u}\mathbf{u}) = -\nabla p_{rgh} + \mu\nabla^2\mathbf{u} + \rho\,\mathbf{g}\,\beta\,(T - T_m) - C\,\frac{(1-\alpha)^2}{\alpha^3 + q}\,\mathbf{u},$$

$$\rho c_p\left(\frac{\partial T}{\partial t} + \mathbf{u}\cdot\nabla T\right) = \nabla\cdot(k\nabla T) - \rho L\,\frac{\partial \alpha}{\partial t},$$

with liquid fraction α, mushy-zone constant C (10⁶ kg m⁻³ s⁻¹ for n-octadecane and 5 × 10⁶ for lauric acid), q = 10⁻³, and T_m the midpoint of the melting range (lauric acid 43.5 to 48.2 °C; n-octadecane 27.99 to 28.01 °C, effectively isothermal). The liquid fraction is updated each iteration from the temperature, linearly across the melting range. The heated wall has a fixed temperature T_w and the other walls are adiabatic and no-slip. Fins are cells of the same mesh held solid (α = 0) with the conductivity of aluminium (130 W m⁻¹ K⁻¹) and harmonic-mean face conductivities, so heat conducts through them and across the fin/PCM interface; their heat capacity is taken as that of the PCM. Tilt is applied by rotating gravity.

## 2.4 Quality control and freeze

Every run passed automated quality checks (energy balance, field bounds and, for PCM, solver convergence). In the tank family, 1,211 runs pass and one is kept with a warning. Five planned runs were excluded: one for an energy-balance failure, and four discharge runs whose hot layer lies entirely above the outlet, so that almost no energy leaves (a design rule fixed before the final training). The median energy-conservation error is 7.4 × 10⁻⁵ of the exchanged energy. In the PCM family, a solver-convergence check, added after the first non-converged case was found, led to 34 corrected reruns with a different linear solver: 13 whose pressure solve had failed and 21 rerun under a pre-specified rule for warning cases. Another 39 cases with milder warnings were kept under the same rule; Section 5.2 shows that excluding them changes no conclusion. Both families are frozen in manifests that list every run with the md5 checksum of its file (Table 1).

Two tank runs, T0211 and T0052, carry a numerical-setting uncertainty of about 7 % of ΔT, found in the verification below. They are flagged in the release rather than removed.

## 2.5 Verification

Agreement limits for the tank were committed to the project repository before any comparison was run (pre-specified; Appendix A): for example, at most 1.5 % of ΔT in field RMSE between a test and a production solution, and at most 0.5 % in stored energy. Halving the mesh to 2.5 mm in four designs changes the field by 0.34 to 2.76 % of ΔT. The largest difference, in a laminar design, is of the same order as the response of that design to a 0.01 % change in inlet velocity (2.76 against 1.85 %): the unsteady solution itself moves that much, so the mesh effect cannot be separated from it, and we do not claim mesh convergence. Stored energy and thermocline position agree within their limits, with one borderline energy difference (0.96 %); the outlet temperature is borderline in some event windows (Appendix A). Doubling the outer iterations or halving the time step changed one low-Richardson SST discharge run (T0211) by 7.4 % of ΔT. Of 14 similar designs tested, one more (T0052) is affected under a rule added afterwards, and a pre-specified sample of ten found none (95 % interval 0 to 31 %), so the effect is not systematic across the regime; these two runs are the flags above. On the 588 SST runs, 60 % of wall cell-snapshots have a first-cell y⁺ below 5 (viscous sublayer) and 38.5 % lie in the buffer layer, a stated limitation at the highest Reynolds numbers. The 20 mm slots have four cells across the inlet, but their slot Reynolds number never exceeds 5,809; the highest Reynolds numbers (up to 24,008) occur with 80 mm slots, which have 16 cells. The highest-Reynolds run of each kind is repeated on the 2.5 mm mesh [PENDING].

**Sensitivity floor.** To measure how far the labels themselves move, 24 test-side runs, chosen by a fixed rule (two per closure in each of six Richardson-number bins), were rerun with the inlet velocity changed by 0.01 %. The SST runs are deterministic: their fields change by at most 0.06 % of ΔT. The laminar runs are not: their fields change by a median 3.0 % and up to 11.8 % of ΔT, most at Ri below 10 (Appendix A.4). In five of the twelve laminar runs this change equals or exceeds the field error of at least one hybrid canonical network. In such runs the label is one realisation of a sensitive unsteady flow, and no model can be expected to match it point by point more closely than the floor.

For PCM, refining from 0.5 to 0.25 mm in six designs delays melting by 1.0 to 8.7 %, always in the same direction: the 0.5 mm labels melt early [PENDING: a 60-case check at 0.25 mm, with every model rescored against the finer labels, is running]. Where three levels allow it (design G131), the grid convergence index [32] of the time to 99 % melting is 13.06 % on the medium and 7.50 % on the fine grid (observed order 0.741). This bias is stated in the dataset card so that users can judge model differences smaller than it.

# 3. Validation against experiments

## 3.1 Tank: a buoyant jet in a real tank (Lou et al.)

No quasi-two-dimensional tank-charging experiment with field data was found, so the SST set-up of the tank family (same solver, closure, buoyancy source and properties) was tested in three dimensions against the PIV and temperature measurements of Lou et al. [33] (Fig. 2a, b). Over 14 times, the simulated jet penetration h_j stays within 9 mm of the mean of the two PIV tests up to 450 s (mean −2.9 mm over 50 to 300 s) but runs 7 to 13 mm deeper than both tests after 500 s (mean +10.8 mm); Lou et al.'s own CFD was 29.7 mm too shallow on average.

For the outlet temperature, the published curve is given as an outlet-based bulk Richardson number Ri_bulk, proportional to β(T)(T_in − T_out), and its conversion back to temperature needs an assumption about the thermal expansion coefficient β that the paper does not state. With constant β in the reconstruction of Lou et al.'s experimental outlet curve, the 10 % breakthrough occurred at t* = 0.806 in the simulation and 0.796 in the experiment. The simulated outlet then warmed more rapidly, reaching 50 % at t* = 0.932, compared with approximately 0.97 to 1.045 under the two β assumptions examined. Over t* = 0.95 to 1.45, the simulated outlet was approximately 0.08 to 0.20 warmer in normalised temperature. Heat loss from the uninsulated experimental tank is consistent with the direction of this discrepancy; its contribution cannot be isolated from the published measurements. The reported charging efficiency, which needs no β assumption, points the same way: 0.750 in the experiment against 0.919 from the simulation's port energy balance at t* = 1.0 (Appendix B). This tests the SST solver set-up against a three-dimensional experiment; it does not validate the two-dimensional labels directly, and the laminar closure and discharge are not validated against experiment (no suitable tank experiment was found).

## 3.2 PCM: plain, finned and tilted walls

For the plain wall of Kamkari and Shokouhmand [31], the model at the dataset settings stays within ±0.06 in liquid fraction and melts fully at 194.7 min against about 195 min measured (Fig. 2c). This agreement is partly by construction, because the same experiment set the lauric-acid mushy constant, and it may partly reflect cancellation between the early melting of the 0.5 mm mesh and model error. With one and three fins the model melts about 0.1 too fast during the first hour and then approaches the experiment; the one-fin full-melting time matches (161 against about 160 min) and the three-fin case melts 8 % early. The tilted cases of the same group [34] (inclination 45° and heating from below, their θ = 45° and 0°), run at the dataset settings, agree within ±0.10 in liquid fraction (mean absolute difference 0.055 and 0.037), but full melting comes late: 147 against about 122 min at 45° (+20 %) and 103 against about 92 min from below (+12 %). For Vogel and Thess [30], our run matches their two-dimensional model within the ±0.02 digitising accuracy (mean absolute difference 0.009) and the experiment with a mean absolute difference of 0.030 (Fig. 2d). The remaining finned-wall difference combines residual discretisation, properties, boundary conditions, experimental uncertainty and model form, which these runs do not separate; the three-dimensional front and back walls of the experiment, which damp convection near the fins, are one candidate.

# 4. Benchmark tasks, splits, metrics and models

## 4.1 Tasks

Tank: given the design inputs (geometry, operation, temperatures, initial state, closure) and a dimensionless time t* = tQ/V, predict the normalised temperature field θ = (T − T_c)/(T_h − T_c) on the native grid. PCM: given the design inputs and τ = t/t_ref, predict the normalised temperature θ = (T − T_0)/(T_w − T_0), with T_w the wall and T_0 the initial temperature, and the liquid-fraction field. Here t_ref is an a priori melting time computed from the inputs only (energy over a laminar Nu ~ Ra^0.25 heat rate), so the true melting time is never an input. Both tasks query any time directly; an autoregressive rollout task is not part of this release.

## 4.2 Splits

Splits are assigned by design point, so laminar and SST twins of one design are never divided between training and test, and they are fixed by parameters or a hash of the case identifier (Fig. 1c). The tank has a random split (10 % of design points) and three out-of-distribution splits: unseen widths outside 0.33 to 0.93 m (the tails of one geometry family, not new geometry families), discharge (all discharging runs, training on charging only, an operating mode never seen), and faster inflow (Reynolds number above the design 90th percentile; all of its test runs are SST, so it tests Reynolds extrapolation and closure together). The PCM family has a random split and five out-of-distribution splits: held-out fin counts (4 and 5 fins, training on 0 to 3), stronger heating (superheat above the 90th percentile), unseen tilt (45° and heating from below, training on side heating), and material transfer in both directions (lauric acid tested after training on n-octadecane, and the reverse).

## 4.3 Metrics

The primary metric is the temperature-field RMSE (tank in % of ΔT, PCM in K). Engineering metrics are scored alongside it: the horizontally averaged vertical profile, the thermocline midpoint (with the share of snapshots where it is undefined reported separately), stored energy as a fraction of full charge, and the near-outlet temperature for the tank; liquid-fraction RMSE, liquid-region overlap, stored energy, and the time to 90 % melting (t90) for PCM. The t90 error is conditional on the prediction reaching 90 % within a fixed input-only horizon (τ ≤ 3), so the share of runs that reach it is always reported with it. Two metrics are proxies (Appendix I). Stored energy uses constant ρc_p, for which a model's real-property energy error equals its proxy error within ±1 %. The outlet metric is the area-averaged temperature of the cells next to the outlet; it differs from the flow-weighted (mixing-cup) outlet temperature by a median 0.6 % of ΔT but by up to about 30 % in some very-high-Ri laminar runs, so we call it the near-outlet temperature, and the main outlet comparison is repeated with the flow-weighted temperature (Section 5.1, Appendix G).

## 4.4 Baselines and neural models

Baselines span physics and interpolation: the initial field, a one-dimensional ideal stratification model (plug flow with a sharp interface), a calibrated multi-node one-dimensional model with Richardson-dependent inlet mixing whose protocol was fixed before any test score (four parameters fitted per closure by a limited search, so a reasonable rather than an optimal 1D model; Appendix G), and interpolation in standardised parameter space: k-nearest neighbours (k = 5), inverse-distance weighting (IDW; 8 neighbours, weights 1/d²) and radial basis functions (thin-plate spline over 40 neighbours). For PCM there are also a conduction model (the exact two-phase Stefan solution [35]) and a front model that follows the Stefan solution early and then a melt fraction growing linearly in τ with a slope fitted on the training runs. Two practitioner baselines, added after the external review with settings fixed before scoring, predict from the same design inputs and time as the networks: scalar regressors (gradient boosting, and a Gaussian process with automatic relevance determination), one per scalar quantity (tank stored energy, near-outlet temperature and thermocline midpoint; PCM melted fraction and t90), and a field model that regresses 32 proper-orthogonal-decomposition (POD) coefficients of the training fields with gradient boosting (Appendix D).

The neural models are the Fourier neural operator (FNO) [36] and the U-Net convolutional network [37], co-equal baselines with no "main" model, each in up to four variants. *Hybrid* variants learn the correction to a physics base (ideal stratification for the tank, the front model for PCM). *Canonical* variants (tank only) map a discharge run into the charge frame by a 180° rotation with hot and cold exchanged (θ → 1 − θ) and map the prediction back before scoring; this symmetry is exact under the Boussinesq approximation and approximate with real water properties. Building symmetries into networks for fluids is established [38,39,40,41]; we found no prior use of the charge/discharge symmetry in machine learning for storage. A transformer operator, a 4 × 4-patch variant of Transolver [42], was added for PCM after the main results, under a plan fixed before training; it was not run on the tank because a pre-set check (fitting eight training samples to a masked RMSE of 0.01) failed narrowly (0.012), an implementation and resource decision rather than evidence about generalisation. Each network is trained with three seeds, at batch 16 with AdamW and a one-cycle schedule, for 60 epochs (FNO, Transolver) or 100 (U-Net). Learning rates were not tuned for FNO and U-Net, and their epoch counts follow one fixed protocol for both families (the same for all splits); only Transolver's learning rate was chosen, between two values, on validation loss. Inputs, grids and masks are listed in Appendix D (Table D.1).

# 5. Results

## 5.1 Tank

Table 2 gives the field error of every model on the four tank splits, and Table 3 the engineering metrics.

[[TABLE2]]

[[TABLE3]]

**Surrogates against physics and interpolation.** On random, unseen-width and discharge test runs, the hybrid canonical networks reach 3.6 to 6.2 % of ΔT, against 7.1 to 7.6 % for the calibrated multi-node model, 8.7 to 10.8 % for the best interpolation (where it works at all) and 15 to 17 % for ideal stratification. Across the four splits, both hybrid-canonical surrogates reduced vertical-profile error by 3.5 to 4.1 percentage points of ΔT and thermocline-midpoint error by 6.0 to 19.1 mm relative to the calibrated multi-node model (run-level means, Table 3 and Table G.1; the design-level intervals of Appendix E average runs per design first, so their means differ slightly). Faster inflow is the hardest split for the hybrid canonical networks (9.2 and 9.8 %) and for the one-dimensional models.

**For the networks, discharge requires the symmetry** (Fig. 3a). Trained on charging only, the plain networks fail on discharge (65 to 67 %, as poor as interpolation), and the hybrid networks without the frame reach 13 %, between ideal stratification (16.5 %) and the multi-node model (7.6 %), which transfers to discharge without any special treatment. The canonical frame alone brings FNO to 12.4 % and U-Net to 9.9 %, and with the hybrid base both reach about 4.4 %, the same level as on charging. The gap of the frame alone has one cause. On discharge runs that start uniform, the frame alone already reaches charge-level error (FNO 4.5 %, U-Net 4.2 %); the failure is confined to the pre-stratified runs (31.9 and 23.8 %). Our frame mirrors the initial field of such a run, which moves its interface to height 1 − y_i, but left the interface-height input y_i unchanged, so these runs received contradictory inputs. No other input leaves the training range (log Re for 0.6 % of the runs, by 0.18 standard deviations), and the parameter-space distances of discharge test runs to the training runs are like those of charge validation runs. The hybrid base supplies the correct initial field and is insensitive to this input (4.0 to 4.6 % for both start types). Retraining the frame-only networks with y_i mirrored, and a ceiling trained with half of the discharge designs, test this explanation [PENDING]. A pre-specified analysis on the 215 discharge designs with no identified exposure before the models were frozen supported the gain of adding the frame to the hybrid model: 9.2 percentage points for FNO and 9.7 for U-Net (Holm-adjusted p = 0.0004 each). These runs were part of the discharge result already reported, so this is a pre-specified subset analysis, not a prospective confirmation (Appendix E).

**Where the networks fail** (Fig. 3b). Error grows as the jet overcomes stratification (Spearman correlation with the bulk Richardson number −0.84 for FNO). All 80 test cases (run-split pairs) above 10 % for the FNO hybrid canonical model are SST runs with Ri below 9.5, where large coherent eddies and wall short-circuits are smoothed out. U-Net has the same regime dependence plus a second failure: 17 of its 18 laminar cases above 10 % are the widest unseen tanks (W > 0.93 m), which accounts for most of its higher error on unseen widths (6.2 against 4.4 % for FNO). No architecture wins everywhere: U-Net variants lead on random and faster inflow, FNO on unseen widths, and on discharge U-Net is ahead by 0.13 percentage points [0.01, 0.24]. Nor is one variant best: the hybrid canonical combination is clearly best only on discharge; the canonical-only models are slightly better on random and faster inflow, and for U-Net on unseen widths the hybrid or canonical model alone beats the combination (design-level intervals, Appendix E). The two flagged runs (Section 2.4) lie in this regime; replacing their labels by alternative CFD references changes the ensemble error by at most 0.43 percentage points and keeps the model ordering (Appendix C).

**The 1D model matches the surrogates at the outlet** (Fig. 5b). For the near-outlet temperature, the multi-node model has lower error than both surrogates on discharge (by 0.17 and 0.31 K) and faster inflow, with paired intervals excluding zero, and a lower mean than U-Net on unseen widths (Table 3). Because the near-outlet temperature is an area average, all models were rescored on the flow-weighted (mixing-cup) outlet temperature, weighting each outlet cell of a prediction by the CFD outflow velocity in that cell. The multi-node advantage then holds for U-Net on discharge (0.31 K [0.11, 0.53]) and for FNO on faster inflow (0.19 K [0.08, 0.30]) but is not resolved for FNO on discharge (0.15 K [−0.004, 0.32]) or U-Net on faster inflow (0.04 K [−0.09, 0.16]) (design-level intervals, Appendix G). For the delivered outlet temperature, the calibrated one-dimensional model is therefore as good as the field surrogates on these splits, at 0.05 s per case. The surrogates remain better on thermocline position on every split, and on stored energy except U-Net on unseen widths. The benefit of full-field prediction therefore depends on which thermal quantity is required.

**Scalar regressors and POD.** For single quantities, regressors on the design inputs are strong within the design range. A Gaussian process predicts stored energy to 0.49 % of full charge, the near-outlet temperature to 0.85 K and the midpoint to 12.0 mm on the random split, against 0.38 %, 0.67 K and 6.0 mm for hybrid canonical U-Net and 0.55 %, 0.83 K and 12.7 mm for the multi-node model; on unseen widths and faster inflow the best scalar regressor is within 0.11 K of the multi-node model at the outlet. Without the symmetry, all regressors fail on discharge (stored-energy error 36 to 53 % of full charge). The POD field model reaches 11.0 to 15.1 % of ΔT on random, unseen widths and faster inflow, no better than interpolation and about three times the networks' error on random and unseen widths, and 63 % on discharge.

## 5.2 PCM

Table 4 gives the field and melt-time errors of every model on the six PCM splits.

[[TABLE4]]

**The ranking changes with the generalisation task.** Across the random, fin-count, heating, and orientation splits, all neural variants had lower mean temperature-field RMSE than IDW. The best neural model has 2.8 to 4.3 times lower field error than IDW (2.8 to 3.8 times lower than the best baseline of each split) on random, held-out fins and stronger heating. Unseen tilt is a second open problem: every network reaches only 6.2 to 7.1 K against 7.7 K for IDW and the front model, about 8 to 11 times its own error on the random split. The ordering reversed for transfer between n-octadecane and lauric acid in either direction (Fig. 4). Against hybrid U-Net, IDW's mean advantage was 0.26 K [0.10, 0.43] on held-out lauric acid and 3.94 K [3.67, 4.21] on held-out n-octadecane (95 % intervals over test runs, seed means fixed; Appendix E). Individual training seeds reversed the first comparison: two of the three hybrid U-Net seeds beat IDW on lauric acid. With a seed spread of 1.38 K, five times the 0.26 K gap, and a label uncertainty of similar size (Section 6), no neural model beats interpolation on held-out lauric acid, but IDW is not shown to be better either; the interval above holds the seed means fixed and does not cover retraining [PENDING: two further seeds on both material splits, under a wording rule fixed before their results]. On n-octadecane, IDW beats every seed of every model, and several networks rarely predict near-complete melting: only 2.0 % (Transolver) and 33 % (FNO) of their predictions reach 90 % melting within the horizon, against 100 % for hybrid U-Net. These results identify material transfer, particularly prediction of n-octadecane after training on lauric acid, as a limitation of the evaluated surrogates. The standard deviation of field RMSE across the three training seeds is large on these splits (FNO 8.7 and 9.6 K), so single-seed rankings there would not be reliable.

**A third architecture shares the limitation.** The Transolver baseline lies between U-Net and FNO in field error within a material and gives no geometry advantage on tilt or fins. IDW had lower field RMSE than every seed of both Transolver variants in both transfer directions, so the material-transfer limitation holds for all three evaluated architectures.

**Field accuracy and melt time rank models differently** (Fig. 5a). On held-out fin counts, plain U-Net has the lower field RMSE (1.76 against 2.31 K) but plain Transolver the lower t90 error (5.6 against 10.2 %, a paired reduction of 4.69 percentage points [3.43, 6.01]). All 139 runs reach t90 in every seed, so this is not an effect of dropped runs. Within a material, Transolver gives the lowest melt-time error on random, fins and stronger heating (0.7 to 0.8, 5.6 and 1.0 to 1.1 %), although on stronger heating the plain-against-plain difference from U-Net is within its paired interval. On held-out n-octadecane, the front model has the lowest t90 error of the original models (17.6 %, all runs reaching t90).

**Low-dimensional models transfer better between materials.** For melt time alone, a Gaussian process on the design inputs predicts t90 within 1.2 % (random) and 1.6 % (stronger heating), close to the best networks (0.7 and 1.0 %), but not on held-out fins (10.7 against 5.6 %) or unseen tilt (gradient boosting 22.7 against 13.5 %). Under material transfer, gradient boosting gives the lowest t90 error of all models: 11.6 % on held-out lauric acid (IDW 16.9 %, best network 23.7 %) and 13.4 % on held-out n-octadecane (front model 17.6 %). The POD field model, weak within a material (3.25 K on random against 0.59 K for U-Net), is the most accurate field model on held-out lauric acid (3.87 K against 5.35 K for IDW and 5.61 K for the best network) and second to IDW on held-out n-octadecane (3.78 against 3.55 K). Material transfer is an extrapolation in the property inputs (Appendix D, Table D.1), and the networks handle it worst of all model types.

**Solver warnings do not matter.** Removing the 39 retained solver-warning cases from scoring changes neural field RMSE by at most 0.10 K and baseline RMSE by at most 0.60 K, and changes no neural ordering or conclusion.

## 5.3 Reproducibility and cost

Every released checkpoint was taken from the machine that produced its stored score and rescored from the frozen data. All 96 tank checkpoints reproduce their 19,704 stored per-run field scores exactly, and all 108 PCM checkpoints their 16,056 per-run scores on every compared metric. PCM rescoring on the original training workers reproduced all compared finite metric values exactly; in a six-checkpoint laptop spot check, the largest observed cross-GPU discrepancy in per-run field RMSE was 1.6 × 10⁻⁴ K (Appendix H). One released tank checkpoint had come from an earlier attempt of the same job; the audit found and replaced it, and no reported number changed.

A three-seed tank prediction (the 120 snapshots after t = 0) takes a median 1.45 s on a laptop RTX 4060 with the model loaded, against a median 2.64 h of single-core CFD: a latency ratio of about 6,500. The hardware differs, so this is not an equal-cost comparison. Generating the tank runs took an estimated 3,200 core-hours (median run time times the number of runs) and the PCM runs about 3,100 core-hours [TO CHECK: planned estimate; replace by the measured total]; training all 96 tank networks took 146.6 GPU-hours. Fig. 6 shows typical predictions, chosen as the median-error test run of each family.

# 6. Discussion: what the benchmark tests and what it does not

**Scope of the labels.** The fields are two-dimensional with adiabatic walls. They test surrogates on realistic buoyant transients; they are not a design tool for a specific three-dimensional tank. The labels are themselves approximate. Tank mesh differences reach 2.76 % of ΔT against best model errors of 3.5 to 4.5 %, and laminar tank runs respond to a 0.01 % inlet change by up to 11.8 % of ΔT, as much as the network error in some runs (Section 2.5). PCM fields at 0.5 and 0.25 mm differ by 4.2 to 7.6 % of ΔT (1.3 to 2.3 K at a typical ΔT of 30 K), more than the best within-material PCM errors (0.59 to 1.76 K); the PCM labels also melt early by up to 8.7 %. Within-material scores therefore measure agreement with the 0.5 mm reference solutions rather than with the physical process, and model differences smaller than these label uncertainties should not be over-interpreted. Scoring the tank models against alternative CFD references did not change their ranking (Appendix C).

**Scope of the splits and physics.** Unseen widths are the tails of one rectangular geometry family; faster inflow mixes Reynolds-number extrapolation with the closure; discharge relies on an approximate symmetry; and material transfer involves two materials only, so it is transfer between them, not to a third. The PCM family covers melting only, without solidification or cycling, with constant properties, no volume change and a single cell height; fin counts above three appear only in the fin-count test, while the fin validation covers up to three fins. Heating from below at Ra_H up to 9 × 10⁸ is modelled as laminar at 0.5 mm. The tank has 2D slot ports and a fixed height of 1 m.

**Uncertainty.** For the FNO hybrid canonical ensemble, the spread of three seeds ranks the error well (Spearman 0.82 to 0.94 on the tank splits), and an error bound calibrated on validation runs holds close to its stated rate in distribution, for unseen widths and for faster inflow (88 to 91 % at a nominal 90 %), but under-covers on discharge (71 %; Appendix F). For a mode never seen in training, the seed spread is not a reliable warning.

**How to use the benchmark.** We recommend reporting results per seed and not only means, reporting the share of runs that reach t90 next to the t90 error, and reporting the flagged tank runs separately. The test splits are fixed; validation data come from the training side of each split.

**What we do not claim.** We do not claim mesh convergence, three-dimensional validity of the two-dimensional labels, that any architecture is best overall, that the seed spread is reliable for an unseen operating mode, or novelty of building symmetries into neural networks. The networks were trained with untuned learning rates and one epoch protocol; tuned networks may do better, which the fixed splits allow others to test.

# 7. Conclusions

ThermalStorageBench provides 1,712 quality-controlled transient CFD simulations of sensible and latent thermal storage, with verification on representative designs, with fixed splits, engineering metrics, baselines and reproducible checkpoints. Applying it shows that neural models are clearly better than interpolation and one-dimensional models within a material on field and profile metrics, that a simple change of frame from the charge/discharge symmetry lets the networks predict discharge from charging data, and that the preferred model depends on the quantity needed: a calibrated one-dimensional model is as good at the delivered outlet temperature, and a scalar regressor is competitive for melt time. It also shows two open problems for the evaluated networks: an unseen cell orientation, and a change of PCM material, where no network beats interpolation and low-dimensional regressors on the design inputs are the most accurate models. The data, code, splits and checkpoints are released so that new models can be compared on equal terms.

# Appendix A. Verification

## A.1 Pre-specified limits (tank)

The limits below were committed to the project repository (6 November 2026, after training and before any comparison existed; the commit history is released). A value between the two columns is borderline and is never reported as agreement; a quantity that passes over the whole run but exceeds its limit in any event window (before, around or after the outlet event) is borderline. The perturbation run (inlet velocity × 1.0001) measures the physical sensitivity of the unsteady solution and is never treated as a numerical noise floor; its size is reported as the sensitivity floor of the labels (Section 2.5, Appendix A.4). An observed order or grid convergence index (GCI) is reported only if three levels converge monotonically with an observed order between 0.5 and 3.

**Table A.1. Pre-specified agreement limits, test against production solution.**

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

**Table A.2. Tank mesh (2.5 against 5 mm) and setting tests, field RMSE in % of ΔT against the production run.** Slot: inlet slot height (cells across it at 5 mm). rep: inlet × 1.0001; n4: four outer correctors; co25: maximum Courant number 0.25.

| Design | Slot, mm (cells) | Re, Ri | Mesh 2.5 mm | rep | n4 | co25 |
|---|---|---|---|---|---|---|
| T0408, laminar | 40 (8) | 2,014, 31 | 0.34 | ~0 | ~0 | ~0 |
| T0221, laminar | 20 (4) | 678, 386 | 0.60 | 0.39 | 0.39 | 0.38 |
| T0243, SST | 70 (14) | 18,626, 5.8 | 1.70 | ≤ 0.11 | ≤ 0.11 | ≤ 0.11 |
| T0551, laminar | 20 (4) | 1,259, 55 | 2.76 | 1.85 | 2.14 | 1.96 |
| T0393, laminar | 70 (14) | 600, 5,980 | | 0.50 | 0.67 | 0.78 |
| T0211, SST, discharge | 20 (4) | 5,396, 3.9 | | 0.47 | 7.38 | 7.32 |
| T0052, SST | 40 (8) | 4,725, 3.6 | | 1.68 | 6.77 | |
| T0156, SST, discharge | 40 (8) | 6,507, 4.0 | | 3.84 | 1.80 | |
| T0851, SST (highest Re, 20 mm slot) | 20 (4) | 5,809, 6.0 | [PENDING] | | | |
| T0915, SST (highest Re overall) | 80 (16) | 24,008, 4.1 | [PENDING] | | | |

Stored energy and thermocline position agree within their limits except one borderline energy difference (T0243, 0.96 %). The outlet temperature is borderline in the event window of T0408 (2.03 %) and in every variant of T0393 (2.85 to 3.40 %, the perturbation run included); T0052 with four outer correctors differs by 1.08 % in energy and 5.44 % in outlet temperature. In T0551 the mesh difference (2.76 %) is of the same order as the response to the 0.01 % inlet perturbation (1.85 %), so the two cannot be separated in that design. In T0243 the mesh difference lies on the thermocline interface and grows with time. A 10 mm grid does not converge monotonically with the other two levels, so no order or GCI is reported, and the 5 mm mesh is not called converged.

T0211 shows a numerical-setting dependence: n4 and co25 differ from the production run by 7.4 % but from each other by 2.49 %, so neither is shown to be converged, while the perturbation moves it by only 0.47 %. The difference is a phase error in the tilting of the thermocline after the cold jet reaches it. Two pre-specified tests asked whether this is a regime. The four nearest SST designs in (log Re, log Ri) gave no affected design under the first rule; T0052 missed it narrowly and is counted as affected under a ratio rule added afterwards (labelled post hoc). A second sample of ten wide, low-Ri SST designs, drawn by a fixed rule before any run, gave 0 of 10 affected (95 % interval 0 to 31 %), with all differences at most 0.05 % of ΔT. T0211 and T0052 are flagged (Appendix C); T0156, T0551 and T0393 are listed as sensitive.

Across the 192 design points run with both closures, laminar and SST fields differ by a median 3.9 % of ΔT (10th to 90th percentile 0.7 to 8.3 %), governed by stratification (Spearman correlation with Ri −0.62) rather than Reynolds number (+0.12). In the 588 SST runs, 60 % of wall cell-snapshots have y⁺ below 5, 38.5 % lie in the buffer layer and 1.6 % above 30.

## A.3 PCM mesh, time step and solver

In six dataset cases compared at 0.5 and 0.25 mm, the time to 99 % melting (t99) is 1.0 to 8.7 % later on the finer mesh (median 4.9 %), always in the same direction. Melt curves agree within 0.036 in liquid fraction; the field differs by 4.2 to 7.6 % of ΔT, mostly in a band around the melt front. For case G131 (lauric acid, no fins; 1.0, 0.5 and 0.25 mm), the dense liquid-fraction series gives an observed order of 0.741 and a GCI of 13.06 % on the 0.5 mm and 7.50 % on the 0.25 mm grid; the 0.5 mm run melts about 9.5 % before the extrapolated t99. The time step is Courant-limited and halves with the mesh, so this is a combined space-time refinement. Case G301 (n-octadecane) has an observed order outside 0.5 to 3, so no GCI is given; its 0.5 mm run melts 6.76 % earlier than the 0.25 mm run.

The pressure solve failed to converge in some cases (the first was P0124). A solver-convergence check was added; the 13 failed cases were rerun with a preconditioned conjugate-gradient solver, which changed the melt time by −2.1 to +0.9 % in the four cases compared. A pre-specified test reran the two most severe warning cases of each of three kinds (six cases); one kind changed materially (P0075, 2.54 % of ΔT), so all 17 cases of that kind were rerun. Together these are the 34 corrected reruns (13 failed, 6 tested and 15 further cases of the changed kind), and the 39 cases of the other two kinds were kept (sensitivity in Appendix C).

## A.4 Sensitivity floor of the tank labels

The 24 runs were drawn before any rerun from the test-side runs of the four splits that are not flagged and whose rerun was predicted to take at most 18 h: six equal-count bins of log Ri, two laminar and two SST runs per bin, in a fixed hash order. Each was rerun with the inlet velocity × 1.0001 and compared with the dataset run by the same procedure as Table A.2. Network errors are the seed means of the hybrid canonical models on the splits where the run is a test run.

**Table A.4. Field and stored-energy change for a 0.01 % inlet change, against the network field error, all in % of ΔT.**

| Run | Ri | Closure | Field change | Energy change | FNO hybrid canonical | U-Net hybrid canonical |
|---|---|---|---|---|---|---|
| T0524_sst | 0.8 | SST | 0.01 | 0.01 | 24.56 | 26.31 |
| T0019_sst | 2.9 | SST | 0.02 | 0.01 | 11.61 | 10.41 |
| T0336_lam | 4.2 | laminar | 11.84 | 1.44 | 9.86 | 9.01 |
| T0180_lam | 4.5 | laminar | 7.88 | 1.63 | 9.24 | 9.39 |
| T0992_sst | 7.5 | SST | 0.01 | 0.01 | 4.72 | 4.39 |
| T0496_lam | 8.2 | laminar | 0.07 | 0.02 | 5.33 | 5.08 |
| T0672_lam | 8.5 | laminar | 9.65 | 1.99 | 8.41 | 8.58 |
| T0228_sst | 8.8 | SST | 0.04 | 0.01 | 7.53 | 14.02 |
| T0984_sst | 38.5 | SST | 0.02 | 0.01 | 3.06 | 2.93 |
| T0194_lam | 41.8 | laminar | 2.74 | 0.16 | 3.67 | 3.68 |
| T0810_lam | 45.8 | laminar | 0.00 | 0.00 | 3.63 | 4.71 |
| T0626_sst | 50.0 | SST | 0.02 | 0.01 | 4.19 | 4.05 |
| T0975_sst | 65.3 | SST | 0.04 | 0.01 | 3.00 | 3.07 |
| T0306_lam | 76.7 | laminar | 4.01 | 0.32 | 3.32 | 3.11 |
| T0999_sst | 128.0 | SST | 0.01 | 0.01 | 2.63 | 2.29 |
| T0119_lam | 154.0 | laminar | 0.25 | 0.02 | 2.36 | 2.19 |
| T0733_sst | 224.2 | SST | 0.03 | 0.01 | 3.02 | 6.08 |
| T0189_lam | 233.6 | laminar | 3.18 | 0.14 | 3.31 | 3.13 |
| T1021_lam | 251.9 | laminar | 5.06 | 0.27 | 5.36 | 5.02 |
| T0085_sst | 536.3 | SST | 0.06 | 0.01 | 2.54 | 7.27 |
| T0821_sst | 754.9 | SST | 0.05 | 0.01 | 2.01 | 1.92 |
| T0645_sst | 856.4 | SST | 0.03 | 0.01 | 2.33 | 1.91 |
| T0369_lam | 1,448.4 | laminar | 0.32 | 0.02 | 1.88 | 1.46 |
| T0665_lam | 2,338.4 | laminar | 0.24 | 0.06 | 1.30 | 0.96 |

The SST runs change by at most 0.06 % and the laminar runs by a median 3.0 % (up to 11.8 %), with no monotonic trend in Ri across the whole range (Spearman 0.13). Stored energy changes by at most 2.0 % of full charge, so the integral quantities are far less sensitive than the field.

# Appendix B. Lou et al. tank details

**Case.** The three-dimensional run uses quarter symmetry (230,156 cells), buoyantPimpleFoam with k-ω SST and the same buoyancy source term as the dataset runs (OpenFOAM's buoyancyTurbSource in the compressible solver), real water properties and a maximum Courant number of 2, with baffle-hole open areas within 1 % of the target. It ran to 750 s for the jet comparison and was extended to 1,275 s (t* = 1.507) for the outlet. h_j is taken as the distance from the inlet port to the point on the centreline where the vertical velocity changes sign, averaged over ±6.25 s as in the PIV.

**Jet depth.** Against the mean of the two PIV tests over 14 times, the difference is −2.9 mm (50 to 300 s), −0.9 mm (350 to 450 s) and +10.8 mm (500 to 700 s). After 500 s the simulated jet is deeper than both tests separately, and it penetrates about 19 % faster than the PIV (0.180 against 0.151 mm/s, linear fits). The spread between the two PIV tests indicates repeatability and is not an uncertainty band. Refining the lower baffle region changed h_j by at most 0.1 mm up to 300 s.

**Outlet reconstruction.** The experimental outlet curve (Fig. 15a of [33], uniform baffle, 1 L/min, 333.15 K into 293.15 K) was digitised by curve colour from the publisher's image (about ±0.01). Because Ri_bulk is proportional to β(T)(T_in − T_out), it was converted back to T*_out in two ways: with constant β, T*_out = 1 − Ri/Ri_0 with Ri_0 the plateau before breakthrough; and with β evaluated at the mean of inlet and outlet temperature, solving for T_out. The second reconstruction crosses T* = 0.1 at about t* = 0.77 (interpolated across a gap in the digitised curve between t* = 0.768 and 0.788). Evaluating β at the outlet temperature gives two roots near the plateau and was not used.

**Charging efficiency.** The simulated σ(t*) is the integral of (1 − T*_out) over t*, the port energy balance at constant ρc_p. The published σ rises with a slope of 0.81 on the pre-breakthrough plateau, where a loss-free and perfectly measured tank gives 1.0, and stays below the simulation (0.750 against 0.919 at t* = 1.0; 0.850 against 0.985 at t* = 1.5). This supports a heat-loss explanation in sign, without separating wall loss, mixing and measurement.

# Appendix C. Label flags, alternative references and solver warnings

**Flags.** T0211_sst and T0052_sst carry a numerical-setting uncertainty of 7.4 and 6.8 % of ΔT (Appendix A.2) and are flagged in the release's label-flag file; both are test runs (discharge and unseen width).

**Alternative references.** All held-out tank runs with an alternative CFD solution (18 runs, 23 run-split rows; nothing selected) were scored against each alternative with the same frozen predictions of the two hybrid canonical models. Across the four references (2.5 mm mesh, n4, co25, perturbation), the ensemble field error changes by at most 0.54 percentage points in any row and by at most 0.43 percentage points for the flagged runs; the mean FNO minus U-Net gap changes by at most 0.04 percentage points. One of 64 ensemble comparisons flips the ranking (T0221_lam against the 2.5 mm reference, where the two models differ by 0.11). Similar scalar errors against two CFD references cannot show how much error the two references share with the true solution.

**PCM solver warnings.** The 39 retained warning cases fall into the test sets as random 3, held-out fins 15, stronger heating 4, held-out lauric acid 24, held-out n-octadecane 15 and unseen tilt 11. Removing them from scoring changes neural field RMSE by at most 0.10 K and baseline RMSE by at most 0.60 K. The ordering of the neural models is unchanged on every split and metric, and every neural-against-baseline conclusion is unchanged. This tests exclusion from scoring, not retraining without these cases.

# Appendix D. Models and training

**Architectures.** FNO: four Fourier layers, width 32, 16 retained modes in each direction, with pointwise skips (4.2 M real-valued parameters, counting each complex spectral weight as two). U-Net: four levels, base width 32 (7.8 M). The counts are the same for both families (from the released checkpoints). Transolver (PCM only): six layers of physics attention, width 128, 8 heads, 32 slices, on 4 × 4-cell patch tokens embedded by a patch convolution and decoded to their 16 cells (1.16 M). FNO and Transolver add two normalised coordinate channels internally; U-Net does not.

**Inputs, grids and masks (Table D.1).** Every network gets the same input channels. Each scalar parameter is standardised with the mean and standard deviation of the split's training runs and broadcast as a constant channel; a parameter that never varies in training (the discharge flag on the discharge split, the material flag on the material splits) keeps unit scale, so its test value is seen for the first time. Domains of different width are left-aligned and zero-padded to the widest domain (tank 1.0 m, 200 cells; PCM 60 mm, 120 cells), with a mask channel; the training loss and all scores use only the cells inside the domain, and in the PCM cell the fins are marked by their own mask. The interpolation baselines take the neighbours in standardised parameter space, use each neighbour's snapshot nearest in t* or τ, stretch it linearly in x to the query width, and average with the method's weights; a neighbour with a different fin layout therefore contributes a blended fin pattern. Material properties enter the PCM networks only through the material flag and the property-dependent groups (Ra, Ste, Pr, t_ref), so material transfer is an extrapolation in these inputs: held-out lauric acid has Pr about 97, outside the n-octadecane training range (about 37 to 50).

**Table D.1. Network inputs.** All parameters are standardised on the training runs.

| | Tank | PCM |
|---|---|---|
| Field channels | initial θ field; domain mask; inlet-cell map; outlet-cell map | domain mask; PCM mask; fin mask; heated-wall map |
| Scalar parameters (13 each) | log inlet velocity; ΔT; cold temperature T_c; slot height; port offset; width W; inlet type B; discharge flag; pre-stratified flag; interface height y_i; log Re; log Ri; turbulent flag | material flag (lauric acid); superheat; subcooling; width W; number of fins; fin reach (length/W); fin thickness; sin and cos of tilt; log Ra_H; Ste; Pr; log t_ref |
| Time | t* = tQ/V | τ = t/t_ref |
| Hybrid variants | ideal-stratification θ field at t* | front-model θ and liquid-fraction fields at τ |
| Output | θ field | θ and liquid-fraction fields |

**Table D.2. PCM properties (constant).** Density and specific heat are means of solid and liquid values; viscosity is evaluated at T_m + (T_w − T_m)/2, so it varies with the wall superheat for n-octadecane.

| Property | n-octadecane [30] | Lauric acid [31] |
|---|---|---|
| Melting range, °C | 27.99 to 28.01 | 43.5 to 48.2 |
| Density, kg m⁻³ | 820.7 | 912.5 |
| Specific heat, J kg⁻¹ K⁻¹ | 2,078 | 2,285 |
| Conductivity, W m⁻¹ K⁻¹ | 0.151 | 0.140 |
| Dynamic viscosity, mPa s | 2.69 to 3.63 | 5.93 |
| Latent heat, kJ kg⁻¹ | 242.5 | 187.2 |
| Expansion coefficient, K⁻¹ | 8.9 × 10⁻⁴ | 8.2 × 10⁻⁴ |
| Prandtl number | 37 to 50 | 97 |
| Mushy-zone constant, kg m⁻³ s⁻¹ | 10⁶ | 5 × 10⁶ |

**Scalar and POD baselines.** Settings fixed before scoring: gradient boosting with 500 iterations and learning rate 0.05; a Gaussian process with a constant times anisotropic squared-exponential kernel plus white noise, fitted on 2,000 training rows drawn with a fixed seed; inputs as Table D.1 (scalar parameters and time) standardised on the training rows. The POD model uses 32 modes of at most 8,000 training snapshots (θ for the tank; θ and liquid fraction stacked for PCM), capturing 95 to 96 % (tank) and 89 to 91 % (PCM) of the variance about the mean, with one gradient-boosting model per coefficient. All are scored with the benchmark's metric code at the same snapshots as the networks; the scalar regressors are scored on their own quantities only. PCM POD field error, K: random 3.25, held-out fins 4.84, stronger heating 4.78, unseen tilt 7.19, held-out lauric acid 3.87, held-out n-octadecane 3.78.

**Training.** AdamW (weight decay 10⁻⁴) with a one-cycle schedule, peak learning rate 10⁻³ (3 × 10⁻⁴ for Transolver, chosen on validation loss only between 10⁻³ and 3 × 10⁻⁴: 0.0456 against 0.0473), batch 16, bfloat16 autocast, 60 epochs for FNO and Transolver and 100 for U-Net (U-Net was still improving between 60 and 100 epochs in a trial run). The checkpoint with the best validation loss is scored once on the test set. Each model is trained with seeds 0, 1 and 2. Tank test scores use every 10th snapshot, PCM every 5th. The epoch counts were fixed before the final training from pipeline trial runs on earlier subsets of the data (one with 629 tank runs); those trials recorded validation and test scores of preliminary models on those subsets, which we disclose. FNO hybrid canonical at 150 epochs was not better than at 60 on validation loss (0.0378 against 0.0374). Interpolation settings (k = 5; IDW with 8 neighbours and weights 1/d²; thin-plate-spline RBF over 40 neighbours) were set once and not tuned.

**Hybrid and canonical models.** A hybrid model predicts the correction to a physics base: the ideal-stratification field for the tank (plug flow with a sharp interface placed by the energy balance) and the conduction-then-convection front model for PCM. The canonical frame maps a discharge run to the charge frame by a 180° rotation and θ → 1 − θ, on input and back before scoring; the transform is its own inverse to 3 × 10⁻⁸.

**Transolver.** The plan, the analysis and the expectations were committed before training. Tokens of single cells cost 15 times FNO per step and fitted eight training samples no better, so 4 × 4 patches were used (amendment committed before any validation or test use). The tank was to be run only if the patch model fitted eight tank training samples to a masked RMSE of 0.01 within 1,600 steps; the best variant, with convolutional slice projections, reached 0.012, so the tank was not run. This is an implementation and resource decision; an eight-sample fit does not show how Transolver would generalise on tank data.

# Appendix E. Statistics

All intervals are descriptive 95 % percentile bootstrap intervals [43] (10,000 resamples). Neural scores are the per-run mean of three seeds.

**Tank, design level.** Runs are averaged per design, and designs are resampled. On the random split, hybrid canonical U-Net is better than hybrid canonical FNO by 0.41 percentage points [0.34, 0.48]; on unseen widths FNO is better (Table 2). Full tables are in the release.

**Discharge confirmation (pre-specified).** The protocol was committed before any subset score was computed. On the 259 discharge test runs from 215 designs with no identified exposure before the models were frozen, adding the canonical frame to the hybrid model improves field error by 9.17 percentage points [8.33, 10.02] (FNO; 96 % of designs) and 9.74 [8.84, 10.64] (U-Net; 95 %), and the hybrid canonical models beat ideal stratification by 12.53 and 12.61 percentage points. All four hypotheses are supported (Holm-adjusted p = 0.0004 each, the floor of the null-centred bootstrap). The subset was part of the discharge result already reported, so this is a pre-specified subset analysis, not a prospective confirmation.

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

On discharge, calibrated on charging only, the multi-node model has 7.58 % field error against 4.48 and 4.37 %, but lower near-outlet error by 0.17 K [0.02, 0.34] and 0.31 K [0.12, 0.52].

**Flow-weighted outlet.** Every prediction was also scored on the flow-weighted outlet temperature, Σ max(u_n, 0) θ / Σ max(u_n, 0) over the outlet cells, with u_n the outward velocity of the CFD label at the same snapshot, for prediction and label alike (volume-flux weighting; density varies by less than 1 %). Every scored snapshot has outflow. The multi-node model was refitted under its fixed protocol and gives the same near-outlet errors as Table G.1.

**Table G.2. Flow-weighted outlet temperature error, K (means), and paired difference to the multi-node model (positive: multi-node better), design-level 95 % intervals.**

| Split | Multi-node | FNO hybrid canonical | U-Net hybrid canonical |
|---|---|---|---|
| Random | 0.93 | 0.89 (−0.05 [−0.15, 0.05]) | 0.69 (−0.24 [−0.33, −0.16]) |
| Unseen width | 1.02 | 1.05 (0.02 [−0.08, 0.13]) | 2.06 (1.11 [0.74, 1.52]) |
| Discharge | 1.07 | 1.23 (0.15 [−0.004, 0.32]) | 1.38 (0.31 [0.11, 0.53]) |
| Faster inflow | 1.65 | 1.84 (0.19 [0.08, 0.30]) | 1.69 (0.04 [−0.09, 0.16]) |

Under the decision rule fixed before this rescoring (the near-outlet claim stays as stated only if both networks are worse on discharge and faster inflow with intervals excluding zero), the claim is weakened to the statement in Section 5.1. In the breakthrough window (snapshots where the label's flow-weighted θ has moved 10 to 90 % of its largest change) all errors are larger, and the multi-node advantage is resolved for U-Net on discharge and FNO on faster inflow.

# Appendix H. Reproducibility audit

Each released checkpoint was copied from the machine that trained it (the `sources` field of the merged results) and rescored from the frozen data with the unchanged evaluation code; the code was md5-identical on all machines. All 96 tank checkpoints reproduce their 19,704 stored per-run field scores exactly. One tank checkpoint first released had come from an earlier attempt of the same job on a machine that later failed; it was replaced with the correct file, which then reproduced exactly, and no reported number changed. All 108 PCM checkpoints, rescored on their training machines, reproduce all 16,056 per-run scores exactly on every compared metric. The only metric that can be undefined (t90 error) is undefined exactly when t90 is not reached, and the reached flag matched on every run, so the defined and undefined entries also match. In a six-checkpoint spot check on a different GPU model (laptop RTX 4060 against RTX 4070 Ti training), the largest per-run field RMSE difference was 1.6 × 10⁻⁴ K; checkpoints trained on the same GPU type reproduced exactly. All six training machines used Python 3.12.3, PyTorch 2.14.1 with CUDA 12.6 and OpenFOAM v2606. The repository's commit history, which dates every pre-specified plan and limit relative to the results, is released with the code.

# Appendix I. Metric definitions and proxies

**Tank.** Field RMSE is the mean over scored snapshots of the per-snapshot RMS difference of θ over the fluid cells, in % of ΔT. The profile metric uses horizontally averaged θ. Stored-energy error is the mean-θ difference as a fraction of a full charge; it is a constant-ρc_p proxy whose weight varies by 0.990 to 1.009 over the temperature range, so a model's real-property energy error equals its proxy error within ±1 %. The outlet metric is the area-averaged temperature of the cells next to the outlet; the flow-weighted alternative is defined in Appendix G. The area average differs from the flow-weighted (mixing-cup) outlet temperature by a median 0.62 % of ΔT over all snapshots and 2.3 % in the breakthrough window, and by up to about 30 % in some very-high-Ri laminar runs where a sharp thermocline crosses the outlet slot. The thermocline midpoint is the height where the horizontally averaged θ crosses 0.5; snapshots where the label has no crossing (median 2.5 % per run, up to 51 %) are excluded from the midpoint error and counted separately.

**PCM.** Field RMSE is in K over PCM cells. The t90 error is |t90,pred − t90,true| / t90,true, where the prediction is evaluated on a fixed input-only time grid up to τ = 3 and the reference t90 is interpolated between field snapshots; on all six test sets the reference matches the dense liquid-fraction series within 0.10 %. The t90 error is reported only for runs whose prediction reaches 0.9, together with the share that do. The energy metric covers sensible and latent energy in the PCM cells, normalised by their full-charge capacity, and excludes energy stored in the fins.

---

## Declarations

**CRediT authorship contribution statement.** [TO AGREE with all authors.] Saxam Bhattarai: Conceptualization, Methodology, Software, Investigation, Data curation, Formal analysis, Validation, Visualization, Writing: original draft. Bivek Baral: [roles]. Henrik Davidsson: [roles].

**Declaration of competing interest.** [TO CONFIRM] The authors declare no competing interests.

**Declaration of generative AI and AI-assisted technologies in the manuscript preparation process.** [TO AGREE with all authors; the journal requires this section.] During the preparation of this work the authors used Claude (Anthropic) to assist with code, data analysis and drafting of the text. After using this tool, the authors reviewed and edited the content as needed and take full responsibility for the content of the published article.

**Data availability.** The data (1,712 runs, 64.7 GB of run files; about 69 GB with checkpoints), frozen manifests with md5 checksums, split definitions, all 204 checkpoints and the verification cases are deposited in Zenodo, https://doi.org/10.5281/zenodo.24087719 (CC BY 4.0) [TO CHECK: reserved DOI, registered when the record is published at submission]. The training and evaluation code is available at [code repository and DOI, to be added].

**Funding.** [TO CONFIRM] (RP2 acknowledged the SOLARFOOD project, Research Council of Norway, project 352437, and Erasmus+ ICM; whether either applies here is for the authors to decide.)

---

## References

[1] O. Abdelhak, H. Mhiri, P. Bournot, CFD analysis of thermal stratification in domestic hot water storage tank during dynamic mode, Building Simulation 8 (2015) 421-429. https://doi.org/10.1007/s12273-015-0216-9

[2] E.M. Kleinbach, W.A. Beckman, S.A. Klein, Performance study of one-dimensional models for stratified thermal storage tanks, Solar Energy 50 (1993) 155-166. https://doi.org/10.1016/0038-092X(93)90087-5

[3] A.L. Nash, A. Badithela, N. Jain, Dynamic modeling of a sensible thermal energy storage tank with an immersed coil heat exchanger under three operation modes, Applied Energy 195 (2017) 877-889. https://doi.org/10.1016/j.apenergy.2017.03.092

[4] J.H. Davidson, D.A. Adams, J.A. Miller, A coefficient to characterize mixing in solar water storage tanks, Journal of Solar Energy Engineering 116 (1994) 94-99. https://doi.org/10.1115/1.2930504

[5] M.Y. Haller, C.A. Cruickshank, W. Streicher, S.J. Harrison, E. Andersen, S. Furbo, Methods to determine stratification efficiency of thermal energy storage processes: review and theoretical comparison, Solar Energy 83 (2009) 1847-1860. https://doi.org/10.1016/j.solener.2009.06.019

[6] A. Rahman, A.D. Smith, Predicting heating demand and sizing a stratified thermal storage tank using deep learning algorithms, Applied Energy 228 (2018) 108-121. https://doi.org/10.1016/j.apenergy.2018.06.064

[7] A. Soomro, A.A. Mokhtar, Prediction of performance parameters of stratified TES tank using artificial neural network, AIP Conference Proceedings 2035 (2018) 080001. https://doi.org/10.1063/1.5075600

[8] T. Gaonwe, K. Kusakana, P. Hohne, O. Odufuwa, L. Tartibu, Z. Wandong, Artificial neural network-based prediction of storage-tank temperatures in hybrid electric water-heating systems with integrated thermal energy storage, Journal of Energy Storage 156 (2026) 121540. https://doi.org/10.1016/j.est.2026.121540

[9] S. Shen, C. Wu, F. Duan, Machine learning for predicting the PCM melting process in a rectangular enclosure energy storage, AI Thermal Fluids 1 (2025) 100001. https://doi.org/10.1016/j.aitf.2024.100001

[10] H. Ma, Y. Liu, X. Zhang, S. Fan, H. Shu, X. Zhao, S. Tian, Multi-objective optimization of fin-embedded concrete thermal energy storage systems using computational fluid dynamics and machine learning, Journal of Energy Storage 180 (2026) 124366. https://doi.org/10.1016/j.est.2026.124366

[11] P. Yan, C. Wen, H. Ding, X. Wang, Y. Yang, The potential of machine learning to predict melting response time of phase change materials in triplex-tube latent thermal energy storage systems, Applied Energy 390 (2025) 125863. https://doi.org/10.1016/j.apenergy.2025.125863

[12] M. Ramanipriya, I. Tlili, S. Anitha, Numerical and machine learning framework for strategic fin design to accelerate phase change material melting in advanced enclosures, Scientific Reports 16 (2026) 32253. https://doi.org/10.1038/s41598-026-68207-0

[13] S. Kim, H. Kim, W.P. King, N. Miljkovic, Gaussian process optimization of phase change material heat sink design, Numerical Heat Transfer, Part B: Fundamentals 85 (2023) 1767-1785. https://doi.org/10.1080/10407790.2023.2273513

[14] M. Hassanzadeh, E. Ghaderi, F. Fatahi, M.A. Bijarchi, An adaptive physics-driven deep learning framework for a two-phase Stefan problem, arXiv:2512.01011 (2025).

[15] W. Chen, Y. He, Z. Song, Novel prediction model for solid-liquid phase change in latent thermal energy storage based on physics-informed neural networks, Journal of Energy Storage 146 (2026) 120035. https://doi.org/10.1016/j.est.2025.120035

[16] M.-H. Benzaama, A. Boudenne, K. Benzarti, Physics-guided artificial intelligence for latent heat transfer in phase-change material walls: comparison between universal differential equations and the Fourier neural operator, Journal of Energy Storage 175 (2026) 123309. https://doi.org/10.1016/j.est.2026.123309

[17] M. Takamoto, T. Praditia, R. Leiteritz, D. MacKinlay, F. Alesiani, D. Pflüger, M. Niepert, PDEBench: an extensive benchmark for scientific machine learning, Advances in Neural Information Processing Systems 35, Datasets and Benchmarks Track (2022). arXiv:2210.07182

[18] R. Ohana, M. McCabe, L. Meyer, R. Morel, F.J. Agocs, M. Beneitez, et al., The Well: a large-scale collection of diverse physics simulations for machine learning, Advances in Neural Information Processing Systems 37, Datasets and Benchmarks Track (2024). arXiv:2412.00568

[19] F. Bonnet, A.J. Mazari, P. Cinnella, P. Gallinari, AirfRANS: high fidelity computational fluid dynamics dataset for approximating Reynolds-averaged Navier-Stokes solutions, Advances in Neural Information Processing Systems 35, Datasets and Benchmarks Track (2022). arXiv:2212.07564

[20] Y. Luo, Y. Chen, Z. Zhang, CFDBench: a large-scale benchmark for machine learning methods in fluid dynamics, arXiv:2310.05963 (2023).

[21] S.M.S. Hassan, A. Feeney, A. Dhruv, J. Kim, Y. Suh, J. Ryu, Y. Won, A. Chandramowlishwaran, BubbleML: a multiphase multiphysics dataset and benchmarks for machine learning, Advances in Neural Information Processing Systems 36, Datasets and Benchmarks Track (2023). arXiv:2307.14623

[22] R. Mao, R. Zhang, X. Bai, T. Wu, T. Zhang, Z. Chen, et al., Benchmarking neural surrogates on realistic spatiotemporal multiphysics flows, arXiv:2512.18595 (2025).

[23] D. Hang, W. Yang, K. Ding, H. Xin, J. Wei, IC-ThermBench: an open, progressive benchmark for generalizable 2.5D/3D-IC thermal learning, arXiv:2608.23977 (2026).

[24] C. Dunlap, R. Olabiyi, F. Al-Hindawi, H. Pandey, S. Pierson, D. Curl, et al., Open datasets and machine learning for two-phase heat transfer: a review following a spatial-temporal taxonomy, Transport Phenomena 1 (2026) 20260081. https://doi.org/10.1515/tp-2026-0081

[25] I.M. Sobol', On the distribution of points in a cube and the approximate evaluation of integrals, USSR Computational Mathematics and Mathematical Physics 7 (1967) 86-112. https://doi.org/10.1016/0041-5553(67)90144-9

[26] H.G. Weller, G. Tabor, H. Jasak, C. Fureby, A tensorial approach to computational continuum mechanics using object-oriented techniques, Computers in Physics 12 (1998) 620-631. https://doi.org/10.1063/1.168744

[27] F.R. Menter, Two-equation eddy-viscosity turbulence models for engineering applications, AIAA Journal 32 (1994) 1598-1605. https://doi.org/10.2514/3.12149

[28] V.R. Voller, C. Prakash, A fixed grid numerical modelling methodology for convection-diffusion mushy region phase-change problems, International Journal of Heat and Mass Transfer 30 (1987) 1709-1719. https://doi.org/10.1016/0017-9310(87)90317-6

[29] A.D. Brent, V.R. Voller, K.J. Reid, Enthalpy-porosity technique for modeling convection-diffusion phase change: application to the melting of a pure metal, Numerical Heat Transfer 13 (1988) 297-318. https://doi.org/10.1080/10407788808913615

[30] J. Vogel, A. Thess, Validation of a numerical model with a benchmark experiment for melting governed by natural convection in latent thermal energy storage, Applied Thermal Engineering 148 (2019) 147-159. https://doi.org/10.1016/j.applthermaleng.2018.11.032

[31] B. Kamkari, H. Shokouhmand, Experimental investigation of phase change material melting in rectangular enclosures with horizontal partial fins, International Journal of Heat and Mass Transfer 78 (2014) 839-851. https://doi.org/10.1016/j.ijheatmasstransfer.2014.07.056

[32] I.B. Celik, U. Ghia, P.J. Roache, C.J. Freitas, H. Coleman, P.E. Raad, Procedure for estimation and reporting of uncertainty due to discretization in CFD applications, Journal of Fluids Engineering 130 (2008) 078001. https://doi.org/10.1115/1.2960953

[33] W. Lou, N. Baudin, S. Roux, Y. Fan, L. Luo, Impact of buoyant jet entrainment on the thermocline behavior in a single-medium thermal energy storage tank, Journal of Energy Storage 71 (2023) 108017. https://doi.org/10.1016/j.est.2023.108017

[34] B. Kamkari, H. Shokouhmand, F. Bruno, Experimental investigation of the effect of inclination angle on convection-driven melting of phase change material in a rectangular enclosure, International Journal of Heat and Mass Transfer 72 (2014) 186-200. https://doi.org/10.1016/j.ijheatmasstransfer.2014.01.014

[35] H.S. Carslaw, J.C. Jaeger, Conduction of Heat in Solids, 2nd ed., Oxford University Press, Oxford, 1959.

[36] Z. Li, N. Kovachki, K. Azizzadenesheli, B. Liu, K. Bhattacharya, A. Stuart, A. Anandkumar, Fourier neural operator for parametric partial differential equations, International Conference on Learning Representations (2021). arXiv:2010.08895

[37] O. Ronneberger, P. Fischer, T. Brox, U-Net: convolutional networks for biomedical image segmentation, in: Medical Image Computing and Computer-Assisted Intervention (MICCAI 2015), Lecture Notes in Computer Science 9351, Springer, 2015, pp. 234-241. https://doi.org/10.1007/978-3-319-24574-4_28

[38] R. Wang, R. Walters, R. Yu, Incorporating symmetry into deep dynamics models for improved generalization, International Conference on Learning Representations (2021). arXiv:2002.03061

[39] R. Wang, R. Walters, R. Yu, Approximately equivariant networks for imperfectly symmetric dynamics, Proceedings of the 39th International Conference on Machine Learning, PMLR 162 (2022). arXiv:2201.11969

[40] B. Siddani, S. Balachandar, R. Fang, Rotational and reflectional equivariant convolutional neural network for data-limited applications: multiphase flows, Physics of Fluids 33 (2021) 103323. https://doi.org/10.1063/5.0066049

[41] M. Lino, S. Fotiadis, A.A. Bharath, C.D. Cantwell, Multi-scale rotation-equivariant graph neural networks for unsteady Eulerian fluid dynamics, Physics of Fluids 34 (2022) 087110. https://doi.org/10.1063/5.0097679

[42] H. Wu, H. Luo, H. Wang, J. Wang, M. Long, Transolver: a fast transformer solver for PDEs on general geometries, Proceedings of the 41st International Conference on Machine Learning, PMLR 235 (2024). arXiv:2402.02366

[43] B. Efron, R.J. Tibshirani, An Introduction to the Bootstrap, Chapman and Hall/CRC, New York, 1994. https://doi.org/10.1201/9780429246593
