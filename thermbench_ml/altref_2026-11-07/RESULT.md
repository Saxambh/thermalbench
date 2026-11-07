# Paired alternate-reference scoring of the tank models (7 November 2026)

**Question** (independent review, section 5.2). Do the ML scores and the FNO/U-Net ranking change when the
same frozen predictions are scored against alternative CFD solutions instead of the production labels?

**Method** (`alt_ref.py`, analysis `alt_an.py`, data `alt_ref.json`).
- **Cases:** every held-out tank run with an existing alternative solution: 18 runs, 23 run-split rows.
  Nothing was selected. Inventory check (corrected 7 November after review; an earlier version said 20
  runs): 21 tank runs in `~/tb_verify` have an alternative solution; the other 3 (T0036_sst, T0252_sst,
  T0988_sst) are training or validation runs in every split and so have no held-out prediction to score.
- **Models:** FNO and U-Net, both hybrid + canonical frame; 3 seeds each and the 3-seed ensemble, for every
  split. The checkpoints are those of `results_merged/ckpt`.
- **Alternative references:**
  - n4 (nOuterCorrectors 4, 23 rows);
  - co25 (maxCo 0.25, 10 rows);
  - rep (inlet × 1.0001, 23 rows);
  - h25 (2.5 mm mesh, block-averaged 2 × 2 onto the native 5 mm cells; 8 rows from 4 designs).
  T0211, T0243 and T0393 use the reruns with corrected inputs (`v2/`).
- **Identical scoring for every reference:**
  - each prediction is computed once and scored with `metrics.score`;
  - the same 119 snapshots: production times with t > 0, alternatives interpolated linearly in time;
  - the same clipping to [0, 1] and the same outlet cells.
- **Event-window outlet error:** snapshots where the reference's near-outlet θ has completed 10 to 90 % of
  its change over the run. Each reference defines its own window, so a change in this score also includes
  a change in which snapshots are evaluated.

**Norm.** Field errors here are the ML norm: the mean over snapshots of the per-snapshot RMS. The
verification tables use the RMS pooled over all snapshots, which is larger for unsteady runs. Both norms,
recomputed on the exact snapshot set of this study (`agg_119.py`):

| Run | Label change (n4 vs production), pooled | Label change, ML norm (= `alt_ref.json`) |
|---|---|---|
| T0211_sst | 7.41 % | 6.09 % |
| T0052_sst | 6.80 % | 5.56 % |
| T0156_sst | 1.80 % | 1.36 % |

The verification documents quote 7.38 / 6.77 / 1.80 % pooled (6.05 / 5.53 / 1.37 % per snapshot). Those
use 120 snapshots; this study scores 119 (corrected 7 November after review). The alternatives' stored
last time is 222.0 s against 222.04 s in production, so the final snapshot falls outside the alternative's
range and is dropped for every reference alike. Any comparison between a label difference and an ML error
must use the same norm and the same snapshot set.

## Results

### Field error (% of ΔT)

| Reference | Rows | Label change vs production, median (max) | Change of ensemble error, FNO: median [range] | U-Net: median [range] | Mean gap FNO − U-Net, production → alternative | Ensemble ranking flips |
|---|---|---|---|---|---|---|
| h25 | 8 | 0.45 (2.57) | +0.01 [−0.04, +0.45] | −0.03 [−0.18, +0.47] | +0.20 → +0.24 | 1 (T0221_lam, ood_mode) |
| n4 | 23 | 0.02 (6.09) | 0.00 [−0.35, +0.16] | 0.00 [−0.33, +0.09] | +0.43 → +0.43 | 0 |
| co25 | 10 | 0.09 (6.06) | −0.01 [−0.37, +0.09] | −0.01 [−0.42, +0.02] | +0.30 → +0.31 | 0 |
| rep | 23 | 0.02 (3.02) | 0.00 [0.00, +0.54] | 0.00 [0.00, +0.48] | +0.43 → +0.43 | 0 |

