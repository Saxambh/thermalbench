# ThermBench: PCM melting family, parameter plan (DRAFT, 2026-11-01)

**Status.** Draft. Decisions 1, 2 and 4 were taken on 2026-11-01 (section 7). Nothing in this plan has been run except the validation runs listed in section 8, which are still running.

## 1. What the PCM family must capture

A phase change material (PCM) in a slab-shaped container is melted from a heated wall, sometimes with metal fins on that wall. This is the basic cell of most latent heat storage units: plate, slab and finned heat exchangers. What matters to users and for ML:
- **Melting rate.** How fast the material melts: liquid fraction over time, and total melting time.
- **Heat input.** How much heat the wall delivers over time: heat rate and Nusselt number. This is the "power" of the store.
- **Interface shape.** Natural convection in the melt makes the top melt much faster than the bottom. A model that misses this gets the melting time wrong by a factor of 2 or more.
- **Fins.** How much they help, and when. Fins help most early on, then partly block the convection (Kamkari & Shokouhmand 2014).

These are controlled by a handful of dimensionless groups, so the ranges below are chosen to cover them:

| Group | Formula | Meaning |
|---|---|---|
| Rayleigh number Ra_H | g β (Tw − Tm) H³ / (ν α) | strength of natural convection in the melt |
| Stefan number Ste | cp (Tw − Tm) / L | sensible vs latent heat: how "hard" the wall drives the melting |
| Subcooling number Sc | cp,s (Tm − T0) / L | sensible heat needed to warm the solid up to melting first |
| Prandtl number Pr | ν / α | material property (paraffins about 50, fatty acids about 100) |
| Aspect ratio A | H / W | tall thin slabs vs wide boxes |
| Fin groups | N, L_f / W, t_f / H | number, reach and thickness of the fins |

H = height, W = PCM layer width (distance from the heated wall), Tw = wall temperature, Tm = melting point, T0 = initial temperature, L = latent heat.

## 2. Parameters and ranges (2D planar)

**Fixed:** height H = 100 mm. The width varies, as in the tank family, so every case maps onto the same 200-row grid. The heated wall is the left wall. The other walls are adiabatic, with no-slip on all of them.

Continuous parameters, sampled with a Sobol sequence:

| Parameter | Range | Sampling | Why this range |
|---|---|---|---|
| Wall superheat Tw − Tm | 5 to 30 K | uniform | gentle (low-temperature solar, building) to strong driving. Covers both validation cases (10 K and 26.5 K) |
| Subcooling Tm − T0 | 0.5 to 20 K | uniform | store starting just below the melting point (Vogel, 1 K) to fully cold (Kamkari, 18.5 K) |
| PCM layer width W | 20 to 100 mm | uniform, snapped to the cell size | A = 1 to 5; typical slab and plate store thicknesses |
| Fin length L_f / W (finned cases) | 0.2 to 0.8 | uniform, snapped | short stubs to fins reaching most of the way across. Kamkari used 0.5 |
| Fin thickness t_f (finned cases) | 1 to 4 mm | uniform, snapped to 0.5 mm | thin sheet fins to milled fins like Kamkari's 4 mm |

Categorical options:

| Option | Values | Share of cases |
|---|---|---|
| Material | n-octadecane (Pr ≈ 50, Tm = 28 °C); lauric acid (Pr ≈ 100, Tm = 43.5 °C) | 50% / 50% |
| Number of fins N | 0, 1, 2, 3, 4, 5 (equally spaced, all on the heated wall) | 30% with no fins; the rest spread evenly over 1 to 5 |
| Orientation (decision 2) | heated from the side (0°); tilted 45°; heated from below (90°) | 70% / 15% / 15% |

**Resulting coverage (H = 100 mm)**
- Ra_H from about 1e8 to 7e8, all laminar by Elder's criterion (laminar below about 1e10).
- Ste from about 0.04 to 0.37.
- Sc from 0 to about 0.23.
- Both validation cases sit inside the box: Vogel at Ra 2e8, Ste 0.09; Kamkari at Ra 8e8 (H = 120 mm), Ste 0.32.

**Why only two materials.** Each material we include is one we have validated against an experiment (section 8). A third material without its own validation would weaken the "every family is validated" claim (decision 1).

