# Response to "Mesh Verification: Recommendations for Compute-Efficient Scoping" (2026-11-06)

Prepared by the project assistant for Saxam, 2026-11-06 about 22:50 Nepal time. Every number is from
output produced today. Nothing was stopped, restarted or changed because of the note.

**Criteria record.** The acceptance limits for each quantity were committed before the first comparison
was seen: `verification_criteria_2026-11-06.md`, commit 1a63b11, 22:13 Nepal. The first comparison finished
after that, at about 22:30.

## 0. First evidence: T0408 (complete, both closures)

**The case.** Discharge from a pre-stratified start, lid/bottom slots (40 mm), W = 0.28 m (aspect ratio
3.6), Re 2,014, dT 18.3 K, duration 54.5 s (t* = 0.32).

**Runs.**
- Mesh: 5 mm (11,200 cells), 2.5 mm (44,800) and 10 mm (2,800).
- Settings, all on 5 mm: production rerun (p2), nOuterCorrectors 4 (n4), maxCo 0.25 (co25), and inlet
  velocity x 1.0001 (perturbation).
- All serial, as the dataset runs.

**Mapping.** Finer fields are block-averaged onto the coarser grid by the exact integer ratio (2 x 2 or
4 x 4 cells). Times match the reference snapshots, with linear time interpolation if needed (all offsets
here are 0). Snapshots with t > 0 only.

| Comparison (laminar; SST identical to 2 digits) | Field RMSE % dT (K) | By quarter of the run (%) | Horizontal profile % dT | Time-mean field % dT | Max (K) | Stored energy % | Outlet T RMS % dT | Thermocline mid (mm) |
|---|---|---|---|---|---|---|---|---|
| p2 vs dataset run | 0.00 (0.00) | 0 / 0 / 0 / 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0 |
| Perturbation (inlet x 1.0001) vs p2 | 0.00 (0.00) | 0 / 0 / 0 / 0 | 0.00 | 0.00 | 0.01 | 0.01 | 0.01 | 0.0 |
| nOuter 4 vs 2 | 0.00 (0.00) | 0 / 0 / 0 / 0 | 0.00 | 0.00 | 0.05 | 0.00 | 0.05 | 0.0 |
| maxCo 0.25 vs 0.5 | 0.01 (0.00) | 0 / 0 / 0 / 0 | 0.00 | 0.01 | 0.23 | 0.00 | 0.18 | 0.0 |
| **2.5 mm vs 5 mm** | **0.34 (0.06)** | 0.2 / 0.5 / 0.3 / 0.3 | 0.27 | 0.19 | 3.16 | 0.17 | **1.43** | 0.5 |
| 2.5 mm vs 5 mm with maxCo 0.25 | 0.34 (0.06) | 0.2 / 0.5 / 0.3 / 0.3 | 0.27 | 0.20 | 2.93 | 0.18 | 1.52 | 0.5 |
| 10 mm vs 5 mm | 0.37 (0.07) | 0.4 / 0.6 / 0.2 / 0.0 | 0.28 | 0.15 | 3.01 | 0.62 | 1.60 | 0.9 |
| 2.5 mm vs 10 mm | 0.52 (0.10) | 0.5 / 0.8 / 0.2 / 0.2 | 0.40 | 0.23 | 4.10 | 0.66 | 2.75 | 1.5 |

**Reading.**
1. **Reproducible.** The dataset run is reproduced exactly by the current code, so the archived data are
   reproducible for this case.
2. **Settings.** Iterations and time step have no measurable effect.
3. **Mesh.**
   - The 2.5 mm difference is spatial: it is unchanged when the 5 mm run also uses the smaller time step.
   - Against the criteria fixed beforehand, 2.5 vs 5 mm is in "agreement" on every quantity:
     - field 0.34 % (limit 1.5 %);
     - profile 0.27 % (limit 1.5 %);
     - time-mean field 0.19 % (limit 1.0 %);
     - energy 0.17 % (limit 0.5 %);
     - outlet 1.43 % (limit 2 %; the outlet is the closest to its limit);
     - thermocline 0.5 mm (limit 10 mm).
4. **Perturbation.** The perturbation produced no measurable change. In this case there is no phase drift
   to separate, so the perturbation run tells us nothing about drift here.
5. **Closures.** In this case the SST and laminar solutions differ by only 0.04 % of dT (0.01 K). The
   stable stratification suppresses the modelled turbulence, so this pair tests mesh sensitivity twice
   rather than for two different closures.