- **The one flip:** T0221_lam on ood_mode against the 2.5 mm reference. FNO is better by 0.11 against
  production (1.95 vs 2.06) and U-Net is better by 0.11 against 2.5 mm (2.00 vs 1.89).
- **Seed level:** 3 of 72 seed pairs flip for h25, 3 of 207 for n4, 1 of 90 for co25 and 2 of 207 for rep.

### Flagged runs (ensemble field error, FNO / U-Net)

| Run | Production | n4 | co25 | rep |
|---|---|---|---|---|
| T0211_sst (ood_mode) | 7.98 / 7.04 | 7.73 / 6.77 | 7.60 / 6.62 | 7.98 / 7.04 |
| T0052_sst (ood_geom) | 7.23 / 6.58 | 7.24 / 6.57 | | 7.32 / 6.69 |

**Claim (wording adopted from the review, 7 November):** across T0211 and T0052, changing to the tested
alternative references moved ensemble field error by at most 0.43 percentage points of ΔT (unrounded
maximum 0.4234, T0211 U-Net against co25) and preserved the model ordering.

What this does not show: similar scalar errors against two CFD fields cannot tell how much error either
field shares with the unknown physical solution, nor whether the model residual and the label difference are
unrelated in direction. An earlier version of this report said the ML error on these runs "is not explained
by their label uncertainty"; that went beyond the data and is withdrawn. The dossier's statement that "part
of the ML error there may be label error" is also not supported either way and is replaced by the claim
above.

### Other quantities (ensemble)

| Quantity | Reference effect | Flips |
|---|---|---|
| Energy proxy | ≤ 0.13 points for every reference | none |
| Thermocline midpoint | h25 adds a median 0.5 mm to the model errors | T0551 flips on every reference, including rep. The two models differ there by 0.05 to 0.67 mm (errors 2.0 to 2.9 mm, cells 5 mm), so its sign carries no information |
| **Outlet in the event window** | h25 adds a median 0.9 points (up to +3.3); the 2.5 mm reference itself differs from production by a median 6.0 % of ΔT in this window | 1 (T0551, h25) |

The outlet event window is the quantity most sensitive to the reference. Its metric is the near-outlet-cell
proxy, and the 2.5 mm outlet cells are block-averaged, so this result is specific to that proxy. Each
reference also defines its own breakthrough window, so part of the change comes from scoring different
snapshots, not only from a different label.

## What it shows

1. **Changing the numerical settings (n4, co25) or the inlet (rep) does not change any ensemble ranking**
   on 23 held-out rows. The mean FNO/U-Net gap is unchanged to 0.01 points.
2. **The 2.5 mm mesh changes one ranking** (T0221, a 0.11-point gap) and raises the model errors by up to
   0.47 points. That is the size of the mesh effect on scores in the four mesh designs. T0221 is the
   concrete example for the paper of a model advantage too small to interpret confidently.
3. **On the flagged runs (T0211, T0052), the alternative references moved ensemble field error by at most
   0.43 points and preserved the model ordering.** No family-wide tank rerun is indicated.
4. **The scores most sensitive to the reference are the outlet temperature around breakthrough** and,
   for close cases, the midpoint.

## Limits

- **Selection:** the cases are those with existing alternative solutions. They are dominated by SST and
  low-Ri runs (selected for verification), not a random sample of the test sets, so the mean gap here (U-Net
  better by 0.43) is not a benchmark result.
- **Only 4 designs have a fine mesh** (8 rows), 3 of them laminar.
- **Models covered:** only the two hybrid + canonical ensembles (and their seeds). The plain-model
  ablations and the low-data models were not scored against the alternatives, so no claim is made for them.
- **The ensemble here** is the mean of 3 seeds scored on 119 snapshots. It matches neither the §8.4 seed
  means (every 10th snapshot) nor exactly the §8.1 ensemble (120 snapshots), and is labelled as its own
  table.