## 3. Model

- **Solver.** buoyantPimpleFoam with OpenFOAM's built-in enthalpy-porosity melting model (solidificationMeltingSource; Voller & Prakash 1987).
  - Constant properties, using the Vogel & Thess "B-2D" set: mean density and cp of solid and liquid; liquid conductivity and viscosity at the mean liquid temperature.
  - Boussinesq buoyancy relative to Tm, added once (constant density in the solver).
  - Vogel & Thess showed this model is within 1.4% of a variable-property, volume-expansion model on liquid fraction.
- **Mushy zone constant.** 1e6 kg/(m³ s), ε = 1e-3, the same as Vogel & Thess.
- **Fins.** Held at the wall temperature, an approximation for metal fins (decision 3). Kamkari's validation will tell us how large the error is.
- **Generator.** `make_pcm_case.py` (built and smoke-tested 2026-11-01; meshes with 0 and 3 fins both pass checkMesh).

## 4. Run length and outputs

**Run length**
- Each case runs until it is fully melted (liquid fraction 0.995), stopped automatically by a runTimeControl function object.
- There is a cap of 1.5 times the predicted melting time. The prediction comes from Kamkari's melt-fraction correlation in X = Ste*² Fo Ra^0.25 (1 + N)^0.5, which is accurate to within 0.014 RMS for their geometry and is used here only for budgeting.
- Snapshots: 100 per case, evenly spaced over the predicted melting time, so runs are comparable whatever their speed.

**Fields saved** on the uniform grid as image-like arrays: temperature T, liquid fraction, and velocity Ux and Uy.

**Scalar series, every 10 steps**
- Liquid fraction and mean temperature.
- Heat rate through the heated wall and through the fins, separately.
- Nusselt number.
- Stored energy, sensible and latent separately.
- An energy balance check: stored energy minus the integrated wall heat. This should close within 1%, as it does for the tank family.

**Storage.** About 10 to 25 MB per case at the 0.5 mm mesh, so about 10 GB for 500 cases.

## 5. Benchmark splits

| Split | How it is made | What it tests |
|---|---|---|
| In-distribution | random 80/10/10 by design point | basic accuracy |
| Unseen fin count | train on N ≤ 3, test on N = 4 and 5 | generalisation to new geometries |
| Unseen driving | hold out Ste above the 90th percentile | extrapolation to stronger heating (faster, more convective melting) |
| Unseen material | train on n-octadecane, test on lauric acid, and the reverse | transfer across materials (Pr 50 vs 100) |
| Unseen orientation (if decision 2 is yes) | train on side heating, test on 45° and bottom heating | regime shift: bottom heating gives Rayleigh-Bénard style plumes |
| Long horizon | train on t below 0.5 t_melt, roll out to full melting | error growth in time-stepping surrogates |

The physics baseline, matching the tank family's plug-flow model, is the Kamkari correlation for melt fraction. A **conduction-only Stefan solution** shows how much convection matters. The hybrid ML entry learns the correction to the correlation.

## 6. Size and compute

**Size.** 500 cases is recommended (decision 4). PCM runs cost more than tank runs: melting takes 0.5 to 4 hours of physical time at time steps of about 0.1 s.

**Measured cost (Vogel case, 0.5 mm mesh, 10k cells, busy laptop core)**
- About 2.1 s of wall time per simulated second.
- Average case (about 20k cells, about 1.5 h of melting): about 6 core-hours.
- 500 cases is therefore about 3,000 core-hours: about 2.5 to 3 days on all three PCs (about 45 job slots).

**Two ways to cut this, pending tonight's validation runs**
- If the halved time step (V3) shows no difference, raise the maximum step from 0.1 to 0.2 s. That roughly halves the cost.
- If the 0.25 mm and 0.5 mm meshes agree, 0.5 mm is confirmed for production. A 1 mm production mesh plus a 0.5 mm fidelity subset (the multi-fidelity design used for the tank family) would cost about one quarter as much. Use it only if the 1 mm mesh stays within about 3% on liquid fraction.

**Timing.** The batch would start when the tank batch frees the PCs (about 4 November), and only with Saxam's go-ahead.

