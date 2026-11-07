# Discharge subset analysis: result (7 November 2026)

**Protocol:** `PROPOSAL.md` revision 3, committed as 0334509 before any subset score was computed. The
analysis (`analysis.py`) was written after that commit and run once, as specified, with no deviations.
Output: `analysis_result.json` and `analysis_log.txt`.
Input scores: `results_merged/ood_mode.json` (merged final results of all workers), md5 `ad863d497c1ecfb40b5628bbfc41cb27`.

**What this is:** a pre-registered subset analysis of an existing benchmark. The subset is the 259
ood_mode (discharge) test runs, from 215 designs, with no identified pre-freeze evaluation exposure. These
runs were part of the ood_mode aggregate already reported, and the hypotheses were written after that
aggregate was seen. It is not a prospective confirmation on new designs.

## Primary result (Holm over 4 tests, α = 0.05)

| Hypothesis | Architecture | Mean improvement, pp of ΔT [marginal 95 % interval] | Designs improved | p (one-sided) | Holm p | |
|---|---|---|---|---|---|---|
| H1: canonical frame added to the fixed hybrid model | FNO | **+9.17** [+8.33, +10.02] | 96 % | 0.0001 | 0.0004 | supported |
| H1 | U-Net | **+9.74** [+8.84, +10.64] | 95 % | 0.0001 | 0.0004 | supported |
| H2: hybrid + canonical model vs ideal stratification | FNO | **+12.53** [+11.59, +13.47] | 98 % | 0.0001 | 0.0004 | supported |
| H2 | U-Net | **+12.61** [+11.65, +13.55] | 98 % | 0.0001 | 0.0004 | supported |

- **p-values:** 0.0001 is the floor of the null-centred bootstrap: (1 + 0) / 10,001, meaning no null
  resample reached the observed mean.
- **Inference:** the intervals and p-values treat designs as replicates of a broader population of
  comparable cases. The mean improvements describe these 215 designs exactly.
- **Sensitivity:** without the flagged run T0211_sst (214 designs), every mean estimate changes by less
  than 0.01 pp (largest 0.0077 pp) and all four hypotheses remain supported. (Corrected after review:
  an earlier version gave the looser bound "at most 0.03 pp".)

## Descriptive (field error, % of ΔT, seed means: mean / median, run-weighted)

These means give each run equal weight. The primary tests give each design equal weight, so differences of
the means below do not reproduce the primary effects. Both are correct for their purpose.

| Model | Subset (259 runs, 215 designs) | Remaining ood_mode test runs (104 runs, 88 designs) |
|---|---|---|
| fno_hybrid | 14.02 / 14.30 | 10.39 / 9.86 |
| **fno_hybrid_canon** | **5.03 / 4.16** | 3.12 / 2.64 |
| unet_hybrid | 14.47 / 14.72 | 10.53 / 10.02 |
| **unet_hybrid_canon** | **4.96 / 4.26** | 2.90 / 2.45 |
| ideal_stratified | 17.41 / 17.75 | 14.30 / 14.48 |
| Composition | SST 58 %, Ri < 5 14 % | SST 27 %, Ri < 5 5 % |

All models have higher errors on the subset. It contains about twice the share of SST runs and nearly three
times the share of Ri < 5 runs, which are the conditions where every model is weakest (dossier §8.2). The
size of the improvement is similar in both groups: the frame cuts the error by 64 % to 66 % on the subset,
against 70 % to 72 % on the remaining runs. The difference between the groups is descriptive and is not
tested.

## What may be said (per §6 of the protocol)

"On 215 discharge designs with no identified pre-freeze evaluation exposure, adding the canonical frame
lowered the mean design-level field error of the fixed hybrid model by 9.2 pp of ΔT for FNO (marginal 95 %
interval 8.3 to 10.0) and by 9.7 pp for U-Net (8.8 to 10.6). The hybrid + canonical models improved on
ideal stratification by 12.5 pp and 12.6 pp. All four effects are supported after Holm correction. These
runs were part of the previously reported discharge aggregate, so this is a pre-registered subset analysis,
not an independent prospective confirmation."