**Limits of this evidence.** T0408 is the mildest pilot case: short, pre-stratified, transitional Re and
in effect laminar. It shows nothing about jet-dominated or long laminar evolution. It is screening
evidence for one design.

## 1. Status of each tank pilot case

Production numerics on every mesh: PIMPLE nOuterCorrectors 2, maxCo 0.5, maxDeltaT 0.5, serial.

| Case | Configuration | Mesh check | Duration, outlet event | Status 22:50 Nepal | Expected finish (Nepal) |
|---|---|---|---|---|---|
| T0408_lam / _sst | discharge, pre-stratified, slots, W 0.28, Re 2,014 | 10 / 5 / 2.5 mm | 54 s | **complete** | done |
| T0243_sst | charge, side wall, pre-stratified, Re 18,600 (ood_flow test) | 5 / 2.5 mm (geometry not on a 10 mm grid) | 41 s; outlet T leaves its start value (10 % of its total change) at 14 s, 34 % of the run | 2.5 mm at about 9 % | about 04:00 Sat |
| T0221_lam | discharge, side wall, pre-stratified, 20 mm slot, Re 678 (ood_mode test) | 10 / 5 / 2.5 mm | 1,149 s; outlet event at 414 s, **36 %** | 2.5 mm at about 3 % | outlet event about 05:00 Sat; end about 18:00 Sat |
| T0551_lam | charge, lid slots, uniform start, 20 mm slot, Re 1,259 | 10 / 5 / 2.5 mm | 1,050 s; outlet event at 832 s, **79 %** | 2.5 mm at about 1.5 % | outlet event about 04:00 Sun; end about 13:00 Sun |
| T0211_sst, T0393_lam | stage 1A only (2.5 mm would take about 40 h each) | none | | | |

The 5 mm p2 runs for T0221 and T0551 are running on pc4. Because T0408 reproduced its dataset run exactly,
partial comparisons can also use the dataset files directly, with reproducibility confirmed once p2 ends.

## 2. Answers to the eight questions

**Q1. Which long laminar case to complete: modify (complete both; if only one, T0551).**
- If only one could finish, it should be **T0551**. Its outlet event comes at 79 % of the run, so no
  partial comparison can cover it. T0221's outlet event comes at 36 % and is covered by its partial run
  by Saturday 05:00.
- But see Q7: finishing both costs nothing that is needed elsewhere.

**Q2. Evidence to stop the other case early: none yet.**
- No long-case comparison exists yet.
- The earliest meaningful check is T0221 after its outlet event (Saturday morning), using the
  pre-registered limits and the per-window time history.

**Q3. The 1.5 % threshold: agree with the note's caution; done.**
- Separate limits for the time-averaged field, horizontal profile, stored energy, outlet temperature and
  thermocline position were recorded before any result (commit 1a63b11).
- The field limit (1.5 %) is under half the best random-split ML error (3.4 %).
- The outlet limit (2 %) is the one T0408 came closest to (1.43 %). The outlet is therefore the metric to
  watch in the long cases.

**Q4. Does the perturbation isolate phase drift: no, as the note says.**
- In T0408 neither the perturbation nor a same-input repeat produced any difference. The p2 run
  reproduces the dataset run exactly, so serial runs here are deterministic and a same-input repeat
  measures nothing.
- The diagnostic is now computed alongside the raw error: the horizontally averaged temperature profile
  T(y, t), which removes lateral jet and wave phase but keeps the stratification.
  - In T0408 the profile difference (0.27 %) is about 80 % of the raw field difference (0.34 %), so the
    mesh difference there is mostly vertical structure, not lateral phase.
- If the long laminar runs show growing differences, the next cheap step is a 3-member 5 mm ensemble
  (inlet x 1.0001, x 1.001, initial T + 0.01 K). A mesh difference inside the ensemble spread would then
  be reported as "not distinguishable from perturbation sensitivity", not as negligible.

**Q5. Time step and PIMPLE across meshes: partly established.**
- maxCo is fixed, so the time step roughly halves at 2.5 mm.
- The 5 mm maxCo 0.25 run isolates the time-step part. For T0408 it changes nothing (0.01 %), and the
  2.5 mm comparison is unchanged when made against it. The mesh effect there is therefore spatial.
