# Response to the independent review of 7 November 2026

Point-by-point response to `INDEPENDENT_REVIEW_2026-11-07.md`. Each point is either accepted, accepted
with a correction, or challenged. Where a point could be checked against the code or data, we checked it
on 7 November; the check is given. Nothing below has changed the data, the splits or any pre-registered
outcome.

**Summary.** Of 38 points, 35 are accepted. Of the other three:
- 1 is challenged with evidence (2.7);
- 1 was checked and our claim stands (4.8);
- 1 is partly verified (6.1, prior art).

Checks against the code confirmed four of the accepted points: the 8.1/8.4 labels, the two metric proxies,
and the melt-time problem, which turned out worse than stated. The biggest consequences are:
- the claim narrowing in section D;
- the paired alternate-reference scoring, which needs no new CFD;
- a fix to the PCM melt-time metric before PCM evaluation;
- the reframing of novelty.

---

## 1. Evidence and versions

**1.1 Keep the four versions distinct** (October tests, November verification, interim 246-run ML,
final manifest). **Accepted.** The dossier mixes them in places, for example the canonical-frame evidence in
§7.2 is from the interim set. Every number in the paper will name its version.

**1.2 §8.1 and §8.4 summarise different predictors.** **Accepted, confirmed.**
- §8.1 is the 3-seed ensemble: predictions averaged, clipped to [0, 1] and scored on all 120 snapshots
  (`capacity_2026-11-07/spread.py`).
- §8.4 is the mean of single-seed scores on every 10th snapshot (stored training scores).
- That is why the ensemble mean for random (4.1) is not lower than the seed mean (4.02). The two will be
  labelled separately and reproduced by one script.

**1.3 The stopped 3.33 mm subset is not a multi-fidelity benchmark.** **Accepted.** It was already listed as
not delivered; no multi-fidelity claim will be made.

## 2. Tank numerical reliability

**2.1 The 2.8 % is a measured range on four designs, not a dataset-wide ceiling.** **Accepted.** The dossier
wrote "a mesh uncertainty of up to about 2.8 %" in §5.2 and §14. That generalises from four designs, three of
them laminar, and none of them a flagged SST case. It will read: "0.34 to 2.76 % of ΔT field difference in
the four designs tested".

**2.2 T0243.** **Accepted.** The energy difference (0.96 %) is borderline, so "every integral quantity
passed" must not appear anywhere. The suggestion to separate displacement from broadening by comparing front
position and thickness is good. Both are already in the comparison files (midpoint and thickness
differences), so this is analysis, not new runs.

**2.3 T0551: the perturbation does not explain a fraction of the mesh difference.** **Accepted.** The dossier
said "most of the 2.76 % is the flow's own sensitivity". That is a decomposition the data cannot support. The
statement becomes: "the mesh difference (2.76 %) is of the same order as the response to a 0.01 % inlet
change (1.85 %), so the mesh effect cannot be separated from flow sensitivity in this design."

**2.4 T0211 shows setting dependence, not which effect or which setting is converged.** **Accepted.** n4 and
co25 still differ by 2.49 %, so neither is shown to be converged, and the iteration and time-step effects
are not separated. The dossier's "numerical error of the production settings" becomes "numerical-setting
dependence of the production solution".

**2.5 T0052 has no small-time-step run.** **Accepted.** Its causal evidence is weaker than T0211's, and this
will be stated. A co25 run of T0052 costs a few hours. It is only needed if T0052's reference choice affects
a reported conclusion (see 5.1).

**2.6 The binomial interval.** **Accepted.** The sample was stratified (one hash-chosen run per Ri bin and
mode), so the exact interval for independent identical trials is only illustrative. It will be presented
that way, and "2 of 15" will be called a descriptive count of a deliberately chosen set.

**2.7 "Correct §5.4's 12 of 14 at ≤ 0.05 %: T0156 alone has n4 = 1.80 %".** **Challenged.** The statement
counts 14 neighbours: the 4 of test 1 and the 10 of test 2. The two that are not at ≤ 0.05 % are T0156
(1.80 %) and T0052 (6.77 %). The remaining 12 (T0252 ≤ 0.03, T0256 ≤ 0.02, and the ten at ≤ 0.05) are at
≤ 0.05 %, so "12 of 14" is correct. We agree with the reviewer's underlying point that the ten prospective
cases are the clean basis. The paper will state the ten on their own and give the four as a separate,
nearest-neighbour test.

