# HeatStoreBench: stratified tank family, parameter plan (DRAFT, 2026-10-30)

Status: draft for Saxam's review. Nothing in this plan has been run yet except the pilot tests listed in section 8.

## 1. What the tank family must capture

Hot water enters a tank that is initially cold (charging). The physics that matters for users and for ML:
- how sharp the hot/cold boundary (thermocline) stays,
- how much the inlet jet mixes the tank,
- when hot water reaches the outlet.

These are controlled by three dimensionless numbers, so the ranges below are chosen to cover them, not just the raw inputs:

| Group | Formula | Meaning |
|---|---|---|
| Inlet Reynolds number Re | u_in * s / nu | laminar or turbulent inlet jet |
| Richardson number Ri | g * beta * dT * H / u_in^2 | buoyancy vs inflow momentum (high Ri = good stratification, low Ri = mixing) |
| Aspect ratio | H / W | tall tanks stratify better |

(s = inlet slot height, H = tank height, W = tank width, dT = inlet minus initial temperature.)

## 2. Parameters and ranges (Tier 1, 2D planar)

Continuous parameters, sampled with a Sobol sequence (even coverage, reproducible):

| Parameter | Range | Sampling | Why this range |
|---|---|---|---|
| Inlet velocity u_in | 0.005 to 0.2 m/s | log-uniform | covers slow domestic charging to fast pump-driven inflow |
| Temperature difference dT | 5 to 50 K | uniform | small solar top-up to full charge (20 C to 70 C) |
| Inlet slot height s | 20 to 80 mm | uniform, snapped to the cell size | pipe-like jet to wide diffuser-like inlet |
| Inlet position below the top | 0 to 0.2 H | uniform, snapped | inlet at the top vs partway down (affects mixing below the inlet) |
| Tank width W (H fixed at 1 m) | 0.25 to 1.0 m | uniform, snapped | aspect ratio H/W from 1 to 4 |

Resulting coverage (with the 40 mm slot as reference):
- Re from about 150 to 24,000 (laminar and turbulent),
- Ri from about 0.4 (strong mixing) to about 7,000 (very stable), which spans the regimes reported for real tanks.

Categorical options:

| Option | Values | Share of cases |
|---|---|---|
| Inlet type | A: horizontal jet from the side wall (current case); B: downward jet from the top lid | 70% / 30% |
| Initial state | uniform cold; pre-stratified (a hot layer already on top, random thickness) | 70% / 30% |

Outlet: bottom of the opposite side wall for type A, centre of the bottom for type B.

## 3. Turbulence model per case

- Re below 1,500: laminar.
- Re above 3,000: k-omega SST with our corrected buoyancy term (`--buoyk`).
- Re 1,500 to 3,000 (transition band): every case run BOTH ways, so users and the paper can see the model effect directly.
- Every case carries its model as a label in the dataset. OpenFOAM's own `buoyancyTurbSource` is NOT used (wrong sign in the Boussinesq k term, found 2026-10-30).

## 4. Run length and outputs

- Each case runs to dimensionless time t* = t * Q / V = 1.2 (Q = inflow rate, V = tank volume), i.e. a little past the point where one tank volume has entered. This makes runs comparable across flow rates. To first order the cost per case does not depend on flow rate (fast inflow means a shorter run but smaller time steps), but it does grow with tank width and with narrower slots: up to about 4 times the reference case for the widest tank with the narrowest slot. The pilot (section 8) will measure the real spread.
- 120 snapshots per case (every 0.01 t*) of T, U, p_rgh, plus k, omega, nut for turbulent cases, on the uniform grid (directly usable as image-like arrays).
- Scalar time series at every step: mean tank temperature, outlet temperature, stored energy, stratification number, MIX number, exergy, thermocline height and thickness.
- Storage estimate: about 40 MB per case in float32 at the 5 mm mesh, about 40 GB for 1,000 cases (Zenodo allows 50 GB per record; split by family if needed).

## 5. Benchmark splits

| Split | How it is made | What it tests |
|---|---|---|
| In-distribution | random 80/10/10 | basic accuracy |
| Unseen geometry | hold out all cases with H/W above 3.5 and all type-B inlets with s above 70 mm | generalisation to new tank shapes |
| Unseen regime | hold out the lowest-Ri corner (Ri below 2) | extrapolation to strong mixing |
| Long horizon | train on t* below 0.6, test the rollout to 1.2 | error growth in time-stepping surrogates |
| Laminar/turbulent | train on laminar only, test on turbulent | regime shift |

## 6. Size and compute

- Tier 1 target: 1,000 cases plus the transition-band duplicates (about 100 more).
- Cost per case at the 5 mm mesh: reference case 744 s on one laptop core when running alone; expect an average of 20 to 30 min per case when many run together (measured on the lab PC: one 5 mm case runs about 3 times slower when 26 solver processes share its 16 physical cores).
- If mesh convergence (running now) says 5 mm is enough: roughly 400 to 500 core-hours, about 1 to 1.5 days of wall time on the lab PC plus the laptop.
- If 3.33 mm is needed: about 5 times more, roughly 1 week. Still feasible, but the pilot should confirm before committing.
- Lesson from the convergence runs: on the lab PC, run at most about 16 solver processes at once (one per physical core); more than that slows everything.
- Batches are launched only with Saxam's go-ahead.

## 7. Decisions for Saxam