### Cost re-estimate (2026-11-02): the section 6 figure was far too low

**Method** (`scripts/pcm_budget.py`, `pcm_budget500.py`)
- **Melting time.** An energy balance with laminar convection on the heated wall, Nu ∝ Ra^0.25.
  - Calibrated on our Vogel and Kamkari runs; the constant agrees to 13 % between the two.
  - Fins scale it by (1 + N)^-0.5 and tilt by Kamkari's ratios.
  - It underestimates finned cases by 25–35 %, so it is used for budgeting and snapshot spacing only.
- **Cost per case.** Measured on the lab at 0.5 mm: 5.8 s of wall time per simulated second for 24k cells.
- **Time step.** It is Courant-limited at strong heating (Co ≈ 1 at 0.1 s for Kamkari), so a larger maxDeltaT helps only the gentle cases.

**Why the old figure was wrong.** Gentle heating (5 K) in a wide box (100 mm) takes 30–40 h of physical time to melt. That is about 200 core-hours per case at 0.5 mm, against the 6 core-hours assumed above.

| Design (500 cases) | Core-hours | Days on all PCs (~1000 core-h/day) | Slowest case |
|---|---|---|---|
| As drafted: superheat 5–30 K, W 20–100 mm, 0.5 mm, maxDeltaT 0.1 | ~12,400 | ~12 | ~220 core-h |
| Same, maxDeltaT up to the Courant limit | ~9,100 | ~9 | ~120 core-h |
| Same ranges, **1 mm** mesh | ~1,100 | ~1 | ~15 core-h |
| Superheat 10–30 K, W 20–60 mm, 0.5 mm | ~3,100 | ~3 | ~30 core-h |
| Superheat 10–30 K, W 20–60 mm, 1 mm | ~400 | ~0.4 | ~3 core-h |

The 1 mm mesh test (lab, started 2026-11-02 06:48 UTC) decides between these. If 1 mm is within about 3 %, the full ranges at 1 mm plus a 0.5 mm fidelity subset is affordable.

**Pilot tables** (`scripts/pcm_design.py`)
- 12 corner points per material, plus a time-step check (maxDeltaT 0.1 against 0.5).
- They are generated for both meshes and both range options.
- Pilot cost: ~730 core-h at 0.5 mm with full ranges (two cases at ~165 core-h each), against ~90 core-h at 1 mm.
- **Definitions for melting-range materials.**
  - Superheat is measured above the range midpoint, which is the model's reference temperature (lauric 45.85 °C).
  - Subcooling is measured below the solidus, so the PCM always starts fully solid.
  - With this, the Vogel and Kamkari calibrations agree to 0.5 %.
  - On the old definition (above 43.5 °C), a 5 K lauric case had its wall only 0.3 K above the liquidus.
- **Dry run.** All 50 pilot meshes (25 cases × 2 meshes) pass checkMesh.
- Runner: `scripts/pcm_batch.sh`. It runs the slowest cases first, restarts cleanly, and exports each case on finishing.

## 7. Decisions for Saxam

**Decided 2026-11-01** (Saxam: "go with your recommendations for 1, 2 and 4"):
- **1.** Two validated materials only: n-octadecane and lauric acid.
- **2.** Include orientation (0°, 45°, 90°; 70/15/15). This needs the inclination validation.
- **4.** 500 cases.

**Decided 2026-11-02** (Saxam: "yes go with your recommendation"):
- **5. Mesh: 0.5 mm for all cases.**
  - The 1 mm test melted 8–11 % faster than 0.5 mm in the middle of the melt (Kamkari, no fin and 1 fin), against the 3 % threshold.
  - 0.5 mm agrees with 0.25 mm within about 1 % (Vogel).
- **Ranges narrowed for cost:**
  - superheat 8–30 K, measured above the range midpoint for lauric;
  - width W 20–60 mm (A = H/W 1.7–5).
  - Both validation cases stay inside. Cost: about 3,000 core-hours, about 3 days on all PCs, and the slowest case about 30 core-hours.
  - Very gentle heating (5–8 K) and wide boxes (60–100 mm) are dropped. They would have cost about 3 times more.