**2.8 Document wall treatment, inlet turbulence and outlet/backflow thermal conditions.** **Accepted.** These
are in the case generator but not in the dossier or the dataset card. They will be added to the card. The
reviewer is right that neither the reruns nor the perturbation runs validate the production outlet
condition.

**2.9 No family-wide rerun; publish both alternative solutions for the flagged runs.** **Accepted.** This is
option A as applied, plus one addition: release the n4 and co25 solutions of T0211 and the n4 solution of
T0052 next to the production labels, with provenance.

## 3. PCM verification and validation

**3.1 GCI arithmetic.** **Accepted.** The reviewer's independent calculation matches ours (p 0.678,
extrapolation 5,096 s, GCI 15.43 % and 9.22 %). The correction is in the wording:
- "0.5 mm melts about 11 % too fast" relies on the extrapolated tail. Against the actual 0.25 mm result it
  is 4.4 %. Both numbers will be given, each with its basis.
- The GCI applies to one scalar (t99) in one configuration (G131). It is not a dataset-wide uncertainty.

**3.2 G301 two-grid difference.** **Accepted.** The 7 % is a two-grid difference (6.67 % against the observed
fine result), and the GCI stays withheld.

**3.3 Report time-step controls and t99 sampling across levels; distinguish t99, the 0.995 stop and
experimental "full melt".** **Accepted.** The three are used in different places in the dossier: t99 in the
mesh study, 0.995 for the stop and for "full melt" in the validation tables, and the experiment's visual
"full melt". They will be named separately.

**3.4 "Uniformly early across 500 cases" is unsupported.** **Accepted.** The dossier said the bias is
"systematic in sign (all cases melt early)". The evidence is 6 spot-check cases plus 3 three-level sets. It
becomes: "in all 9 cases tested, the finer mesh melts later (1.0 to 8.7 % in the spot check)". The ranking
argument built on it is withdrawn (see 5.1).

**3.5 A 1 mm front shift matters for 1 mm fins; P0021 has a 2.17 s snapshot mismatch.** **Accepted.**
Matched-time interpolation and a common fin mask will be used in any fine-reference scoring.

**3.6 Retained WARN cases: report results with and without them; equal file size is not identity; bind
path and hash.** **Accepted.**
- The PCM freeze now writes an md5 per file.
- We will add the accepted source machine and path from the inventory to each manifest entry, so the hash
  is bound to its provenance.
- PCM scores will be reported with and without the 39 solver-WARN cases.

**3.7 The Lou mean bias hides temporal structure; the PIV spread is not an uncertainty band.** **Accepted.**
The difference runs from −8.5 mm at 150 s to +11.5 mm at 700 s, so the model trails the jet early and leads
it late. The paper will show the time series, not only the bias and RMS. It will also drop "within the
measurement spread" as an uncertainty statement.