1. **Water properties.** Current setup: constant properties (Boussinesq, beta fixed at 3.5e-4 1/K). Real water's beta roughly doubles between 20 C and 60 C, and viscosity halves, so with dT up to 50 K thermal-journal reviewers may object. Option: switch production runs to the compressible solver with real water property curves. A bonus: OpenFOAM's buoyancy term for that solver has the correct sign, so we would rely less on our own code. Cost likely 1.5 to 2 times higher. Recommendation: run one pilot comparison before deciding.
2. **Discharging cases.** With constant properties, discharging (cold water in at the bottom) is an exact mirror image of charging and adds nothing. With real properties it becomes genuinely different and worth about 30% of the cases.
3. **Inlet type B (top lid).** Keep, or drop to save effort and keep only the side-wall inlet.

### Pilot result for decision 1 (2026-10-30, laptop, 5 mm mesh, Tin 60 C, T0 20 C)

| Case | Boussinesq | Real properties | Note |
|---|---|---|---|
| Laminar, u_in 0.02, 600 s: final mean T | 329.98 K | 329.92 K | same energy |
| Laminar: thermocline height, 100 to 600 s | | | within 0.00 to 0.06 m of each other |
| Laminar: wall time | 942 s | 1059 s | real is 12% slower |
| Turbulent, u_in 0.1, 150 s: thickness | 0.16 to 0.26 m (our k fix) | 0.13 to 0.21 m (OpenFOAM's density-based term) | two independent buoyancy implementations agree |
| Turbulent: bottom temperature at 150 s | 20.00 C | 20.01 C | no false mixing in either |
| Turbulent: wall time | 841 s | 801 s | similar |

Decision (Saxam: "go with your recommendations"): production runs use REAL water properties (buoyantPimpleFoam, `--props real`, with OpenFOAM's buoyancyTurbSource for turbulent cases). Reasons: only about 10% extra cost, physically correct across the full dT range, makes discharging cases meaningful, and relies on OpenFOAM's own (correct) buoyancy term. The Boussinesq + our k fix becomes a documented cross-check, not the production model. Discharging cases are therefore included (about 30% of cases), and the top-lid inlet (type B) is kept.

### Mesh convergence result and decision (2026-10-30, lab PC, real properties)

Same tank on 5 mm (L1), 3.33 mm (L2), 2.22 mm (L3); laminar u_in 0.02 m/s to 430 s, turbulent (SST + buoyancyTurbSource) u_in 0.1 m/s to 135 s.

| Quantity | L1 vs L3 | L2 vs L3 |
|---|---|---|
| Mean tank temperature | 0.004 K (lam), 0.02 K (tur) | 0.004 K, 0.03 K |
| Thermocline height | mean 15 mm, max 35 to 52 mm | similar or smaller |
| Thermocline 10-90 % thickness | 0.15 to 0.21 m on all levels, no mesh trend | |
| Centreline T profile, RMS difference | 0.6 to 5.2 K (typically 1.5 to 3.7 K) | typically about 1 K |

GCI on thermocline height applies at only 12 of 37 (laminar) and 1 of 6 (turbulent) times, because the differences are oscillatory: the jet and the internal waves are unsteady, so instantaneous snapshots on different meshes are out of phase. Integral and engineering quantities are mesh-independent at 5 mm; instantaneous fields are not converged point by point (about 4 to 9 % of dT RMS at 5 mm, about 2.5 % at 3.33 mm).

DECISION (Saxam, 2026-10-30, "option 1"): all 1,024 cases at 5 mm, plus a fidelity subset of the first 128 Sobol cases (12.5 %) rerun at 3.33 mm with identical parameters. The paper reports the field uncertainty; the paired subset becomes a multi-fidelity benchmark task (coarse to fine). Geometry is snapped to a common 10 mm grid so the same cases fit both meshes (design_v2_full.csv, design_v2_fine128.csv). Outlet breakthrough curves were not logged in the convergence runs (outlet logging added later); they are compared in the fidelity subset.

## 8. Before the full batch

1. Mesh convergence: L1/L2/L3, laminar and turbulent (running on the lab PC since 2026-10-30 08:45 UTC).
2. Validation against a published experiment. Scopus search 2026-10-30 (72 + 35 records screened): no quasi-2D tank-charging experiment with usable data exists, so Tier 1 (2D) is validated indirectly: the same solver, properties and turbulence treatment are validated in 3D, then used in 2D. Chosen primary case: Lou, Baudin, Roux, Fan, Luo (2023), J. Energy Storage 71, 108017 (ScienceDirect pii S2352152X23014147). Cuboid tank 194 x 194 mm, 390 mm high, central 10 mm top port, upper and lower perforated-baffle manifolds (33 mm), charging only, Re_in 1,368 to 6,831, hot 50 to 70 C into cold 20 C. Measured: PIV velocity fields and jet penetration length vs time (their Fig. 5), inlet and outlet temperatures. Fits our laminar/turbulent split and dT range, and tests exactly the buoyant-jet mixing our turbulence fix targets. Data must be digitised from figures. Secondary: Shah and Furbo (2003), Solar Energy 75(4) 337-348 (cylinder, three inlet designs, measured stratification, discharge). For Tier 2 (axisymmetric): ASHRAE RP-1185 chilled-water slotted-diffuser field data.
3. DONE 2026-10-30: generator upgrades (variable W, s and inlet position; type-B inlet; discharge mode; pre-stratified start; t* based end time; case.json metadata) and the exporter (export_case.py: one HDF5 file per case plus metrics.json with stored energy, exergy, MIX number, stratification number, thermocline height and thickness, outlet temperature). Tests: default case byte-identical to the reference, all variants run, energy balance within 0.1 % of the inflow, MIX = 0 and 1 in the synthetic limits. Storage: about 18 MB per exported case (120 snapshots); raw OpenFOAM output is about 400 MB per case, so raw files are deleted after a verified export.
4. Pilot of about 20 cases at the corners of the parameter space (lowest/highest Ri, Re, aspect ratio) to catch failures before the full run.
