# Verification criteria, fixed before any mesh or iteration result was seen (2026-11-06, 22:25 Nepal)

Written before any stage 1A or mesh-check output had been compared (first comparison, T0408, was still
waiting on its runs). Purpose: the limits cannot be adjusted to the observed results. Any later change is
added below with its date and reason, and the original limits stay in the record.

Applies to the tank pilot (stage 1A: nOuterCorrectors 4, maxCo 0.25, inlet x(1+1e-4)) and the tank mesh
check (2.5 mm and 10 mm against 5 mm), all compared with the 5 mm production rerun (p2) of the same design.

## Reference scales (observed before this date)

- Best test-set ML field RMSE (% of dT), tank: random 3.4, ood_geom 4.4, ood_mode 4.2, ood_flow 9.0.
- nOuterCorrectors 1 vs 2 (34 laminar runs): median field RMSE 8.3 % of dT.
- October mesh study (5 vs 2.22 mm, 2 cases, older numerics): mean tank T within 0.02 K; thermocline height
  mean 15 mm, max 52 mm; instantaneous field 4 to 9 % of dT.

## Quantities and limits

Each quantity is judged on its own; a pass on one does not excuse a fail on another.

| Quantity (test vs p2) | Agreement | Clear disagreement | Reason for the limit |
|---|---|---|---|
| Field RMSE, all snapshots t > 0 (% of dT), raw, matched physical time | <= 1.5 % | > 3 % | 1.5 % is under half the best random-split ML error (3.4 %); 3 % is that error |
| Time-averaged field difference, RMS (% of dT) | <= 1.0 % | > 2 % | diagnostic of a systematic (not phase) difference; stricter because averaging removes drift |
| Horizontally averaged T profile T(y,t), RMSE (% of dT) | <= 1.5 % | > 3 % | stratification without lateral phase of the jet and internal waves |
| Stored energy, max abs difference / max abs stored-energy change | <= 0.5 % | > 2 % | dataset energy-conservation error is ~1e-4; ML energy errors are 0.5 to 1.5 % |
| Outlet temperature series, RMS (% of dT) | <= 2 % | > 5 % | ML outlet errors are ~1.5 to 2.5 K (5 to 10 % of a 25 K dT) |
| Thermocline midpoint, mean abs difference where both defined | <= 10 mm (2 cells) | > 25 mm | cell size 5 mm; ML midpoint errors are ~27 to 33 mm |
| Thermocline midpoint defined in one run but not the other (share of snapshots) | <= 5 % | > 15 % | |

Between the two columns: borderline. The run continues (if running) and the result is reported as
borderline, not as agreement.

## How the physical-perturbation run (inlet x 1.0001) is used

It is reported as physical-perturbation sensitivity, not as a numerical noise floor. A mesh or setting
difference within the perturbation sensitivity is reported as "not distinguishable from the sensitivity of
the unsteady solution to a 0.01 % inlet change", never as "within numerical noise" or "mesh-converged".
The criteria above apply to the raw differences regardless of the perturbation result.

## Partial-duration comparisons

A comparison over part of a run is reported with its verified interval in seconds and in t* and whether
outlet breakthrough had occurred in that interval. It supports only a claim about that interval.

## Coarse grids

The 10 mm tank grid and the 1.0 mm PCM grid are diagnostic. An observed order or GCI is reported only if
the three levels converge monotonically and the observed order lies between 0.5 and 3; otherwise the
inter-grid differences are reported as they are.

## Addendum 2026-11-07, about 00:50 Nepal: extra diagnostics (no pass limits)

Added at the collaborator's request, after the limits above were fixed. They are reported next to the
pre-registered quantities and carry no pass/fail limit, so they cannot be tuned to the results:

- **Tank:**
  - thermocline thickness, MIX and stratification number (mean and maximum difference where both runs
    define them, and the share of snapshots defined in only one run);
  - outlet backflow (share of outlet cells with velocity into the tank);
  - solver indicators (time steps, mean time step, p_rgh residual and iterations, maximum Courant number,
    execution time);
  - error-field maps at three moments (before, at and after the outlet event).
- **PCM:**
  - melt-front position difference (mean and 95th percentile, mm);
  - share of the squared temperature error lying in the mushy/front band, against that band's share of
    the area.

## Addendum 2026-11-07, about 01:30 Nepal: event windows and WARN sensitivity (collaborator note of 7 Nov)

**Event windows (tank).**
- A quantity within its limit over the whole run but above it in any time window (before, around or
  after the outlet event) is classified **borderline (event window)**, not pass.
