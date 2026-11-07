# Reply: T0211 regime test and Kamkari 3-fin case at 0.25 mm (7 November 2026)

This covers only completed and tested work.

## 1. Does the T0211 numerical error extend to other tank designs?

**Background.** T0211 (SST, Ri 3.9, discharge) changed by 7.4 % of ΔT in the field with 4 outer iterations
instead of 2, while a 0.01 % inlet change moved it by only 0.47 %. We tested whether neighbouring designs
share this error.

**Test, fixed in advance** (verification_criteria_2026-11-06.md, addendum "regime extent"):
- **Sample.** Wide SST designs (W ≥ 0.6 m, Ri < 10), 119 runs, excluding the designs already tested. Five Ri
  bins per operating mode; from each bin the run with the smallest md5 hash of its run_id. Charge: T0988,
  T0492, T0828, T0851, T0036. Discharge: T0108, T0004, T0636, T0227, T0696.
- **Runs.** Each design rerun with nOuterCorrectors 4 (n4) and with inlet velocity × 1.0001 (rep), and
  compared with its dataset run.
- **Rule.** A design is affected if n4 field RMSE > 3 % of ΔT and either rep < 1.5 % or n4 ≥ 2 × rep.
- **Decision rule.** 0 of 10 affected: the regime is reported as label uncertainty (option A). One or more:
  the share is reported and rerunning the regime is considered.

**Result.** 0 of 10 designs are affected (binomial 95 % interval 0 to 31 %). In every design, n4 and rep
differ from the dataset run by at most 0.05 % of ΔT in the field. Stored energy differs by at most 0.01 %,
outlet temperature by at most 0.04 % of ΔT and thermocline midpoint by at most 0.06 mm.

**Earlier test of four nearby designs** (same n4 and rep runs): T0252 and T0256 agree (≤ 0.03 %); T0156 is
sensitive (n4 1.80 %, rep 3.84 %); T0052 differs by 6.77 % with n4 against 1.68 % with rep. Under the rule
written before that test, T0052 was not affected; under the later rule, which adds the ratio condition
because of T0052, it would be. We state that this reclassification was made after the result.

**Conclusion.** The error is not systematic across the regime. Of all 15 wide, low-Ri SST designs tested, 2
show it (T0211, and T0052 under the later rule). The dataset is kept as it is. T0211 and T0052 are reported
as examples of label uncertainty in the fast-jet regime and will be flagged in the manifest and dataset
card. As noted before, the production run's residuals do not single these cases out, so the flag cannot be
extended to unseen cases from the logs.

## 2. PCM mesh: Kamkari 3-fin case at 0.25 mm

Same dataset settings (melting range 43.5 to 48.2 °C, mushy constant 5e6, conducting Al fins), compared
with Kamkari et al. Fig. 6 (digitised, ±0.02) at 10 to 100 min:

| Mesh | Mean deviation | Largest | Full melt (0.995) |
|---|---|---|---|
| Experiment | | | about 125 min |
| 0.5 mm | +0.059 | +0.105 at 30 min | 115.5 min (−8 %) |
| 0.25 mm | +0.045 | +0.077 at 30 min | 121.3 min (−3 %) |

- Refining from 0.5 to 0.25 mm lengthens the melt by 5 %, the same direction as in all other tests (0.5 mm
  melts early) and inside the range of the six-case spot check (+1 to +8.7 %).
- About a quarter of the early deviation is mesh; the remaining +0.08 in the first hour is model error, as
  reported in the validation note.
- The 0.5 mm run predates the pressure fix, which moves the melt curve by less than 0.005.

**Consequence.** The 500 PCM cases stay at 0.5 mm. The mesh uncertainty is reported from the three-level
sets and the spot check, and this run is added to the released fine-mesh subset. A 0.25 mm subset of 50 to
100 cases was considered and not run, because it would re-measure an effect already quantified.

## What's left

- Flag T0211 and T0052 in the tank manifest and dataset card.
- PCM manifest freeze, then PCM ML training.
- Remaining U-Net training runs (ood_flow seeds), design-level confidence intervals, then the confirmation
  set after the models are frozen.
