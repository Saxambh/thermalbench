# Discharge subset analysis: pre-registration (revision 3, 7 November 2026)

**Status: revision 3, APPROVED by Saxam on 7 November 2026 and committed before any subset score was
computed.** No score on the subset has been computed. After approval this file, `make_set.py` and
`confirmation_set.json` are committed unchanged before `analysis.py` is written or run. The analysis then
runs once, as written. Any later change is logged as a deviation with its reason.

**What this is:** a pre-registered subset analysis of an existing benchmark. The 259 runs already
contributed to the published ood_mode aggregate, and the hypotheses are written after that aggregate was
seen. It is not a prospective confirmation on new designs; that would need designs outside all previously
examined results.

## 1. Why

The canonical frame was introduced after the interim discharge results of 2 November. So the headline
discharge result (hybrid + canonical models about 4.4 %, 13 to 67 % without the frame) is partly a
development result. This analysis asks whether the discharge advantage persists on designs that played no
recorded part in development.

## 2. The subset (`confirmation_set.json`, built by `make_set.py`)

**Rule:** every ood_mode test run whose design appears in no evaluation made before the model freeze, in any
split.

- **Model freeze:** commit d42ce92, 4 November 13:29. It fixes the training code and `run_final.sh`.
  Changes since then to the training, data, split and scoring code are docstrings and added interpolation
  baselines only (checked with `git diff d42ce92 HEAD`).
- **Exposure is counted from two sources:**
  - (a) recorded per-run scores in every pre-freeze results folder;
  - (b) the reconstructable membership of the one aggregate-only pre-freeze evaluation.
- **Pre-freeze evaluations, and what they informed:**

| Evaluation | Date | Informed | Runs (designs) exposed |
|---|---|---|---|
| testpass | 1 Nov | pipeline test pass | 48 (47) |
| interim | 2 Nov | ablation that led to the canonical frame | 116 (107) |
| modediag | 2 Nov | discharge diagnostics; canonical frame adopted; main model chosen | 88 (82) |
| epochcheck 60 / 150 | 3 Nov | epoch choice | 65 (59) each |
| rehearsal | 4 Nov 08:32 | full-pipeline rehearsal | 102 (85) |
| n1 pilot | 31 Oct | first pilot, aggregate scores only | 3 of its 5 test designs reconstructed |

- **Checks on the audit** (the script stops with FAIL on any of them):
  - every expected pre-freeze folder exists and yields results;
  - every entry has a per-run list without duplicates;
  - in each file, at least one entry lists exactly the recorded test size, every other entry is a subset
    of it, and the union equals it;
  - where the evaluation kept its run list (modediag), the test set rebuilt from ids alone equals the
    recorded ids exactly (72 and 21 runs).
- **Why some entries are shorter:** a results file collects entries from successive sessions, and its
  recorded test size is that of the last session. Entries from earlier sessions, when fewer runs had
  finished, list fewer runs. This affects 4 files: interim random, rehearsal random, testpass ood_geom and
  testpass ood_mode. In all four, every shorter list is a subset of the full one.
- **What cannot be checked:**
  - The test size of an earlier session was not recorded, so its per-run list is accepted as recorded.
  - The other folders kept no run list, so their membership is checked against the recorded test size
    only, not rebuilt.
  - The 2 unidentified n1 pilot runs.
  - n1 recorded only aggregates. Its run folder still holds 34 of its 53 runs, and the random split is fixed
    by design. So 3 test designs (T0551, T0713, T0806) are recovered and excluded. The other 2 cannot be
    identified, which is a stated limit.
- **Not counted as exposure:** evaluations after the freeze. These are the data-efficiency runs
  (6 November) and the paired-reference and capacity analyses (7 November); none informed a model choice.
  T0211_sst's final per-run score was examined in the paired-reference study on 7 November, after the
  freeze.
- **Unit of exclusion: the design.** A design is excluded if any of its runs (laminar or SST, either mode)
  appears in a pre-freeze evaluation.
- **Result:** 259 of the 363 ood_mode test runs, from 215 designs (175 designs exposed). The stricter audit
  left the list unchanged. Of the 259:
  - 149 are SST;
  - 36 have Ri < 5;
  - 44 designs contribute two runs;
  - T0211_sst, the flagged run, is included.
- **What the set does not cover:** cases looked at only through plots or informal diagnostics are captured
  only where they were scored per run, and 2 pilot test runs are unidentified. So the set is described
  throughout as "designs with no identified pre-freeze evaluation exposure", not "designs never seen".
