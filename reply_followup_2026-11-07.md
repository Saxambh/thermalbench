# Reply to the review of 7 November 2026

Thank you for the review. We agree with the priorities and with not regenerating either dataset. Below is
what has been done in response; work in progress is listed only as remaining.

## Done

**1. T0408 outlet event window recorded as borderline.**
- The outlet-temperature difference of 2.03 % of ΔT around breakthrough is now classified as a borderline
  event-window result, not a pass.
- We made this a general rule, added to the pre-registered criteria: a quantity within its limit over the
  whole run but above it in any time window (before, around or after the outlet event) is classified as
  borderline.

**2. One authoritative accepted output per PCM case.**
- We built a case-by-case inventory of all 500 physical cases.
- The 514 figure in our earlier report counted QC checks of case folders, not cases. A full scan finds
  703 folders, comprising:
  - copies of moved runs;
  - superseded originals;
  - partial and corrected reruns;
  - an archive of a machine that went offline.
- **Acceptance rules:**
  - an output is accepted only if it finished, passed the field QC (OK or WARN) and used the final solver
    set-up;
  - a corrected rerun replaces the original;
  - a run whose pressure solves failed is never accepted;
  - among identical copies one is chosen, and the rest are kept as provenance only.
- **Current state:**

  | | Cases |
  |---|---|
  | Accepted | 489 (479 QC OK, 10 WARN) |
  | Corrected rerun pending | 6 |
  | Long dataset runs not yet finished | 3 |
  | Newly found to need a corrected rerun | 2 |

  - Of the accepted cases, 5 are corrected reruns and 38 carry the time-series repair.
  - Energy-balance error: median 0.15 %, largest 1.6 %.
  - No accepted case has a differing duplicate.
- **The two new cases (P0419, P0442).** Their pressure solves hit the iteration cap in 28 % and 19 % of
  solves. They were found when the solver check was extended to runs that had finished since the first
  scan.
- The published manifest will be generated from this inventory, with superseded attempts listed as
  provenance.

**3. Field-level sensitivity as the criterion for WARN cases, fixed before any rerun.**
- We agree that a solver problem can change the field labels while leaving the melt time almost
  unchanged. The four corrected reruns show exactly this: melt time −2.1 to +0.9 %, field RMSE 1.9 to
  8.0 % of ΔT.
- The field differences come from sub-millimetre shifts of the melt front. 55 to 72 % of the squared
  temperature error lies in the front band, which covers 8 to 15 % of the cavity.
- **Test design.** Rather than rerunning all 59 WARN cases, we test the six most severe:
  - capped iterations with a high residual: P0075, P0048;
  - capped iterations only, thin fins: P0319, P0007;
  - high residual only: P0164, P0376.
- **Material change**, in any one of:
  - field RMSE > 2 % of ΔT;
  - mean melt-front shift > 0.5 mm (one cell);
  - melt-time change > 1 %.
- **Decision rule:**
  - no material change: all WARN cases are kept;
  - changes confined to one kind of warning: every case of that kind is rerun;
  - changes spread across kinds: all 59 are rerun.
- The rule was committed before any of these reruns exists.

**4. Corrected tank inputs.** The three pilot designs affected by the design-list mismatch (T0243,
T0393, T0211) are being repeated with the production design inputs. No result from their first runs will
be used as evidence.

**5. Confirmation set.** It will be generated only after model choices are frozen, and kept out of all
architecture and hyperparameter decisions.

## Remaining

- Tank verification of T0243, T0221 and T0551 (and T0211, T0393) against the pre-registered limits, with
  the time-window analysis. No further tank designs unless these results identify a gap.
- PCM:
  - finish the corrected reruns (6 pending, plus P0419 and P0442) and the 3 long dataset runs;
  - run the WARN sensitivity test;
  - then rebuild the inventory and freeze the manifest.
- PCM three-level mesh comparison and Kamkari validation at exactly the dataset settings.
- Final ML results with design-level statistics, then the untouched confirmation set.