**3.8 Lou's outlet-temperature history is the highest-value extra comparison.** **Accepted.** It uses the
existing 3D run and links the experiment to a benchmark quantity. We need to extract the data from Lou
Section 4 first (Saxam's library access).

**3.9 Vogel 0.009 is against another 2D model.** **Accepted.** The dossier says so, but the headline should
lead with the experimental deviation (0.030).

**3.10 Assigning the remaining 3-fin excess to model error is unjustified.** **Accepted.** The dossier wrote
"the remaining +0.08 in the first hour is model error". It becomes: "the remaining difference combines
residual discretisation, properties, boundary conditions, experimental uncertainty and model form; these
runs do not separate them."

**3.11 Disclose which curves informed the mushy constant.** **Accepted.** For lauric acid, 5e6 and the
melting range were chosen after the plain-wall comparison with Kamkari Fig. 6 (2 November). So the plain
wall informed the choice, and the 1-fin, 3-fin and tilted cases tested it afterwards. For octadecane, 1e6 was
taken from Vogel & Thess before any run. This will be stated in the validation section.

## 4. ML

**4.1 PCM melt-time leakage.** **Accepted, and confirmed worse than stated.**
- In `pcm_metrics.py`, t90 is found on the snapshot times of the CFD file, and the run stops at true full
  melt. So the scored window ends at the true melt time.
- Worse, a prediction that has not reached 0.9 by then gets NaN, and `aggregate` uses `nanmean`, so **the
  slowest wrong predictions are silently dropped** from t90_err.
- **Fix before any PCM evaluation:** query each model on a fixed τ grid that extends past the true end
  (the true melt fraction stays at 1 after full melt), detect the model's own crossing, and count a missing
  crossing as a failure with its own reported rate, never as a drop.
- The PCM rehearsal t90 numbers are affected and will not be used.

**4.2 The energy and outlet metrics are proxies.** **Accepted, confirmed** (`metrics.py`, `score`):
- energy_err is the difference of mean θ, which assumes constant ρcp, while the CFD uses real properties;
- T_out_err_K is the mean of the cells next to the outlet port, not the flux-weighted outlet temperature,
  and can differ during backflow.

Actions:
- rename them: "stored-energy proxy (constant ρcp)" and "near-outlet cell temperature";
- compare both with the CFD's own real-property energy and outlet series (stored in every h5) on the hard
  cases;
- report the thermocline definition-mismatch rate next to the midpoint error. It is already computed as
  y_mid_missing, but the dossier did not report it.

**4.3 Generalisation wording.** **Accepted.** ood_geom covers the tails of one geometry family, ood_flow is
SST-only extrapolation (SST is in training), and ood_mode is transfer under an approximate symmetry. The
round-trip test shows reversibility of the code, not physical accuracy of the symmetry.

**4.4 "Transfers to discharge only through the symmetry" is too strong.** **Accepted.** The evidence is that
the eight trained models fail on ood_mode without the canonical frame. It does not show that no other
method could transfer. The wording becomes "without the canonical frame, none of the tested models
transfers".

**4.5 Present FNO and U-Net as co-equal baselines; one native spacing does not show resolution
independence.** **Accepted.** We drop "main model" and the resolution argument from §8.4. Both architectures
get equal treatment in every table.

**4.6 Test-informed development.** **Accepted.**
- The splits are fixed by hash, so the interim (246-run) test design IDs recur in the final test sets.
- The canonical frame and the 2 × 2 ablation were decided after seeing interim ood_mode test results, and
  epochs after a test pass.
- So the tank results are development-informed. They will be labelled that way, and confirmatory claims wait
  for the untouched confirmation set, which was already planned for exactly this reason.
- We will also list which interim test designs recur.

**4.7 Data-efficiency reporting.** **Accepted.** We will report unique training designs as well as runs,
whether subsets are nested, and what the seeds vary. The reviewer's reading (a large advantage at 5 %,
vanishing by 50 %) matches the stored file.

**4.8 Does the spread only separate easy from hard regimes?** **Checked: no.** Spearman ρ between spread and
error within regimes (`capacity_2026-11-07/ml_spread.json`):

| Split | All | Laminar | SST | Ri ≥ 5 | SST, Ri ≥ 5 | Ri < 5 |
|---|---|---|---|---|---|---|
| random | 0.86 | 0.75 | 0.92 | 0.82 | 0.87 | 0.65 (n 11) |
| ood_geom | 0.86 | 0.70 | 0.90 | 0.80 | 0.82 | 0.93 (n 26) |
| ood_mode | 0.82 | 0.74 | 0.85 | 0.75 | 0.74 | 0.82 (n 41) |
| ood_flow | 0.94 | | 0.94 | 0.90 | 0.90 | 0.91 (n 56) |

The spread ranks cases of comparable difficulty too, somewhat less well within laminar runs (0.70 to 0.75).
The claim stands, with these numbers added.

**4.9 Statistics.** **Accepted.** We will use paired bootstrap intervals over physical designs with closure
twins kept together, show seeds separately, and never treat cells or snapshots as replicates. The spread will
be described as an indicator of surrogate error against production CFD.

**4.10 Speed.** **Accepted.** It will be stated as a latency ratio of median wall times (about 6,455 to 1),
with hardware, timing boundaries and I/O named, and training amortised. There will be no energy or
equal-cost claim.

## 5. Can the reference change the ML conclusions?