- First instance: T0408, 2.5 vs 5 mm, outlet temperature 2.03 % of ΔT in the outlet-event window.

**WARN sensitivity (PCM), fixed before any of these reruns exists.**
- **Sample:** six accepted cases with solver-QC WARN, the most severe two of each kind:
  - capped iterations with a high residual: P0075 and P0048;
  - capped iterations only: P0319 and P0007 (thin fins);
  - high residual only: P0164 and P0376.
- **Test:** rerun each with PCG + DIC for both pressure solves and compare with the accepted dataset run.
- **Material change**, in any one of:
  - field RMSE > 2 % of ΔT (half the smallest 0.5 vs 0.25 mm mesh discrepancy seen, 4.2 %);
  - mean melt-front shift > 0.5 mm (one cell);
  - t99 change > 1 %.
- **Rule:**
  - if no case shows a material change, all WARN cases are kept;
  - if cases of one kind do, every WARN case of that kind is rerun;
  - if the changes are spread over the kinds, all 59 WARN cases are rerun.

## Addendum 2026-11-07, about 10:30 Nepal: is the T0211 failure one case or a regime? (fixed before these runs)

T0211_sst failed: n4 and co25 each differ from production by 7.4 % of ΔT field RMSE, agree with each other
(2.5 %), and the inlet x 1.0001 run differs by 0.5 %. Test: the four dataset SST designs nearest T0211 in
(log Re, log Ri) that cover both modes and both inlet types: T0156 (discharge B), T0256 (discharge B),
T0052 (charge B, wide), T0252 (charge A). Each is run with n4 and with rep (inlet x 1.0001), compared with
its dataset run (p2 reproduced the dataset exactly in all five pilot designs).
- **Affected design:** n4 field RMSE > 3 % of ΔT **and** rep field RMSE < 1.5 % (a numerical error that
  the solution's sensitivity cannot explain). If both are high, it is reported as sensitivity, not as affected.
- **Outcome:** 0 of 4 affected: T0211 is reported as an isolated label error of known size. 1 or more:
  the regime is affected; the extent and any SST reruns are decided with Saxam before anything is regenerated.

## Addendum 2026-11-07, about 13:45 Nepal: extent of the wide, low-Ri SST regime (fixed before these runs)

**Outcome of the first regime test.**
- Under the rule above, 0 of 4 designs were affected: T0252, T0256 and T0156 were not; T0052 had n4 6.77 %
  and rep 1.68 %, so it missed the rep < 1.5 % condition by 0.18.
- That outcome is kept on record as it stands.
- T0052 nevertheless resembles T0211 (n4 four times rep; outlet 5.44 %). Both affected-looking designs are
  wide (0.68 and 0.96 m), while the narrow ones (0.36, 0.42 m) were unaffected. Saxam chose to measure the
  regime (option B).

**Sample.** Wide SST dataset runs (W ≥ 0.6 m) with Ri < 10, excluding the six designs already tested
(119 runs: 85 charge, 34 discharge). For each mode, the runs are split into 5 equal bins by Ri, and from each
bin the run with the smallest md5 hash of its run_id is taken:
- charge: T0988, T0492, T0828, T0851, T0036;
- discharge: T0108, T0004, T0636, T0227, T0696.

(A first draw without mode balancing gave only charge runs and was replaced before anything ran.)

**Runs.** Each design gets n4 and rep, compared with its dataset run.

**Rule for these runs.**
- A design is **affected** if n4 field RMSE > 3 % of ΔT **and** either rep < 1.5 % **or** n4 ≥ 2 × rep.
  The ratio condition is added because T0052 showed that a fixed rep limit can miss a numerical error four
  times larger than the sensitivity.
- Under this rule T0052 would be affected; that reclassification is post hoc and is labelled as such.
- A design with n4 > 3 % but n4 < 2 × rep is reported as sensitive.

**Outcome.**
- 0 of 10 affected: the regime is reported as label uncertainty (option A), with T0211 and T0052 as
  examples.
- 1 or more: the affected share (with a binomial 95 % interval) is reported, and A against C (rerunning the
  regime) is decided with Saxam.

**Result (2026-11-07, about 15:45 Nepal).** All 10 designs are unaffected. For every design, n4 and rep differ
from the dataset run by at most 0.05 % of ΔT in the field, with energy, outlet and midpoint differences
near zero (verification_data/regime2_*.json). 0 of 10 affected (binomial 95 % interval 0 to 31 %), so under
the rule above the regime is reported as label uncertainty (option A), with T0211 and T0052 as examples.
