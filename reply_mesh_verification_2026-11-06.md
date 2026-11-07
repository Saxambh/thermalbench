# Reply: mesh verification scoping (6 November 2026)

Thank you for the note. We checked each recommendation against our actual runs. Below are the first
complete results, the status of the remaining cases, and our position on your eight questions.

**Acceptance limits fixed in advance.** Before looking at any comparison, we recorded acceptance limits
for each quantity separately and committed them to version control. The quantities are: raw field RMSE,
time-averaged field, horizontally averaged temperature profile, stored energy, outlet temperature and
thermocline midpoint. The field limit (1.5 % of ΔT) is under half our best random-split ML error (3.4 %).
The limits will not be changed after the fact; any later change will be recorded with its date and reason.

## First complete result: T0408 (laminar and k-ω SST)

**The case.** Discharge from a pre-stratified start, lid/bottom slots of 40 mm, tank width 0.28 m, Re 2,014,
ΔT 18.3 K, duration 54 s.

**Runs.** The same design was run:
- on 10, 5 (production) and 2.5 mm meshes;
- at 5 mm, also with 4 instead of 2 PIMPLE outer iterations, with maxCo 0.25 instead of 0.5, and with the
  inlet velocity multiplied by 1.0001.

**Mapping.** Finer fields were block-averaged onto the coarser grid by the exact integer ratio and compared
at matched physical times.

| Comparison | Field RMSE, % ΔT (K) | Horizontal profile, % ΔT | Stored energy, % | Outlet T, % ΔT | Thermocline midpoint, mm |
|---|---|---|---|---|---|
| Production rerun vs archived dataset run | 0.00 (0.00) | 0.00 | 0.00 | 0.00 | 0.0 |
| Inlet velocity × 1.0001 | 0.00 (0.00) | 0.00 | 0.01 | 0.01 | 0.0 |
| 4 vs 2 outer iterations | 0.00 (0.00) | 0.00 | 0.00 | 0.05 | 0.0 |
| maxCo 0.25 vs 0.5 | 0.01 (0.00) | 0.00 | 0.00 | 0.18 | 0.0 |
| **2.5 mm vs 5 mm** | **0.34 (0.06)** | 0.27 | 0.17 | **1.43** | 0.5 |
| 2.5 mm vs 5 mm (5 mm at maxCo 0.25) | 0.34 (0.06) | 0.27 | 0.18 | 1.52 | 0.5 |
| 10 mm vs 5 mm | 0.37 (0.07) | 0.28 | 0.62 | 1.60 | 0.9 |

Laminar and SST results agree to two digits in every row. The maximum local difference between 2.5 and
5 mm is 3.2 K.

**What we conclude:**
1. **Reproducible.** The archived dataset run is reproduced exactly by the current code.
2. **Iterations and time step have no measurable effect** in this case.
3. **The 2.5 mm vs 5 mm difference is spatial.** It is unchanged when the 5 mm reference also uses the
   smaller time step.
4. **All quantities fall within the pre-registered limits.** The outlet temperature is the closest
   (1.43 % against 2 %).
5. **The perturbation run cannot separate drift here.** The 0.01 % inlet perturbation produced no
   measurable change, so this case has no phase drift to separate. As you pointed out, that run is not a
   noise floor.

**Limitations.** T0408 is the mildest pilot case: short, transitional, and its SST and laminar solutions
differ by only 0.04 % of ΔT because the stable stratification suppresses the modelled turbulence. It is
screening evidence for one design. It says nothing about long laminar evolution or jet-dominated SST flow.

## Status of the remaining tank cases

| Case | Configuration | Duration and outlet event | Expected completion of the 2.5 mm run |
|---|---|---|---|
| T0243_sst | charge, side-wall inlet, pre-stratified, Re 18,600 | 41 s; outlet temperature starts to change at 34 % of the run | about 7 November, 04:00 Nepal time |
| T0221_lam | discharge, side-wall inlet, pre-stratified, 20 mm slot, Re 678 | 1,149 s; outlet change at 36 % | outlet event about 7 Nov, 05:00; end about 7 Nov, 18:00 |
| T0551_lam | charge, lid inlet, uniform start, 20 mm slot, Re 1,259 | 1,050 s; outlet change at 79 % | outlet event about 8 Nov, 04:00; end about 8 Nov, 13:00 |