**5.1 The half-best-error rule does not protect rankings.** **Accepted.** The triangle-inequality argument is
correct: a reference change of size d can move a model's score by up to d and a two-model gap by up to 2d.
The dossier's sentence "a label difference smaller than half the best ML error cannot change a benchmark
ranking" is withdrawn. The limits stay as written, as engineering tolerances, and are described as such.

**5.2 The paired alternate-reference analysis.** **Accepted, and we can do most of it now.** Split
membership, checked against the stored test-run scores:
- **Flagged runs:** T0211 (ood_mode) and T0052 (ood_geom), with alternates n4 and co25 for T0211 and n4 for
  T0052.
- **Mesh designs at 2.5 mm** (block-averaged to the native cells): T0243 (random and ood_flow), T0551
  (random), T0408 (ood_geom and ood_mode), T0221 (ood_mode). They include quiet controls (T0408, T0221)
  and interface-sensitive cases (T0243, T0551).
- **Other alternates:** n4 and rep runs of T0156 and T0256 (ood_mode), and of 8 of the 10 regime designs
  (T0492, T0828, T0636 in ood_flow; T0851 in ood_geom; T0108, T0004, T0227, T0696 in ood_mode; T0696
  also in random).
- **Cost:** predictions on about 20 runs for each model and split. That's minutes on one GPU, with no new
  CFD.
- **Plan:** report every eligible case (no selection), each model's score on both references, the paired
  gap and its sign, event-window outlet error and front position. Flagged runs stay in the main score, with
  flagged-only and excluded-flagged results reported separately.

## 6. Novelty

**6.1 Prior art.** **Partly verified** (pages fetched 7 November):
- **Energies 18(3):511 (2025),** a neural network predicting 2D tank behaviour from CFD images: the page
  refused automated access, so it is **not verified**. Saxam should open it. If it is as described, we
  cannot claim novelty for neural prediction of tank fields, and we agree.
- **Hydrate dataset (Li, Sun, Li, Dec 2025):** 320 COMSOL cases varying branched-fin geometry, scalar
  outputs, CC BY; no test split or benchmark.
- **Finned shell-tube PCM dataset (Alimi et al., Sep 2025):** 7 melting scenarios, 173,077 samples (rows,
  not runs), linked to a Case Studies in Thermal Engineering paper; no splits stated.
- **Mushy-constant dataset (Feb 2026):** 3D Fluent enthalpy-porosity runs varying one numerical parameter
  (the mushy constant, 1e3 to 1e10), simulation only (the "experimental" part is its validation); no fins,
  tilt or splits.

**6.2 Framing.** **Accepted.** The contribution is the combination: two storage families of transient
fields, fixed design-level OOD protocols, engineering-level scores, and released fidelity and closure
evidence. We do not claim the individual elements. PDEBench and The Well will be cited as the general
benchmark precedent. Our earlier Scopus searches missed the Mendeley datasets, because they are data records,
not papers.

**6.3 Venue.** **Noted.** Journal of Energy Storage is first choice for the combined study; Applied Thermal
Engineering becomes stronger with the Lou outlet comparison.

## 7. Required work (sections D and E), and our order

| Order | Work | Needs |
|---|---|---|
| 1 | Narrow the claims in the dossier and dataset card (2.1, 2.3, 2.4, 3.1, 3.4, 3.10, 4.4, 4.5, 5.1) | text only |
| 2 | Fix the PCM melt-time metric (4.1) | code, before PCM evaluation |
| 3 | Finish the PCM freeze with md5 plus source path per case (3.6) | running |
| 4 | Paired alternate-reference scoring of the tank (5.2) | GPU predictions, existing CFD |
| 5 | Proxy metrics against the real-property and outlet series; definition-mismatch rate (4.2) | analysis |
| 6 | Merge all seeds; ensemble and seed-mean labels; paired design-level bootstrap; list of interim-test overlap (1.2, 4.6, 4.9) | analysis |
| 7 | PCM training and evaluation on the frozen manifest, with and without WARN cases | about 37 GPU-hours |
| 8 | Lou outlet-temperature comparison (3.8) | data extraction by Saxam |
| 9 | Release package and a clean reproduction of one headline table | packaging |

Not planned unless a result above calls for it: co25 for T0052, a combined n4 + co25 run of T0211, a 0.25 mm
PCM subset, and any family-wide rerun.