- nOuterCorrectors is fixed at 2 on all meshes; 4 iterations at 5 mm changes nothing for T0408.
- **Not tested:** 4 iterations at 2.5 mm. The same checks for the other cases come from stage 1A
  (T0221, T0551 and T0243 at maxCo 0.25 and nOuter 4 are running on pc4).

**Q6. 10 mm tank and 1.0 mm PCM grids: agree, diagnostic only for now.**
- **Tank.** The 10 mm grid has 4 cells across T0408's slot but only 2 across T0221's and T0551's. For
  T0408 the field differences do not shrink with refinement (0.37 % for 10 vs 5, 0.34 % for 5 vs 2.5), so
  no order or GCI for the field. Stored energy shrinks by 3.6x (0.62 % to 0.17 %), consistent with
  roughly second order, but only absolute maxima were compared, so monotonic convergence is not
  established. Report the differences, not a GCI.
- **PCM P0021.** 1.0 mm melts at about 1,900 s against about 1,530 s at 0.5 mm and 1,545 s at 0.25 mm:
  far off and non-monotonic, so 1.0 mm is outside the asymptotic range for that case.
- **PCM G131 (lauric, unfinned).** 4,202 s at 1.0 mm and 4,518 s at 0.5 mm, so finer melts later, the same
  direction as 0.5 vs 0.25 mm in the dataset spot check. The 0.25 mm result is due Saturday.
- **PCM verdict.** G131 and G301 are unfinned with 22 and 26 cells across at 1.0 mm. A GCI is reported only
  if all three levels are monotonic with an order between 0.5 and 3 (pre-registered).

**Q7. Finish both or stop both: finish both.**
- The lab's cores are not needed for anything else this weekend. The incremental cost is waiting time
  only (to Sunday about 13:00); nothing waits for these cores.
- Both runs together cover a pre-stratified discharge (early outlet event) and a uniform charge (late
  outlet event), each at a different inlet type.
- **Reason to stop one:** only if stage 1A fails and the lab is needed for reruns. Then T0221 would stop
  first, after its outlet event, reported as interval-limited.

**Q8. Smallest additional plan: no new runs are required for the claims below; one cheap optional
addition.**
- Running already: 2.5 mm T0243, T0221, T0551, and stage 1A (iterations, time step and perturbation for
  all 7 pilot runs).
- **Optional (not started; needs Saxam's approval):** two short high-Re SST jet cases at 2.5 mm, T0307_sst
  (Re 20,184) and T0771_sst (Re 16,638), about 2 to 3 h each on the lab. They broaden the jet-dominated
  coverage that T0408 lacks, at little cost.

## 3. Claims (wording as in the note's section 7)

- **Now defensible:** "For one transitional design (T0408, 54 s, both closures), the 5 mm and 2.5 mm
  solutions differed by 0.34 % of dT in field RMSE, 0.17 % in stored energy, 1.4 % of dT in outlet
  temperature and 0.5 mm in thermocline position; 4 outer iterations and maxCo 0.25 changed the 5 mm
  solution by at most 0.01 % of dT."
- **Not defensible now:** any statement about the full dataset, long laminar runs, jet-dominated SST runs
  or late-time behaviour; "mesh-converged"; "within the noise floor".
- **Wording:** "inter-grid discrepancy" until a formal estimate is justified.

## 4. Decisions for Saxam

1. Finish both long laminar runs (recommended), or stop T0221 after its outlet event.
2. Approve or decline the two optional high-Re SST mesh runs.

## Correction (2026-11-07, about 00:05 Nepal)

The verification runs took their inputs from `design_h5mm_full.csv`, but the dataset was built from
`design_v2_full.csv` (geometry on a 10 mm grid). For T0221, T0551 and T0408 the two lists are
identical, so their results stand, including the exact reproduction of T0408. Three pilot runs differ
slightly:

| Run | Field | Wrong list | Dataset |
|---|---|---|---|
| T0243_sst | port offset | 0.115 m | 0.12 m |
| T0393_lam | port offset | 0.045 m | 0.04 m |
| T0211_sst | width | 0.67 m | 0.68 m |

Their first verification sets are self-consistent, but they verify a near neighbour of the dataset run.
The 1.79 % "p2 vs dataset" difference for T0243 is this 5 mm port shift, not irreproducibility. All
three are being rerun with `design_v2_full.csv`: on pc3 (T0243, including 2.5 mm) and on pc4 (T0211,
T0393), in `~/of_runs/tank_verify_v2`.
