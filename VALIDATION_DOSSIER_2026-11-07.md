# ThermalStorageBench: validation dossier for independent review (7 November 2026)

**Purpose.** This file collects, in one place, everything done so far on ThermalStorageBench: the design
logic, the numerical set-up, verification, validation, quality control, the ML benchmark and its results.
It is written for an independent reviewer who has not seen the project. For every major choice it gives
the reasoning, the evidence, what we accept, and what we do not claim.

**Status.** No paper text has been written. Results come first. The tank family (CFD, verification and ML)
is complete apart from the final statistical tables. The PCM family has all 500 simulations accepted, its
verification and validation done, and its ML training not yet started.

**How to read the numbers.**
- Field errors are RMSE in % of the run's temperature difference ΔT unless stated otherwise.
- "Pre-registered" means the limit or rule was written down and committed to git before the result it
  judges existed. Rules added after a result are labelled post hoc.
- All file names are relative to the repository root.

---

## Corrections after review (added 7 November, late)

This dossier is kept as the version the independent reviewer assessed. The statements below are **superseded**,
and the corrected wording applies wherever the old one appears in the body. Details are in
`REVIEW_RESPONSE_2026-11-07.md` (item numbers in brackets).

| § | Superseded statement | Corrected statement |
|---|---|---|
| 5.2, 14 | "a mesh uncertainty of up to about 2.8 %" | 0.34 to 2.76 % of ΔT field difference in the four designs tested (three laminar, none flagged); not a dataset-wide bound [2.1] |
| 5.2 | "most of the 2.76 % (T0551) is the flow's own sensitivity" | The mesh difference (2.76 %) is of the same order as the response to a 0.01 % inlet change (1.85 %); the two cannot be separated in this design [2.3] |
| 5.2 | "every integral quantity passed" (T0243) | T0243's energy difference (0.96 %) is borderline [2.2] |
| 5.3, 5.4 | "numerical error of the production settings" (T0211) | Numerical-setting dependence of the production solution; n4 and co25 still differ by 2.49 %, so neither is shown converged [2.4] |
| 8.2 | "part of the measured ML error in this regime may be label error" | Across T0211 and T0052, the tested alternative references moved ensemble field error by at most 0.43 pp of ΔT and preserved the model ordering (`thermbench_ml/altref_2026-11-07/RESULT.md`). Similar scalar errors cannot show how much error the two CFD fields share with the true solution |
| 7.4, 8.1 | "energy error" and "outlet temperature error" as real quantities | Energy is a constant-ρcp proxy and matches the real-property energy error within ±1 %. The outlet metric is exactly the area-averaged outlet temperature; it differs from the flow-weighted outlet temperature by a median 0.6 % of ΔT, 2.3 % around breakthrough, and up to about 30 % in very-high-Ri laminar runs (`thermbench_ml/proxy_check_2026-11-07/RESULT.md`) [4.2] |
| 7.4 | y_mid missing rate not reported | The label has no θ = 0.5 crossing in a median 2.5 % of snapshots (up to 51 %); these are excluded from the midpoint error and counted in `y_mid_missing` [4.2] |
| 7.3 | generalisation wording | ood_geom covers the tails of one geometry family; ood_flow is SST-only extrapolation; ood_mode is transfer under an approximate symmetry [4.3] |
| 8.4, 13 | "transfers to discharge only through the symmetry" | On ood_mode (FNO / U-Net), the models without the canonical frame stay at 13 % or worse (plain 64.8 / 67.0 %, hybrid only 13.0 / 13.3 %); canonical only reaches 12.4 / 9.85 %, and hybrid + canonical about 4.4 %. The canonical-frame benefit was then confirmed on 215 designs with no identified pre-freeze exposure: +9.2 pp (FNO) and +9.7 pp (U-Net), Holm p 0.0004 each, as a pre-registered subset analysis (`thermbench_ml/confirmation_discharge_2026-11-07/RESULT.md`) [4.4] |
| 7.2, 8.4 | "main model: FNO hybrid in the canonical frame"; resolution-independence argument | FNO and U-Net are co-equal baselines, with no "main model"; the resolution argument is dropped [4.5] |
| 8.4 (new) | the hybrid + canonical combination is implicitly the best variant | Design-level intervals show it is clearly best only on ood_mode. The canonical-only model is slightly better on random and ood_flow (both architectures), and U-Net hybrid + canonical is worse than U-Net hybrid or U-Net canonical on ood_geom (`thermbench_ml/stats_2026-11-07/design_ci.md`) |
| 8.1 | speed "about 6,000 times faster" | A latency ratio of median wall times, 2.64 h single-core CFD (293 logs) against 1.45 s for the 3-seed ensemble on a laptop RTX 4060 with the model loaded (821 run-split timings from 654 distinct runs): about 6,500 (exact 6,541; the response's "6,455" used the rounded 2.6 h). Hardware and timing boundaries in `thermbench_ml/capacity_2026-11-07/SPEED.md`; no equal-cost claim [4.10] |
| 5.1 | "a label difference smaller than half the best ML error cannot change a benchmark ranking" | Withdrawn. A reference change of size d can move a two-model gap by up to 2d; the limits are engineering tolerances [5.1] |
| 11.1 | "systematic in sign (all PCM cases melt early)", "all 9 cases" | 6 unique designs: in the 0.5 vs 0.25 mm comparison the finer mesh melts later in all 6 (1.0 to 8.7 %). G131 and G301 are width-adjusted variants [3.4] |
| 11.1 | G131 GCI 15.43 % (medium) / 9.22 % (fine), p 0.678, from t99 at the snapshots | t99 was quantised by the 42 s write interval. From the dense liquid-fraction series: **13.06 % / 7.50 %, p 0.741**; the 0.5 mm run melts about **9.5 %** before the extrapolated t99 (not 11 %). The time step is Courant-limited and halves with the mesh, so this is a combined space-time refinement. G301 (p ≈ 0.15) gets no GCI; on the same basis as the old 6.67 % (divided by the fine result) the 0.5 mm run melts 6.76 % earlier (dense); P0021 0.70 % (not 0.98 %) [3.3] (`verification_data/pcm_timestep_t99.md`) |
| 10 | Mushy constant choice not disclosed | Lauric acid (Cu 5e6, melting range) was chosen after the plain-wall comparison with Kamkari Fig. 6 (2 November), so that case informed it; the 1-fin, 3-fin and tilted cases tested it afterwards. Octadecane (1e6) was taken from Vogel & Thess before any run [3.11] |
| 10 | "the remaining +0.08 in the first hour is model error" (3 fins) | The remaining difference combines residual discretisation, properties, boundary conditions, experimental uncertainty and model form; these runs do not separate them [3.10] |
| 8.4 | U-Net ood_flow 9.19 (2 seeds) | 9.21 with all 3 seeds (`thermbench_ml/repro_2026-11-07/RESULT.md`) |
| 6 | Lou h_j "bias +2.4 mm ... within the measurement spread" | The mean hides a trend: −2.9 mm (50 to 300 s), −0.9 mm (350 to 450 s), **+10.8 mm (500 to 700 s)**, deeper than both PIV tests. The between-test spread is not an uncertainty band [3.7] (`validation_Lou2023_case_data.md`) |

---

## Contents

1. What the benchmark is and why it exists
2. Tank family: design
3. Tank family: numerical model and the choices behind it
4. Tank family: quality control and exclusions
5. Tank family: verification (pre-registered)
6. Tank family: validation against experiment
7. Tank ML benchmark: task, models, splits, metrics
8. Tank ML results
9. PCM family: design and model
10. PCM family: validation against experiments
11. PCM family: verification, solver repair and QC
12. PCM family: accepted inventory and freeze
13. Process integrity: rules, deviations and errors we found in our own work
14. What we claim and what we do not
15. What is not done yet
16. Questions we would like the reviewer to challenge

---

## 1. What the benchmark is and why it exists

**Gap.** A Scopus search (30 October 2026, rechecked 2 November) found no open CFD dataset with an ML
benchmark for thermal energy storage. The nearest storage dataset found was a 320-run hydrate set made in
COMSOL. Existing ML work on storage tanks trains on private data, so results are not comparable.

**What we provide.**
- Two families of 2D transient CFD simulations made with OpenFOAM v2606:
  - a **stratified water tank** (sensible storage): 1,212 runs;
  - a **phase change material (PCM) cell** (latent storage): 500 runs.
- Fixed design-level train/validation/test splits, including out-of-distribution splits.
- Metrics that match what an engineer uses (stored energy, outlet temperature, thermocline position,
  melt fraction, melt time), not only field RMSE.
- Baselines from simple physics to neural operators (FNO, U-Net), with a physics-hybrid variant.

**Why 2D.** A 2D run costs minutes to hours on one core, where a 3D run of the same tank costs days. 2D
also gives image-like arrays that every ML architecture can use. The benchmark tests surrogate models on
realistic buoyant flows; it is not a design tool for a specific 3D tank. Validation is done in 3D for the
tank (section 6) and against 2D-designed experiments for the PCM (section 10).

---

## 2. Tank family: design

**Physics to capture.** Hot water enters a cold tank (charging), or cold water enters a hot tank
(discharging). What matters:
- how sharp the hot/cold boundary (thermocline) stays;
- how much the inlet jet mixes the tank;
- when the thermocline reaches the outlet.

These are governed by three dimensionless groups, so the ranges were chosen to cover them:

| Group | Formula | Meaning |
|---|---|---|
| Inlet Reynolds number Re | u_in s / ν | laminar or turbulent jet |
| Richardson number Ri | g β ΔT H / u_in² | buoyancy against inflow momentum (low Ri = mixing) |
| Aspect ratio | H / W | tall tanks stratify better |

**Sampled parameters.** Sobol sequence, 1,024 design points (`design_v2_full.csv`):

| Parameter | Range | Sampling |
|---|---|---|
| Inlet velocity | 0.005 to 0.2 m/s | log-uniform |
| ΔT | 5 to 50 K | uniform |
| Slot height s | 20 to 80 mm | uniform, snapped to 10 mm |
| Port offset below the top | 0 to 0.2 H | uniform, snapped |
| Tank width W (H = 1 m) | 0.25 to 1.0 m | uniform, snapped |
| Inlet type | A side-wall slots / B lid and bottom slots | 70 / 30 % |
| Initial state | uniform / pre-stratified (tanh thermocline) | 70 / 30 % |
| Operation | charging / discharging | about 70 / 30 % |

Coverage: Re about 150 to 24,000; Ri about 0.4 to 7,000.

**Why Sobol.** Even, reproducible coverage of a 5-dimensional continuous space, so interpolation tests are
fair and no region is left empty by chance.

**Why snapped geometry.** All geometry sits on a 10 mm grid so the same designs fit the 5 mm production
mesh, the 2.5 mm and 10 mm verification meshes, and a planned 3.33 mm subset without changing the inputs.

**Turbulence treatment by Re** (`scripts/make_design.py`):
- Re < 1,500: laminar.
- Re > 3,000: k-omega SST.
- 1,500 to 3,000 (transition band): **every design is run both ways**, so the closure effect is measured
  directly, not assumed.

Result: 432 laminar-only designs, 396 SST-only, 192 with both models, so 1,020 design points and 1,212 runs
after exclusions (section 4).

**Run length.** Each run lasts to dimensionless time t* = t Q / V = 1.2, a little past the moment one tank
volume has entered. This makes runs comparable across flow rates. 121 snapshots per run.

---

## 3. Tank family: numerical model and the choices behind it

| Item | Setting |
|---|---|
| Solver | buoyantPimpleFoam (OpenFOAM v2606), compressible formulation |
| Properties | real, temperature-dependent water properties |
| Mesh | uniform 5 mm |
| PIMPLE | nOuterCorrectors 2, nCorrectors 2, maxCo 0.5, maxDeltaT 0.5 s |
| Turbulence (SST runs) | k-omega SST with OpenFOAM's buoyancyTurbSource |
| Runs | serial (one core each), so deterministic |
| Output per run | `thermbench.h5`: 121 snapshots of T, p_rgh, ux, uy (and k, omega, nut for SST), plus stored energy, exergy, MIX, stratification number, thermocline midpoint and thickness, mean and outlet T; `case.json` with all inputs |

### 3.1 Real properties rather than Boussinesq

**Decision (30 October).** Production uses real water properties.

**Evidence from the pilot comparison** (laptop, 5 mm, 20 to 60 °C):
- laminar: same final energy (329.98 vs 329.92 K), thermocline within 0.06 m, 12 % slower;
- turbulent: two independent buoyancy implementations gave the same picture (thickness 0.16 to 0.26 m vs
  0.13 to 0.21 m), no false mixing in either, similar cost.

**Why.**
- β of water roughly doubles between 20 and 60 °C and viscosity halves. With ΔT up to 50 K, constant
  properties would be a weak point for a thermal journal.
- With real properties, discharging is no longer an exact mirror of charging, so discharge runs carry
  information (with constant properties they would add nothing).
- About 10 % extra cost.
- The compressible path uses OpenFOAM's own buoyancy source for k, which has the correct sign.

**Related finding.** In the Boussinesq path, OpenFOAM's buoyancyTurbSource has the wrong sign in the k
equation (found 30 October; bug report drafted in `ESI_bug_report_draft.md`). Production does not use that
path. Our own corrected Boussinesq k term is kept only as a documented cross-check.

### 3.2 The 5 mm mesh

**October study** (5, 3.33, 2.22 mm, one laminar and one turbulent case, older numerics):
- mean tank temperature within 0.004 K (laminar) and 0.02 K (turbulent);
- thermocline height mean 15 mm, maximum 35 to 52 mm;
- thermocline thickness 0.15 to 0.21 m on every level, no mesh trend;
- the instantaneous field was not converged point by point (about 4 to 9 % of ΔT at 5 mm), because the jet
  and the internal waves are unsteady and the meshes drift out of phase.

**Decision (Saxam, 30 October).** All runs at 5 mm. The field-level uncertainty is reported, not hidden.
The November verification (section 5.2) replaced this older study with pre-registered limits.

**Defence.** Integral and engineering quantities (energy, profile, outlet, thermocline height) are
mesh-insensitive at 5 mm. The instantaneous field is not, but the largest 2.5 vs 5 mm field difference in
November (2.8 % of ΔT) is below the best ML field error (3.3 % median). A finer production mesh would cost
about 5 times more and would not change the benchmark conclusions.

**Planned but not delivered: a 3.33 mm subset of 128 designs as a multi-fidelity task.** It was stopped on
31 October (an outlet boundary condition fault blew up two runs) so the 5 mm batch could finish. Only 3 runs
exist. It is listed as not done.

### 3.3 PIMPLE settings and time step

**Production uses nOuterCorrectors 2 and maxCo 0.5.** An early test showed that 1 outer corrector is not
enough (median field difference 8.3 % of ΔT on 34 laminar runs). Section 5.3 tests 4 correctors and
maxCo 0.25. Five of six designs show no effect beyond the flow's own sensitivity; T0211 does.

---

## 4. Tank family: quality control and exclusions

**QC checks per run** (`scripts/qc_runs.py`):
- energy conservation (error as a share of the exchanged energy);
- velocity growth;
- temperature bounds.

**Results** on the frozen manifest (`thermbench_ml/manifest_full_h5mm.json`, created 2026-11-05):
- 1,211 OK, 1 WARN (T0393_lam, velocity growth 2.064 against a limit of 2.0; kept);
- energy conservation: median error 7.4e-5 of the exchanged energy;
- all 1,212 h5 files pass an integrity scan and match the manifest md5 sums;
- a production rerun reproduced the archived runs exactly (difference 0.00) in all six verification designs.

**Exclusions** (5 of 1,217 planned runs):

| Run | Reason |
|---|---|
| T0073_lam | QC energy check FAIL (5.86 % of exchanged energy) |
| T0765_lam, T0765_sst | discharge with the hot layer entirely above the outlet: almost nothing leaves, so the energy check cannot judge it (QC FAIL) |
| T0191_sst, T0882_lam | same design rule, QC OK |

The design rule (discharge with initial thermocline above the outlet's top edge is removed, both
turbulence variants) was fixed on 4 November, **before final training**.

**Defence of keeping T0393_lam.** Its WARN is marginal (2.064 vs 2.0). Verification (section 5.3) shows its
outlet behaviour is the same with a 0.01 % inlet change, so it is sensitivity of the flow (backflow events
at the outlet), not a numerical fault.

**Flagged labels.** T0211_sst and T0052_sst are kept but listed in `thermbench_ml/label_flags_tank.json`
(section 5.4). The flag file is separate so the frozen manifest and its md5 do not change.

---

## 5. Tank family: verification (pre-registered)

### 5.1 The pre-registered limits

Written and committed in `verification_criteria_2026-11-06.md` before any comparison existed:

| Quantity (test vs production rerun) | Agreement | Clear disagreement | Reason for the limit |
|---|---|---|---|
| Field RMSE, all snapshots, matched time | ≤ 1.5 % | > 3 % | 1.5 % is under half the best random-split ML error; 3 % is that error |
| Time-averaged field difference | ≤ 1.0 % | > 2 % | detects a systematic (not phase) difference |
| Horizontally averaged profile | ≤ 1.5 % | > 3 % | stratification without the lateral phase of the jet |
| Stored energy | ≤ 0.5 % | > 2 % | dataset conservation error ~1e-4; ML energy errors 0.5 to 1.5 % |
| Outlet temperature | ≤ 2 % | > 5 % | ML outlet errors 5 to 10 % of ΔT |
| Thermocline midpoint | ≤ 10 mm (2 cells) | > 25 mm | ML midpoint errors ~27 to 33 mm |

Further rules, all written in advance:
- Between the two columns: **borderline**, never reported as agreement.
- **Event windows:** a quantity that passes over the whole run but exceeds its limit in any window
  (before, around, after the outlet event) is borderline (added 7 November, 01:30 Nepal, before the runs it
  first applied to were all compared).
- **The perturbation run (inlet velocity × 1.0001)** is reported as physical sensitivity, never as a
  numerical noise floor. A mesh or setting difference inside it is reported as "not distinguishable from the
  sensitivity of the unsteady solution", never as "within noise" or "converged".
- **Coarse grids** (10 mm tank) are diagnostic only. An observed order or GCI is reported only if the three
  levels converge monotonically with an observed order between 0.5 and 3.

**Why these limits.** They are tied to the size of the ML errors the dataset will be used to judge. A label
difference smaller than half the best ML error cannot change a benchmark ranking; a difference as large as
the ML error could.

### 5.2 Mesh: 2.5 vs 5 mm (four designs)

| Design | Field | Profile | Time-avg field | Energy | Outlet | Midpoint | Inlet × 1.0001 (field) |
|---|---|---|---|---|---|---|---|
| T0408 lam (Re 2,014, Ri 31) | 0.34 % | pass | pass | 0.17 % | 1.43 % (2.03 % event window) | 0.5 mm | ~0 % |
| T0221 lam (Re 678, Ri 386) | 0.60 % | pass | 0.28 % | 0.42 % | 0.77 % | 0.8 mm | 0.39 % |
| T0243 SST (Re 18,626, Ri 5.8) | **1.70 %** | 0.92 % | 0.67 % | **0.96 %** | 1.30 % | pass | ≤ 0.11 % |
| T0551 lam (Re 1,259, Ri 55) | **2.76 %** | 0.81 % | 0.29 % | 0.23 % | 1.32 % | 1.1 mm | 1.85 % |

**Verdicts.**
- T0408: agreement, with the outlet borderline (event window).
- T0221: agreement on all quantities.
- T0243: field and energy borderline, all else agreement. The perturbation difference is tiny (≤ 0.11 %), so
  this is a genuine mesh effect: it lies on the thermocline interface and grows with time (0.41, 1.14, 1.99,
  2.49 % by quarter).
- T0551: field borderline (3.03 % in the early window). The perturbation alone moves the field by 1.85 %, so
  most of the 2.76 % is the flow's own sensitivity.
- 10 mm grid: clearly coarser. The three levels do not converge monotonically, so **no order and no GCI**.

**What we accept.** The 5 mm labels reproduce integral quantities within the limits. The field carries a
mesh uncertainty of up to about 2.8 % of ΔT, concentrated at the thermocline. The mesh is **not** called
converged.

### 5.3 Outer iterations, time step and perturbation (six designs)

Field RMSE in % of ΔT against the production rerun:

| Design | rep (inlet × 1.0001) | n4 (nOuterCorrectors 4) | co25 (maxCo 0.25) | Verdict |
|---|---|---|---|---|
| T0408 lam | ~0 | ~0 | ~0 | agreement |
| T0221 lam | 0.39 | 0.39 | 0.38 | agreement |
| T0243 SST | ≤ 0.11 | ≤ 0.11 | ≤ 0.11 | agreement |
| T0393 lam | 0.50 | 0.67 | 0.78 | field agreement; outlet borderline in every variant, rep included (2.87, 3.40, 2.85 %) |
| T0551 lam | 1.85 | 2.14 | 1.96 | field borderline, the same size as the flow sensitivity |
| **T0211 SST** (Re 5,396, Ri 3.9, discharge) | **0.47** | **7.38** | **7.32** | **clear disagreement** |

**T0211 analysis.**
- n4 and co25 agree with each other (2.49 %), both differ from production by 7.4 %, and rep differs by only
  0.47 %. So this is a numerical error of the production settings, not sensitivity.
- The error is a phase error in the tilting and sloshing of the thermocline interface after the cold jet
  reaches it.
- Other quantities: profile 1.9 % and time-averaged field 1.0 % (borderline); stored energy 0.26 to 0.43 %
  and midpoint 5 mm (agreement); outlet 2.0 to 2.4 % overall, 5.1 % around breakthrough.
- The production pressure residual does not single T0211 out (T0551 has a higher one), so the logs cannot
  be used to find similar runs.

### 5.4 Is T0211 one case or a regime? (two pre-registered tests)

**Test 1** (pre-registered 7 November, 10:30 Nepal). The four SST designs nearest T0211 in (log Re, log Ri),
covering both modes and inlet types. Rule: affected if n4 > 3 % **and** rep < 1.5 %.

| Design | n4 | rep | Under the rule |
|---|---|---|---|
| T0252 | 0.03 | 0.03 | not affected |
| T0256 | 0.01 | 0.02 | not affected |
| T0156 | 1.80 | 3.84 | not affected (sensitive) |
| T0052 | 6.77 | 1.68 | not affected (missed rep < 1.5 % by 0.18) |

The outcome (0 of 4) is kept on record as it stands. T0052 also had outlet 5.44 % (11.35 % in the event
window) and energy 1.08 % with n4. Its n4 difference is four times its rep difference, which the fixed rep
limit could not see.

**Test 2** (pre-registered 7 November, 13:45 Nepal, before any of its runs):
- **Sample:** wide SST designs (W ≥ 0.6 m, Ri < 10), 119 runs, excluding those already tested. 5 Ri bins
  per mode; from each bin the run with the smallest md5 of its run_id. Charge: T0988, T0492, T0828, T0851,
  T0036. Discharge: T0108, T0004, T0636, T0227, T0696. (A first draw gave only charge runs and was replaced
  before anything ran.)
- **Rule:** affected if n4 > 3 % **and** (rep < 1.5 % **or** n4 ≥ 2 × rep). The ratio condition was added
  because of T0052, so applying it to T0052 is post hoc and labelled as such.
- **Decision rule:** 0 of 10 affected means option A (report the regime as label uncertainty); 1 or more
  means report the share and decide between A and C (rerun the regime) with Saxam.

**Result.** 0 of 10 affected (binomial 95 % interval 0 to 31 %). In every design n4 and rep differ from the
dataset run by at most 0.05 % of ΔT in the field; energy by at most 0.01 %, outlet by at most 0.04 % of ΔT,
midpoint by at most 0.06 mm (`verification_data/regime2_*.json`).

**Conclusion and action (option A, applied as written).**
- Of the 15 wide, low-Ri SST designs tested, 2 show the error: T0211, and T0052 under the post hoc rule.
- The error is not systematic across the regime. The dataset is kept.
- T0211_sst and T0052_sst are flagged in `label_flags_tank.json` and the dataset card.
- T0156, T0551 and T0393 are listed there as sensitive but not flagged.

**Defence of option A rather than rerunning the regime.** A rerun at n4 would roughly double the cost of the
SST runs, and 12 of 14 tested neighbours show no effect at all (≤ 0.05 %). The two affected runs are
documented with their size, so users can exclude them. What we cannot do is find other such runs from the
logs; the 0 to 31 % interval is the honest bound.

### 5.5 Dataset-wide checks

**Laminar vs SST, all 192 design points run with both:**
- field difference median 3.9 % of ΔT, 10th to 90th percentile 0.7 to 8.3 %, maximum 17.8 %;
- energy median 0.6 %, outlet 2.4 % of ΔT, midpoint 3.4 mm;
- governed by stratification, not Re: Spearman with Ri −0.62, with Re +0.12;
- only 14 pairs are near-identical, mostly strongly stratified (median Ri 324).

So the closure choice matters, and the paired subset tests genuinely different closures.

**Near-wall resolution, all 588 SST runs** (first-cell y+ from Spalding's law, all wall cells and
snapshots):
- 60 % of wall cell-snapshots below 5, 38.5 % in the buffer layer (5 to 30), 1.6 % above 30;
- per-run maximum: median 35, up to 113 at the highest Re.

The buffer-layer share is a stated limitation of the high-Re SST runs.

---

## 6. Tank family: validation against experiment

**Why indirect.** The Scopus search (107 records screened) found no quasi-2D tank-charging experiment with
usable data. So the same solver, properties and turbulence treatment are validated in 3D against a real
tank, then used in 2D.

**Case: Lou et al. (2023), J. Energy Storage 71, 108017.**
- Cuboid tank 194 × 194 × 390 mm, central 10 mm top port, perforated baffle manifolds (37 orifices of radius
  8.05 mm, porosity 0.20; radius vs diameter resolved from the stated porosity).
- Charging at 1 L/min, 60 °C into 20 °C.
- Measured: jet penetration length h_j(t) from PIV (two tests), digitised to about ±3 mm.

**Our run.** Quarter-symmetry 3D, 230,156 cells, kOmegaSST, buoyantPimpleFoam, real properties, to 750 s.
h_j is taken from centreline v_y averaged over ±6.25 s, as in the PIV.

| t (s) | 50 | 150 | 250 | 350 | 450 | 550 | 650 | 700 |
|---|---|---|---|---|---|---|---|---|
| PIV mean (mm) | 108 | 129 | 138 | 160 | 172 | 181 | 201 | 211 |
| Lou's CFD (Fluent) | 74 | 92 | 108 | 125 | 142 | 158 | 176 | 185 |
| **Ours** | 105.8 | 120.5 | 138.1 | 156.1 | 173.8 | 193.1 | 211.5 | 222.5 |

**Agreement over all 14 times.**
- Ours: bias +2.4 mm, RMS 7.2 mm.
- Lou's own CFD: bias −29.7 mm.
- The two PIV tests differ by up to 18 mm, so our deviation is within the measurement spread.

**Mesh check.** Refining the lower baffle region (326,932 cells) changed h_j by at most 0.1 mm up to 300 s.
This is not a refinement of the jet region itself.

**What it supports.** The solver, properties and SST buoyancy treatment reproduce a measured buoyant jet in
a real tank. **What it does not support:** a direct validation of the 2D dataset, the laminar regime, or
the outlet temperature (Lou's outlet data are not yet extracted).

---

## 7. Tank ML benchmark: task, models, splits, metrics

### 7.1 Task

Given a tank's inputs and a time t*, predict the full temperature field at t*.
- **Inputs** (all known before the run): geometry (W, slot, port offset, type A/B), operation (charge or
  discharge, inflow speed, ΔT, cold temperature, pre-stratified start and its height), turbulence flag,
  Re, Ri, and the initial field.
- **Target:** θ = (T − Tc)/(Th − Tc) on the native 5 mm grid.

### 7.2 Models

| Model | Idea |
|---|---|
| initial | no change (lower bar) |
| 1D ideal stratification | plug flow with a sharp interface from the energy balance (MIX = 0) |
| kNN, RBF | interpolation in parameter space |
| FNO | Fourier neural operator, 4 layers, width 32, 16 modes |
| U-Net | 4-level U-Net, base width 32 |

Each neural architecture is trained in a **2 × 2 ablation**: plain / hybrid × own frame / canonical frame,
so 8 neural models, each on 4 splits × 3 seeds. FNO 60 epochs, U-Net 100 (U-Net was still improving between
60 and 100 epochs in the test pass, by up to 17 %). bf16, batch 16.

**Hybrid.** The network learns the correction to the plug-flow (1D ideal stratification) field.
*Defence:* the base supplies energy conservation and the front position at large scale; the network only
has to learn mixing and jet structure.

**Canonical frame.** A discharge run is a charge run turned 180° with hot and cold swapped (θ → 1 − θ).
Discharge runs are mapped into the charge frame on the way in and back before scoring, so every metric is in
the run's own frame.
- *Exactness:* exact under Boussinesq with constant properties; approximate with real properties.
- *Checks:* the transform is its own inverse (round-trip error 3e-8).
- *Evidence* (interim, 246 runs, 2 November, ablation on ood_mode): plain FNO 18.0 K, canonical-frame plain
  FNO 1.75 K, hybrid 2.98 K, hybrid in the canonical frame 0.66 K. The two ideas are complementary.
- *Novelty position:* building symmetries into networks for fluids is established (Wang, Walters & Yu
  2021, 2022; Siddani et al. 2021; Lino et al. 2022); we do not claim the method. We found no use of the
  charge/discharge symmetry in ML for thermal storage. arXiv still to be checked.

**Main model: FNO hybrid in the canonical frame, mean of 3 seeds.** Chosen as the main model on 2 November,
before the final results. Section 8.4 gives the comparison with U-Net.

### 7.3 Splits (`thermbench_ml/splits.py`)

Assignment is by **design point**, so laminar and SST twins of one design are never split across train and
test. It is fixed by parameters or a hash, so it does not depend on which runs finished.

| Split | Test set | Test runs | What it tests |
|---|---|---|---|
| random | 10 % of design points by hash | 131 | interpolation |
| ood_geom | W outside 0.33 to 0.93 m | 224 | width / aspect-ratio extrapolation in the same rectangular 2D geometry (not new geometry families) |
| ood_mode | all discharge runs; train on charging only | 363 | an operating mode never seen |
| ood_flow | Re > 9,007 (design 90th percentile) | 103 | faster inflow; **all of its test runs are SST**, so it tests Re extrapolation and the closure together |

Thresholds are fixed from `design_v2_full.csv`. Validation is 10 % of the remaining design points by hash.

### 7.4 Metrics (`thermbench_ml/metrics.py`)

- Field RMSE (% of ΔT, and K).
- Horizontal profile RMSE (what a 1D tank model is judged on).
- Thermocline midpoint error: recomputed from predicted and true fields and averaged only where both define
  it; definition mismatches are reported separately.
- Stored-energy error as a fraction of the tank's full capacity (not of the current stored energy, which
  goes to zero at the end of a discharge).
- Outlet temperature error in K (what a system simulation takes from the tank).

---

## 8. Tank ML results

### 8.1 Accuracy of the main model (every test run, 3-seed ensemble)

| Split | Field, median (mean) | Energy, median | Outlet T, median | Best interpolation (RBF), mean | 1D ideal stratification, mean |
|---|---|---|---|---|---|
| random | 3.3 (4.1) % | 0.24 % | 0.54 K | 8.7 % | 15.3 % |
| ood_geom | 3.5 (4.4) % | 0.23 % | 0.63 K | 10.8 % | 16.0 % |
| ood_mode | 3.7 (4.5) % | 0.28 % | 0.61 K | 64 % (fails) | 16.5 % |
| ood_flow | 8.7 (9.5) % | 0.70 % | 1.38 K | 15.1 % | 22.8 % |

- About half the error of the best interpolation baseline, a quarter of the 1D model.
- The accuracy carries over to unseen widths and to discharge, where interpolation fails.
- **Speed:** 1.45 s median per run (3 seeds, 120 snapshots) on a laptop RTX 4060, against a median 2.6 h of
  single-core CFD (10 to 90 %: 0.6 to 8.4 h). About 6,000 times faster in wall-clock time; the hardware
  differs, so it is not an equal-cost comparison.

### 8.2 Where it is weak

- Error grows as the jet overcomes stratification: Spearman with Ri −0.75 to −0.80; SST runs about twice the
  laminar error.
- Ri < 5 (12 % of the dataset): median error about 9 to 10 %; Ri ≥ 5: about 3 %.
- Every test run above 10 % error is an SST case with Ri below about 9.
- The model smooths large coherent vortices and wall short-circuits and misplaces the outlet breakthrough.
- **Overlap with label uncertainty:** the two flagged runs are test runs (T0211 in ood_mode, ML error 7.9 %;
  T0052 in ood_geom, 7.2 %). Their label uncertainty (7.4 % and 6.8 %) is the same size, so part of the
  measured ML error in this regime may be label error.

### 8.3 Does the model know when it is wrong? (three-seed spread)

| Split | Spearman ρ (spread, error) | Worst 10 % caught by top-10 % spread | Error > 10 % in upper-spread half | Error share in top-10 % spread cells |
|---|---|---|---|---|
| random | 0.86 | 11 / 13 | 4 / 4 | 74 % |
| ood_geom | 0.86 | 19 / 22 | 13 / 13 | 79 % |
| ood_mode | 0.82 | 29 / 36 | 20 / 20 | 78 % |
| ood_flow | 0.94 | 9 / 10 | 35 / 35 | 55 % |

**Calibration** (bound error ≤ k × spread; k fitted on each split's **validation** runs only, checked on
test runs; `capacity_2026-11-07/ml_calib_summary.json`):

| Split | k for 90 % | Test coverage, 90 % / 95 % | Constant bound, 90 % / 95 % |
|---|---|---|---|
| random | 4.0 | 91 % / 96 % | 87 % / 92 % |
| ood_geom | 3.5 | 88 % / 93 % | 84 % / 89 % |
| ood_flow | 3.7 | 90 % / 94 % | 19 % / 37 % |
| ood_mode | 3.2 | **71 % / 84 %** | 83 % / 93 % |

- In distribution and for unseen widths, "error ≤ about 4 × spread" holds at the stated rate and is about a
  third tighter than a constant bound.
- For faster inflow it keeps its coverage while a constant bound collapses.
- **For discharge (never trained) the spread under-covers (71 % at 90 %).** For ood_mode the bound is not
  reliable, and we say so.
- The raw spread is under-dispersed (about 0.38 of the error) and is only used through the calibrated
  factor.

**Correction on record.** An earlier draft claim said the ensemble "gives no warning because the seeds agree
when wrong". Saxam challenged it, and the analysis above shows it was wrong: the spread does track the
error. The claim was replaced.

### 8.4 All models (mean field error, % of ΔT, from stored per-run scores)

| Model | random | ood_geom | ood_mode | ood_flow |
|---|---|---|---|---|
| fno | 4.13 | 4.70 | 64.8 | 10.2 |
| fno_canon | 3.92 | 4.48 | 12.4 | 9.6 |
| fno_hybrid | 4.17 | 4.76 | 13.0 | 10.4 |
| **fno_hybrid_canon** | 4.02 | **4.44** | 4.48 | 9.83 |
| unet | 3.68 | 7.02 | 67.0 | 9.48 |
| unet_canon | 3.48 | 5.48 | 9.85 | 9.04 (1 seed) |
| unet_hybrid | 3.83 | 5.39 | 13.3 | 9.88 (1 seed) |
| unet_hybrid_canon | 3.62 | 6.23 | **4.37** | 9.19 (2 seeds) |

The last 5 U-Net ood_flow seeds finished on 7 November and are **not yet merged** into this table. Final
tables, with design-level confidence intervals, come last.

**Reading.**
- Without the canonical frame, every model fails on ood_mode (13 to 67 %). With the frame and the hybrid
  base, both architectures reach about 4.4 %.
- U-Net hybrid_canon has a lower mean error than FNO on random (3.62 vs 4.02), ood_mode (4.37 vs 4.48) and,
  on 2 seeds, ood_flow. Ensemble medians: random 2.97 vs 3.34 for U-Net.
- FNO is clearly better on unseen widths (4.44 vs 6.23 mean; medians 3.46 vs 4.75).

**Defence of keeping FNO as the main model.**
- The choice was made before the final results and is not changed after seeing them.
- The U-Net advantage on three splits is small (0.1 to 0.4 points of mean error). Its disadvantage on
  ood_geom is large (1.8 points), and width extrapolation is the case where a resolution-independent
  operator should help.
- Both are reported in full; the paper will not claim FNO is the better architecture overall.

**Open for the reviewer:** whether to present both architectures as co-equal results instead of naming one
"main" model.

### 8.5 Horizontal stitching lines

Visible in predicted fields of the hardest cases. Cause: the hard step in the plug-flow base at the
interface. The two step rows hold 4 to 8 % of the error on 0.8 % of the area. Bridging them changes the
field RMSE by at most 0.04 points. Documented; no retraining.

---

## 9. PCM family: design and model

**Physics.** A PCM slab melted from a heated left wall, with 0 to 5 metal fins on that wall: the basic cell
of plate and finned latent stores. What matters: melt rate and melt time, heat input, the convective melt
front shape, and the effect of fins.

**Design** (`scripts/pcm_full.csv`, 500 cases, Sobol):

| Parameter | Range or values |
|---|---|
| Material | n-octadecane (Tm 28 °C, Pr ~50) / lauric acid (melting range 43.5 to 48.2 °C, Pr ~100), 50 / 50 % |
| Wall superheat | 8 to 30 K (above the range midpoint for lauric) |
| Subcooling | 0.5 to 20 K (below the solidus) |
| Width W (H = 100 mm) | 20 to 60 mm (A = 1.7 to 5) |
| Fins | N = 0 to 5 (30 % unfinned), length 0.2 to 0.8 W, thickness 1 to 4 mm |
| Orientation | side heated 0° / 45° / heated from below 90°, 70 / 15 / 15 % |

Ra_H about 1e8 to 7e8 (laminar), Ste about 0.04 to 0.37. Both validation cases sit inside the design box.

**Why two materials only.** Each material has its own experiment (section 10). A third, unvalidated
material would weaken the claim that every family is validated.

**Why the ranges were narrowed** (2 November). The first cost estimate was wrong by about 4 times: gentle
heating in a wide box takes 30 to 40 h of physical time to melt. Dropping 5 to 8 K superheat and widths
above 60 mm cut the cost from about 12,400 to about 3,100 core-hours. This is stated as a coverage limit.

**Model.**
- buoyantPimpleFoam with OpenFOAM's enthalpy-porosity melting source (Voller & Prakash).
- Constant properties (the Vogel & Thess "B-2D" set), Boussinesq buoyancy about Tm.
- Mushy-zone constant: 1e6 for octadecane (as Vogel & Thess), 5e6 for lauric acid with its melting range
  (as Safari/Kamkari 2022); this combination is what fixed the plain-wall validation (section 10).
- **Fins: conducting aluminium (k = 130),** decided after the fin validation (conducting and isothermal fins
  agree within 0.01 for one fin).
- Mesh 0.5 mm (200 rows, padded to W_MAX = 60 mm).
- Run until melt fraction 0.995 (automatic stop).
- **Pressure fix (option A, 4 November):** p_rghFinal relTol 0, maxIter 200 for all 500 cases, after the
  GAMG pressure solve was found not to converge in some cases (P0124). Corrected reruns use PCG + DIC for
  both pressure solves (maxIter 2,000).

**Why 0.5 mm.** The 1 mm mesh melted 8 to 11 % faster mid-melt (against a 3 % threshold), so it was
rejected. 0.5 mm agreed with 0.25 mm within about 1 % on the Vogel case. Later checks (section 11) found a
larger 0.5 vs 0.25 mm difference in finned and lauric cases; that is reported, not hidden.

---

## 10. PCM family: validation against experiments

**n-octadecane: Vogel & Thess (2019)**, rerun with the final solver set-up:
- against their 2D model B-2D: mean absolute deviation 0.009 in liquid fraction, largest +0.015, inside the
  ±0.02 digitising accuracy; full melt 201 vs about 210 min;
- against the experiment: mean absolute deviation 0.030 (the experiment melts faster because the real cell
  gains heat through its other walls, which is expected for ideal 2D walls);
- no temperature overshoot (before the pressure fix, production cases reached +16 to 19 K above the wall).

**Lauric acid: Kamkari & Shokouhmand (2014), 70 °C wall, at exactly the dataset settings:**

| Case | Mean deviation | Largest | Full melt | Experiment |
|---|---|---|---|---|
| Plain wall, 0.5 mm (case 1, 7 Nov) | 0.028 mean abs. | +0.054 at 50 min | 194.7 min | ~195 min |
| 1 fin, 0.5 mm (before the pressure fix) | 0.07 | +0.12 at 50 min | 161 min | ~160 min |
| 3 fins, 0.5 mm (before the pressure fix) | +0.059 (10 to 100 min) | +0.105 at 30 min | 115.5 min | ~125 min |
| **3 fins, 0.25 mm (case 2, 7 Nov)** | +0.045 | +0.077 at 30 min | 121.3 min | ~125 min |

The pressure fix moves the melt curve by less than 0.005, so the pre-fix 0.5 mm runs remain valid
references. Tilted cases (45°, heated from below; Kamkari, Shokouhmand & Bruno 2014) are within ±0.08.

**What it shows.**
- Plain wall: validated (same full-melt time, within ±0.06).
- Finned walls: about 0.1 too fast in the first hour, then converging; 1-fin full melt matches; 3-fin full
  melt 8 % early at 0.5 mm, 3 % early at 0.25 mm. The 3-fin fin benefit is 0.05 too strong (0.59 vs 0.64).
- About a quarter of the early 3-fin excess is mesh; the remaining +0.08 in the first hour is model error.
  Likely causes, not tuned: no-slip surface at the fin cell centres rather than the fin faces, and 3D
  damping by the experiment's front and back walls.
- For comparison, Kamkari's own 2D model reached 5.4 % maximum deviation for 3 fins. Ours is larger early.

**Defence of not tuning.** The settings were frozen before the fin deviation was measured, and the deviation
is reported. Tuning the mushy constant or fin model to one experiment would hide model error and risk
over-fitting to a digitised curve.

**Caveat.** The plain-wall agreement at 0.5 mm (195 vs 195 min) may partly reflect cancellation between mesh
error (0.5 mm melts early) and model error. This will be stated in the paper.

---

## 11. PCM family: verification, solver repair and QC

### 11.1 Mesh

- **G131** (lauric, unfinned, 1.0 / 0.5 / 0.25 mm): t99 4,200 / 4,536 / 4,746 s. Monotonic, observed order
  0.68, extrapolated t99 about 5,096 s. GCI 15.4 % at 0.5 mm, 9.2 % at 0.25 mm. So the 0.5 mm dataset melts
  about 11 % too fast for this case.
- **G301** (octadecane): t99 3,600 / 3,920 / 4,200 s. Monotonic but observed order 0.19, outside the
  pre-registered 0.5 to 3, so **no GCI**. 0.5 mm about 7 % early.
- **P0021:** non-monotonic, no GCI.
- **Spot check, 6 dataset cases, 0.5 vs 0.25 mm:** t99 1.0 to 8.7 % later on the finer mesh (median 4.9 %),
  the same sign in all six; melt curves within 0.036; field RMSE 4.2 to 7.6 % of ΔT; the melt front shifts
  0.3 to 0.8 mm on average, and 36 to 76 % of the squared error lies in the front band (5 to 16 % of the
  area). The bias is not specific to thin fins.

**Decision (option A, Saxam).** Keep all 500 cases at 0.5 mm as a consistent numerical reference; report the
melt-time discretisation uncertainty and its direction (0.5 mm melts early); release the fine-mesh runs as a
subset. A 0.25 mm subset of 50 to 100 cases (option B) was not run: the 3-fin case at 0.25 mm (+5 %) falls
inside the spot-check range, so it would re-measure a quantified effect. All 500 at 0.25 mm (option C,
about 24,000 core-hours) was rejected.

**Why this is acceptable for a benchmark.** ML models are judged against the 0.5 mm labels, all made the
same way. The mesh bias is systematic in sign (all cases melt early), so it shifts the labels consistently
rather than adding noise that would change model rankings. The labels are not claimed to be mesh-converged
truth.

### 11.2 Pressure-solver failures and corrected reruns

- **Found:** in some cases (P0124 first) the GAMG p_rgh solve did not converge (residual ~0.85, every solve
  at the iteration cap). `pcm_qc.py` only checked exported fields, so a solver-convergence QC was added
  (`scripts/pcm_solver_qc.sh`: FAIL if over 20 % of solves hit the cap or mean residual > 0.2; WARN above
  2 % or 0.05; the cap is read from each case's own settings).
- **Corrected reruns** (PCG + DIC) vs originals, four complete cases: melt time −2.1 to +0.9 %, melt curves
  within 0.032, field 1.9 to 8.0 % of ΔT, because the melt front shifts about a millimetre. Failed originals
  are replaced by their reruns.
- **WARN sensitivity test (pre-registered).** Six WARN cases, the two most severe of each kind, rerun with
  PCG + DIC. Material change if field > 2 % of ΔT, front shift > 0.5 mm, or t99 change > 1 %. Rule: if one
  kind changes materially, every case of that kind is rerun.
  - Results (field): P0075 2.54 % (material change), P0048 0.47, P0319 1.03, P0007 1.34, P0164 1.21,
    P0376 0.04.
  - P0075 is of the "capped iterations with high residual" kind, so all 17 cases of that kind were rerun,
    as the rule required. All passed QC.
  - The other two kinds are kept as WARN (39 cases).

### 11.3 Output errors found and repaired

- **Series bug in 41 resumed cases:** postProcessing series were split across restart folders and partly
  overwritten with NUL bytes; the exporter read only the first part, giving no melt time and energy-balance
  errors of 1 to 99 %. Fields were complete and correct (every melt curve rises to 0.995). Series merged
  (`scripts/pcm_repair_series.py`, `scripts/pcm_merge_series_nul.py`), metrics recomputed, backups kept.
  Energy-balance errors now 0.01 to 0.5 %.
- **P0495** was corrupted after a resume (temperatures above the wall) and was rerun from t = 0.

---

## 12. PCM family: accepted inventory and freeze

**Inventory** (`pcm_inventory_2026-11-07.csv`): 703 case folders across seven machines reduce to exactly
one accepted output per case.

**Acceptance rules:**
1. DONE, not a moved-away placeholder, `pcm_qc.py` OK or WARN, final solver set-up.
2. A corrected rerun replaces the dataset run.
3. A run whose pressure solves failed (solver QC FAIL) is never accepted.
4. Identical copies: one chosen by machine order; no accepted case has a copy that differs in size.

**Result: 500 of 500 accepted.** pcm_qc 498 OK, 2 WARN; 34 corrected reruns; 39 solver WARN kept under the
pre-registered rule.

**Freeze (in progress, 7 November).** The accepted runs are being copied into one clean folder, because the
superseded originals of corrected reruns still exist in the old folders and the loader takes the first copy
it finds. Each file is checked against the inventory (size, QC status, solver setting) before the manifest
is written with md5 sums. (A first copy attempt transferred nothing for 441 runs because of a scripting
error; the verification step caught it before anything was frozen.)

**PCM ML.** Not trained yet. Planned: FNO and U-Net, plain and hybrid (correction to a
conduction-then-convection front baseline), 6 splits (random, unseen fin count, stronger driving, unseen
material both ways, unseen orientation) × 3 seeds. A 63-case rehearsal on the random split gave FNO 2.40 K
and U-Net hybrid 2.82 K; these are not benchmark numbers.

**Defence of the PCM time input.** The model's time input is τ = t / t_ref, where t_ref is an **a priori**
melting-time scale computed from the inputs only (energy over a laminar Nu ~ Ra^0.25 heat rate). The true
melting time is an output and is never an input.

---

## 13. Process integrity: rules, deviations and errors we found in our own work

**Rules we follow.**
- Limits and decision rules are committed before the results they judge. Later additions carry their date
  and reason; the originals stay.
- Post hoc reclassifications are labelled as such (T0052).
- Final ML tables come last; no model choice is changed after seeing them.
- Only done and tested work goes into replies; what remains is listed.

**Errors in our own work, found and corrected (disclosed):**

| What | How found | Effect and fix |
|---|---|---|
| OpenFOAM buoyancyTurbSource sign in the Boussinesq k term | code check, 30 Oct | production uses the compressible path; bug report drafted |
| Outlet boundary condition fault in the 3.33 mm subset | two runs blew up, 31 Oct | subset stopped; 5 mm batch used the fixed outlet |
| Verification inputs taken from an unsnapped design list (`design_h5mm_full.csv`) | cross-check, 6 Nov | three pilot verification sets (T0243, T0393, T0211) repeated with the correct inputs; T0408 unaffected |
| PCM pressure solve not converging (P0124 and others) | solver logs | pressure fix for all 500, solver QC added, failed cases rerun |
| PCM series bug in 41 resumed cases | P0228 energy balance 60 % | series merged, metrics recomputed |
| PCM solver QC flagged PCG reruns falsely as FAIL | its fixed 200-iteration cap | cap now read from each case |
| ML claim "no warning when wrong" | challenged by Saxam | analysis showed the opposite; claim replaced |
| First PCM freeze copy moved nothing for 441 runs | file check before freezing | script fixed, copy redone |

---

## 14. What we claim and what we do not

**We claim:**
1. An open, documented 2D CFD dataset of 1,212 stratified-tank runs and 500 PCM-melting runs, with design,
   QC and verification records.
2. Tank labels reproduce integral quantities within pre-registered limits on the mesh and numerical
   settings; the field carries a mesh uncertainty of up to about 2.8 % of ΔT; two runs carry a known
   numerical-setting uncertainty of about 7 % and are flagged.
3. The tank solver set-up reproduces a measured 3D buoyant jet (bias +2.4 mm, RMS 7.2 mm), better than the
   original authors' CFD.
4. PCM labels match the plain-wall experiments, and finned walls within about 0.1 early and 3 to 8 % on
   full-melt time; the 0.5 mm melt time is early by about 1 to 11 %, quantified.
5. A neural-operator surrogate predicts a full tank transient in about 1.5 s with a median field error of
   3.3 to 3.7 % on three of four splits, half the error of the best interpolation baseline, and transfers
   to discharge only through the charge/discharge symmetry.
6. The three-seed spread ranks the error (ρ 0.82 to 0.94) and, after calibration on validation runs, gives
   bounds that hold at the stated rate except for the unseen operating mode.

**We do not claim:**
- mesh convergence of either family, or a GCI where the levels do not allow it;
- 3D validity of the 2D labels, or direct validation of the 2D tank dataset;
- that the perturbation runs measure a numerical noise floor;
- that FNO is the better architecture overall;
- that the spread bound is reliable for an unseen operating mode;
- that other T0211-type runs can be identified from the logs;
- novelty of building symmetry into neural networks.

---

## 15. What is not done yet

**Tank:**
- Merge the last 5 U-Net ood_flow seeds; design-level confidence intervals for the final tables.
- Confirmation set, only after the models are frozen.
- DeepONet and transformer baselines (after the main tank and PCM results).
- Outlet-temperature and laminar comparison with Lou et al. (data not yet extracted); a second tank
  experiment with discharge (Shah & Furbo 2003) if needed.
- The 3.33 mm multi-fidelity subset (planned, not delivered).
- Release items: licence, environment specification, README, version tag and DOI.

**PCM:**
- Finish the freeze (manifest with md5), then train and evaluate all models.

**Both:** arXiv novelty check before submission; the paper itself (written last).

---

## 16. Questions we would like the reviewer to challenge

1. **Pre-registered limits.** Are limits tied to half the best ML error a sound basis for "agreement", or
   should they be tied to physics (for example, the experimental uncertainty)?
2. **Option A for T0211.** With 2 of 15 wide low-Ri SST designs affected and a 0 to 31 % interval on the
   pre-registered sample, is flagging enough, or should the low-Ri SST regime be rerun at n4?
3. **T0052 reclassification.** Is our handling (outcome kept on record, ratio rule used only going forward
   and labelled post hoc) adequate?
4. **Mesh.** Is "integral quantities within limits, field uncertainty up to 2.8 %, not converged" an
   acceptable basis for 5 mm labels in an ML benchmark?
5. **PCM mesh bias.** Is a consistent early-melt bias (median 4.9 %, up to 11 %) acceptable for benchmark
   labels if it is stated, or does it require a correction or a fine-mesh label subset?
6. **Indirect validation.** Is a 3D validation of the solver set-up, plus a 2D dataset, defensible for the
   tank family?
7. **Main model.** Should FNO be the "main" model when U-Net has slightly lower mean error on three splits?
8. **Calibration.** Is fitting k on validation runs and reporting test coverage sufficient, and how should
   the ood_mode under-coverage be presented?
9. **Overlap of ML error and label error** in the fast-jet regime: how should the benchmark score models
   there (exclude flagged runs, report separately, or both)?
10. **Anything missing** a reviewer at a thermal or ML venue would expect before the final tables.