---

## Addendum: reviewer's second reply (7 November)

**Withdrawn by the reviewer:** the "12 of 14" correction (our 2.7). The two sampling groups will be reported
separately when discussing prevalence.

**3.4 revised: unique PCM mesh designs.** The reviewer was right that "all 9 cases" double-counts. Checked
against `verification_data/spotcheck_pcm_stage0.json` and `scripts/pcm_mesh_gci.csv`:
- The six spot-check designs are P0021, P0083, P0131, P0301, P0422 and P0437.
- The three-level sets use the same designs:
  - P0021 directly;
  - G131 is P0131 with W 22.0 mm instead of 21.5 mm;
  - G301 is P0301 with W 26.0 instead of 25.5 mm.
  The widths were rounded so the 1 mm grid fits; all other inputs are identical.
- New wording: "6 unique designs. In the 0.5 vs 0.25 mm comparison, the finer mesh melts later in all 6
  (1.0 to 8.7 %). The three-level sets are width-adjusted variants of two of them (G131, G301) and one of
  them unchanged (P0021)."
- G131 and G301 are therefore not dataset runs and are released as their own fidelity cases.

**4.4 revised.** "None transfers" is replaced by the numbers. On ood_mode, mean field error over seeds:
- FNO: plain 64.8 %, hybrid only 13.0 %, canonical only 12.4 %, both 4.48 %.
- U-Net: plain 67.0 %, hybrid only 13.3 %, canonical only 9.85 %, both 4.37 %.

**4.1 revised: PCM melt-time metric.**
- The evaluation horizon is set from inputs only (a fixed multiple of the a priori t_ref), never from a
  case's true stopping time.
- The share of all eligible cases whose prediction reaches 90 % is reported.
- The t90 error is labelled conditional on crossing.

**Added to §7: untouched-design confirmation**, required before any confirmatory generalisation claim. The
tank results are reported as development-informed until then.

**Milestones the reviewer set for a higher readiness rating:**
1. a corrected PCM evaluation;
2. the paired alternate-reference results;
3. one headline table reproduced from the frozen release.

**Milestone 2 done (7 November, about 19:00 Nepal).** The paired alternate-reference results are in
`thermbench_ml/altref_2026-11-07/RESULT.md`.
- No ensemble ranking flips under n4, co25 or rep (23 held-out rows). One flip under the 2.5 mm reference
  (T0221, a 0.11-point gap).
- Flagged runs (corrected after the third reply): across T0211 and T0052, the tested alternative references
  moved ensemble field error by at most 0.43 points of ΔT and preserved the model ordering. The earlier
  "their ML error is not label error" is withdrawn; scalar errors cannot decide that.
- Norm note: verification tables use pooled RMS, ML tables the mean per-snapshot RMS. On the 119 snapshots
  scored here, T0211 n4 is 7.41 % pooled vs 6.09 % per snapshot (the verification documents' 7.38 / 6.05 %
  use 120 snapshots).

**Milestone 1, PCM metric: fixed and tested** (baselines and a 1-epoch neural smoke test); the PCM evaluation
itself waits for the freeze and training.

## Third reply (7 November): points checked and accepted

- **Run count, accepted.** `alt_ref.json` has 18 distinct runs, not 20. Inventory check: 21 tank runs have an
  alternative solution; the 3 not scored (T0036, T0252, T0988) are training or validation runs in every
  split. So coverage of eligible held-out runs is complete with 18 runs and 23 rows.
- **T0211 norm, accepted and explained.** 6.05 % came from 120 snapshots, 6.09 % from the 119 scored here
  (the alternatives end at 222.0 s, production at 222.04 s, so the last snapshot drops for every reference).
  Both are now labelled in `RESULT.md`, with the script `agg_119.py`.
- **Flagged-run wording, accepted** as proposed, with 0.43 (unrounded 0.4234).
- **Outlet window, accepted.** Each reference defines its own breakthrough window; stated in `RESULT.md`.
- **Scope, accepted.** The result covers the two hybrid + canonical ensembles only; plain ablations and
  low-data models were not scored.
- **T0221 reversal** will go in the paper as the example of a gap too small to interpret.

Next milestones: completed PCM evaluation with the corrected metric; one headline table reproduced from the
frozen release.