- **Availability, checked from ids only (no score read):** all 3 seeds of fno_hybrid, fno_hybrid_canon,
  unet_hybrid and unet_hybrid_canon, and the ideal_stratified baseline, have per-run scores for all 259 runs.
  If a seed were missing, the neural paired comparisons would use only the seeds present in both models.

## 3. Hypotheses

For each architecture A in {FNO, U-Net}:

| | Question | Comparison |
|---|---|---|
| **H1(A)** | Does adding the canonical frame to the fixed hybrid model lower mean design-level discharge field error? | A_hybrid minus A_hybrid_canon |
| **H2(A)** | Does the completed surrogate improve on the 1D ideal-stratification model? | ideal_stratified minus A_hybrid_canon |

- H1 tests the frame added to one fixed base model. It does not establish that the frame is the only route
  to discharge accuracy.
- The improvement is positive when hybrid_canon is better. Every result is reported as the paired
  improvement in percentage points of ΔT.

## 4. Analysis (fixed in advance)

- **Metric and models:**
  - field error `rmse_theta`, in percent of ΔT (mean per-snapshot RMS, every 10th snapshot), from the
    stored final per-run scores; no new predictions;
  - neural models: mean of the 3 seeds per run, as in §8.4 of the dossier.
- **Design differences:** average the runs of each design for each model, then form one paired difference
  d_j per design.
- **Point estimate:** the mean of d_j over the 215 designs, weighting designs equally. This describes these
  215 designs exactly.
- **Effect-size interval:**
  - ordinary (uncentred) paired bootstrap over designs, 10,000 resamples, seed 20261107;
  - percentile 95 % interval, labelled marginal (not multiplicity-adjusted).
- **p-value, null-centred bootstrap:**
  - centre the differences, e_j = d_j − mean(d);
  - draw 10,000 resamples of e over designs, seed 20261108;
  - count the resamples whose mean is ≥ the observed mean(d);
  - one-sided p = (1 + count) / (10,000 + 1).
- **Multiplicity:** Holm over all 4 tests (H1 and H2 for both architectures), family-wise α = 0.05.
  Holm stays valid under the dependence between the tests; for example, the two H2 tests share a
  baseline.
- **Supported** means Holm-adjusted p < 0.05.
- **Interpretation:** the inference treats designs as replicates of a broader population of comparable
  cases.

## 5. Sensitivity and descriptive reporting (no pass/fail)

- **Sensitivity:** repeat all 4 tests without T0211_sst. Remove that run first, then recompute its design
  mean from the remaining sibling run if one exists, or drop the design if not.
- **Descriptive:**
  - mean and median field error of each model on the subset;
  - the same for the 104 remaining ood_mode test runs (designs exposed before the freeze), side by side;
  - the composition of both groups (SST share, Ri < 5 share).
- **Not included:**
  - **Calibration coverage:** the ood_mode under-coverage is already known (71 % at the 90 % level).
  - **FNO against U-Net:** the paper makes no claim either way.

## 6. What may be said

- **H1 supported for both architectures:** "the canonical frame improved both hybrid models on discharge
  designs with no identified pre-freeze evaluation exposure". The paper states the number of designs, the
  mean improvement and its marginal 95 % interval.
- **H2 supported:** the same form of sentence for the improvement over ideal stratification.
- **Not supported:** the paper reports it and presents that claim as exploratory.
- **Every outcome** is reported in full in the main text, and the subset is not redefined.
- **Not claimed:** independent prospective confirmation.

## 7. Changes after review

1. **Exposure rule:**
   - Cut at the model freeze, so the post-freeze data-efficiency runs no longer count. Their designs return,
     which is the reason for 259 runs instead of 251.
   - The aggregate-only n1 pilot is now reconstructed and counted (3 designs excluded).
   - The set is described literally.
   - The T0211 post-freeze inspection is stated.
2. **Hypotheses:** H1 narrowed to the comparison actually made, and effect sizes in percentage points
   reported for both.
3. **Holm:** kept over all 4 tests.
4. **p-value:** now a null-centred bootstrap with (1 + count) / (B + 1). Effect-size intervals come from
   ordinary paired resampling and are labelled marginal.
5. **Revision 3, after the second review:**
   - Replaced the non-empty-list assertion with the membership checks in §2.
   - The script now fails if an expected folder is missing or yields no results.
   - The set is renamed "designs with no identified pre-freeze evaluation exposure".
   - The ID list is unchanged (259).
6. **Additions in revision 2:**
   - an id-only seed availability check, with a common-seed rule;
   - the T0211 sensitivity rule specified run-first.