"Outlet change" is the time at which the outlet temperature has moved 10 % of its total change.

The iteration, time-step and perturbation runs for these cases (and for two further pilot cases, T0211_sst
and T0393_lam, which are not in the mesh check because a 2.5 mm run would take about 40 h each) finish over
the weekend.

## Our position on your questions

**1. Which long laminar case to complete: modify (complete both; if only one, T0551).**
If only one could be completed, it should be T0551, because its outlet event occurs at 79 % of the run
and no partial comparison can capture it. T0221's outlet event (36 %) is covered by its partial run.
Since the compute is available, we will complete both (see 7).

**2. Evidence to stop the other case early: not yet.**
No long-case comparison exists yet. The first meaningful check is T0221 after its outlet event, judged
against the pre-registered limits and the time history per window.

**3. The 1.5 % threshold: agree.**
It is one of several limits, all set in advance, including separate limits for outlet temperature (2 % of
ΔT), stored energy (0.5 %) and thermocline midpoint (10 mm, two cells).

**4. Does the perturbation isolate phase drift: agree that it does not.**
- A same-input repeat is uninformative for us. Serial runs are deterministic: the rerun matched the archive
  exactly.
- We therefore added the horizontally averaged profile T(y, t), which removes lateral jet and wave phase
  but keeps the stratification. In T0408 it retains about 80 % of the raw field difference, so the mesh
  difference reflects vertical structure rather than phase.
- If the long runs show growing differences, we will add a three-member 5 mm perturbation ensemble and
  report any mesh difference inside its spread as "not distinguishable from perturbation sensitivity",
  never as negligible.

**5. Time step and iterations across meshes: partly established.**
- The time step is Courant-limited and roughly halves at 2.5 mm.
- The 5 mm run at maxCo 0.25 isolates this effect; for T0408 it is zero, so the mesh effect is spatial.
- Outer iterations are fixed at 2 on all meshes, and 4 iterations at 5 mm change nothing.
- **Not tested:** 4 iterations at 2.5 mm. The other cases are covered by the iteration and time-step runs
  in progress.

**6. Coarse grids: agree, diagnostic only.**
- **Tank, 10 mm.** The grid has two cells across the 20 mm slots of the long cases. For T0408 the field
  differences do not decrease with refinement (0.37 % for 10 vs 5 mm, 0.34 % for 5 vs 2.5 mm), so we report
  no order or GCI for the field. Stored-energy differences decrease by a factor of 3.6, but monotonic
  convergence is not established.
- **PCM, 1.0 mm.** It is clearly outside the asymptotic range for one case: a 1.0 mm melt time of about
  1,900 s against about 1,530 s at 0.5 mm and 1,545 s at 0.25 mm.
- **When we will report a GCI.** Only if all three levels are monotonic with an observed order between 0.5
  and 3, as recorded in advance.

**7. Finish both or stop both: finish both.**
The machine is not needed for other work, so the incremental cost is elapsed time only (to 8 November).
The two cases are complementary: a pre-stratified discharge with an early outlet event, and a uniform
charge with a late one, with different inlet types. We would stop one early only if the hardware were
needed for corrective reruns, and then report it with its verified interval.

**8. Smallest additional plan.**
- No new runs are needed beyond those in progress.
- **Possible addition:** two short high-Re SST jet cases at 2.5 mm (Re about 20,000 and 16,600, roughly
  2 to 3 hours each), to cover the jet-dominated regime that T0408 does not represent.

## Claims

- **Defensible now:** "For one transitional design (T0408, 54 s, both closures), the 5 mm and 2.5 mm
  solutions differed by 0.34 % of ΔT in field RMSE, 0.17 % in stored energy, 1.4 % of ΔT in outlet
  temperature and 0.5 mm in thermocline position; four outer iterations and maxCo 0.25 changed the 5 mm
  solution by at most 0.01 % of ΔT."
- **Not claimed:** anything about the full dataset, long laminar runs, jet-dominated SST runs or late-time
  behaviour, and no claim of mesh convergence or of being within a noise floor. Until a formal estimate is
  justified, we use "inter-grid discrepancy".

We will send the long-case and PCM three-level results, in the per-case format you proposed, as they
complete.