- **Design files:** `scripts/pcm_pilot.csv` (25 cases, about 220 core-h) and `scripts/pcm_full.csv` (500 cases).
  - Generated with `pcm_design.py` and these ranges.
  - Lauric settings and the fin model are still provisional, so regenerate both files once they are frozen.

Decision 3 (fin model) waits for the conducting-fin Kamkari runs (pc3, started 2026-11-02 07:01 UTC).

1. **Materials.**
   - Recommended: the two validated PCMs (n-octadecane and lauric acid).
   - Optional: a commercial paraffin such as RT35 for industrial relevance, but there is no matching experiment we can validate it against.
   - Gallium (the classic Gau & Viskanta metal case) has very different physics (Pr 0.02, oscillating flow) and would fit better as a separate later family.
2. **Orientation.**
   - Recommended: include it, with tilted and bottom-heated cases at 30% in total. It is a real design question for storage units and costs nothing extra to model; only the gravity vector changes.
   - It needs one more validation: Kamkari, Shokouhmand & Bruno 2014 (IJHMT 72:186) melted lauric acid at 0°, 45° and 90° in the same enclosure. It is readable through Lund.
3. **Fin model.**
   - Isothermal fins: current, cheap.
   - Conducting fins: a conjugate heat transfer solve, about 1 to 2 days of work to build, with runs about 1.5 times slower.
   - Decide after the Kamkari fin validation. If the isothermal model matches the measured melting time ratios (0.82 for 1 fin, 0.64 for 3) within about 5%, keep it.
4. **Size.** 500 cases (recommended) or 1,000. 500 is larger than the comparable storage datasets in our 30 October novelty search. The nearest was a 320-run hydrate storage set made with COMSOL. That search was not specific to PCM, so this should be rechecked before the paper claims it.
5. **Mesh.** 0.5 mm for all cases, or 1 mm plus a 0.5 mm fidelity subset. Decide after tonight's V1/V2 comparison and a 1 mm test.

## 8. Before the full batch

- [x] Generator built; meshes with and without fins pass checkMesh (2026-11-01).
- [x] Validation data extracted:
  - Vogel & Thess 2019 (plain box; numerical and experimental liquid fraction);
  - Kamkari & Shokouhmand 2014 (0, 1 and 3 fins; melt fraction and melting time ratios).
  - Both are saved as `validation_*.md`.
- [ ] Vogel validation running on the laptop since 17:01 UTC, three runs: 0.5 mm, 0.25 mm, and 0.5 mm with half the time step.
- [ ] Kamkari fin validation running on pc3 since 17:40 UTC: 0, 1 and 3 fins at 70 °C.
- [x] Orientation validation data extracted (Kamkari, Shokouhmand & Bruno 2014). The 45° and bottom-heated runs started on the laptop at 17:57 UTC.
- [x] **Source check in Chrome (2026-11-01)**
  - Vogel property formulas confirmed against the published Table 3.
  - The B-2D conductivity is the liquid value at Tm. This is fixed in the generator; V1–V3 used a value 0.6 % lower, which is negligible.
  - Mushy constant 1e6 and q 1e-3 confirmed.
  - Kamkari 3-fin centres are 29/60/91 mm, not 30/60/90. The run was restarted, and `--fin-y` added.
  - Kamkari's own simulation (Safari et al. 2022) uses the melting range with Tm = 45.85 °C. A midpoint sensitivity run was started.
  - β is not published anywhere, so the backed-out 8.2e-4 stays.
  - Heater warm-up of about 4 min: a known 1–2 % effect.
- [ ] Melting-range question: if the 45.85 °C midpoint run is closer to the experiment than 43.5 °C, use the midpoint of the range for lauric acid in production. n-octadecane has a true melting point, so this does not affect it.
- [ ] Exporter: extend `export_case.py` for liquid fraction, fin heat rate and the energy balance; test it on the validation runs.
- [ ] Auto-stop at full melt (runTimeControl) and the melting-time prediction used for the snapshot spacing.
- [ ] 1 mm mesh test against 0.5 mm.
- [ ] Pilot of about 24 cases covering the corners of the design (smallest and largest Ste, W, N, both materials). It must pass energy closure within 1%, with no failures.
