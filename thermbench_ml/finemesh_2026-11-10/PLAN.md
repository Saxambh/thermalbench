# PCM fine-mesh label check and extra material-split seeds (plan, 10 November 2026)

Committed before any run. Saxam, 10 November: "we have all the pcs till this week, how do we utilize it?"
then "go ahead, write the plan and launch". Rules below are applied as written; any change after launch is
logged as a dated amendment at the end of this file.

## Part A. Fine-mesh label check (CPU: lab, pc4, pc3, pc6, pc7)

### Question

The PCM labels are on a 0.5 mm mesh. Six spot-check cases (4 November) showed that a 0.25 mm mesh melts
1.0 to 8.7 % later and that the fields differ by 4.2 to 7.6 % of ΔT, more than the best within-material
model errors. The paper therefore says that model differences smaller than the label uncertainty should
not be over-interpreted. This check asks, on 60 cases instead of 6:
1. How large is the label shift between 0.5 and 0.25 mm, per test set?
2. Scored against 0.25 mm labels, do the model rankings and the paper's headline statements still hold?

### Selection (scripts/finemesh_select.py, run 10 November, output selection.json and scripts/fine_pcm.csv)

- **Eligible:** `solver_qc == "ok"` in `pcm_inventory_2026-11-07.csv` (one solver set-up for fine and
  dataset runs), and predicted fine cost ≤ 36 core-hours.
- **Predicted fine cost:** the campaign's design estimate (`core_h_est`, pcm_design.py) × 4 (cells) × the
  time-step ratio (Courant limit, capped at maxdt). On the six spot cases this predicted the measured fine
  wall time within a factor 0.86 to 2.35 (median 1.3). The earlier rule "measured 0.5 mm wall × 8" was
  rejected: on the same cases the true ratio was 10 to 59.
- **Result:** 216 of the 427 ok cases eligible (51 %); 60 chosen; predicted 1,266 core-hours in total,
  35.2 at most.
- **Strata** (each case in the first that applies, by test membership in the frozen splits): random 10,
  drive 10, fins 10, tilt45 6, tilt90 6, other 18; each half lauric acid and half n-octadecane, so each
  material-transfer test set receives 30 cases.
- **Order** within stratum and material: sha256(case_id + "finemesh-2026-11-10"); the first eligible cases
  are taken.
- Two chosen cases (P0083, P0301) were also in the 4 November spot check. They are rerun anyway, which
  doubles as a repeatability check of the fine runs.

**Known bias, reported with the result:** the cost cap keeps the cheaper half of the ok cases. The
report compares the chosen 60 with all 500 on material, fins, tilt, superheat, drive and melt time, and
states which parts of the design space are not covered.

### Runs

- Generator: the dataset case's own arguments with `--h 0.0005` replaced by `--h 0.00025`
  (`scripts/fine_pcm.csv`), run by `scripts/pcm_batch.sh` with the repository's current scripts. The md5
  of pcm_batch.sh, make_pcm_case.py and export_pcm_case.py on every PC is checked against the commit
  before launch.
- All 60 start at once (serial solvers, one core each), split over the PCs by predicted cost, with
  `PCM_STAGGER=20`: lab 16, pc4 16, pc6 11, pc7 11, pc3 6 (7 GB RAM), lists `fine_pcm_<host>.csv`.
- Output: `~/of_runs/finemesh_2026-11-10/` on each PC; exported `thermbench.h5` per case as for the
  dataset.

### Stop rule

- A case still running **96 h** after the batch start is stopped and reported as incomplete; it is not
  replaced and its partial result is not used.
- A case that fails (GEN_FAIL, SOLVER_FAIL, EXPORT_FAIL, or a solver-QC WARN by the dataset rule) is
  reported as failed, with the reason, and is not rerun with other settings.
- The analysis uses the cases that finish under these rules. If fewer than 45 of 60 finish, the result
  is reported as a partial check and no ranking statement is made from it.

### Analysis (written to compare_finemesh.py before the first fine case finishes)

Label shift (question 1), per case and per stratum:
- the fine fields are 2 × 2 block-averaged onto the 0.5 mm grid at the dataset snapshot times, exactly
  as `spotcheck.py compare pcm`;
- field RMSE between the two label sets in K and in % of ΔT (PCM mask only);
- liquid-fraction RMSE; t99 shift in %;
- the shift of each engineering metric used in the paper's PCM table.

Rescoring (question 2):
- every PCM model in the paper: the non-neural baselines and FNO, U-Net, Transolver (plain and hybrid),
  all seeds, using the released checkpoints (`repro_pcm_2026-11-08`, 108 of 108 exact);
- each case is scored only by the models whose split has it in the test set;
- each model is scored on the subset twice, against the 0.5 mm labels and against the block-averaged
  0.25 mm labels, with the paper's PCM metric code (same inputs, same snapshots);
- reported per split: score on 0.5 mm labels, score on 0.25 mm labels, their difference, and the
  rank order of the models under both;
- uncertainty: paired bootstrap over cases (10,000 resamples, seed 20261110) of each model-pair
  difference, under both label sets.

**Decision rules** (fixed now):
- A ranking statement in the paper "holds" if the sign of the model-pair difference is the same under both
  label sets and the 95 % bootstrap interval of the 0.25 mm difference excludes zero.
- It is "not resolved by the labels" if the 0.25 mm interval includes zero.
- It "flips" if the sign changes and the 0.25 mm interval excludes zero.
- Each headline statement of the PCM section is listed with one of these three verdicts. Statements
  rated "not resolved" or "flips" are reworded in the paper. Nothing is reworded for any other reason
  from this check.
- The limitation paragraph and Appendix (mesh) are updated with the 60-case numbers, replacing the
  six-case numbers as the main evidence (the six cases stay as history).

## Part B. Extra seeds on the material-transfer splits (GPU: lab, pc4, pc3, pc6, pc7)

### Question

The material-transfer errors are the paper's largest and most variable PCM results, with 3 seeds. Two
more seeds (s3, s4) give 5 seeds there, so the mean and spread are less sensitive to one seed.

### Jobs

- Models: fno, fno_hybrid, unet, unet_hybrid, transolver, transolver_hybrid.
- Splits: ood_material, ood_material_r. Seeds 3 and 4. 6 × 2 × 2 = 24 jobs.
- Settings identical to the paper's jobs: `--manifest manifest_pcm.json --amp --batch 16 --threads 2`; FNO
  and Transolver 60 epochs, U-Net 100; Transolver `--lr 3e-4` (the pilot's choice).
- Script: `extra_seeds_2026-11-10/run_seeds.sh <worker>`; outputs `results_pcm_s34/`, checkpoints
  `ckpt_pcm_<name>_s3|s4_<split>.pt`.
- Each GPU runs one job at a time next to the CFD (2 CPU threads each).

### Reporting rules

- The material-split rows of the PCM table are reported with 5 seeds (mean ± standard deviation), the
  other splits stay at 3 seeds, and the table says so.
- Seeds 0 to 2 are not retrained or replaced. All 5 seeds are reported; none is dropped.
- If the 5-seed mean changes the order of two models compared with the 3-seed mean, the text says so.
- The new checkpoints join the release with provenance (host, md5), and `repro_pcm.py` is extended to
  rescore them.

## Order of work

1. Commit this plan, the selection script, selection.json and fine_pcm.csv; push.
2. Check script md5s on the PCs; copy the per-host CSVs and the seeds script.
3. Launch Part A and Part B.
4. Write compare_finemesh.py and commit it before the first fine case finishes.
5. When done: RESULT.md, commit, then update the paper (Part A: limitation, appendix, any reworded
   statements; Part B: material rows).

## Amendments

**1 (10 November, after launch, before any fine case finished).** `compare_finemesh.py` written and tested on
the 4 November spot runs P0083 and P0301 (both also in this selection). Two details the plan did not foresee:
- the dataset run's last snapshot is its auto-stop time, off the write grid, so the fine fields there are
  interpolated linearly in time between the two bracketing fine snapshots; all other snapshot times must
  match exactly;
- fins snap to the 0.25 mm mesh slightly differently (P0083: 9 of 8,200 cells differ after block averaging),
  so the block-averaged fine mask may differ from the dataset mask in at most 1 % of the cells; scoring uses
  the dataset mask, and the count is reported per case.

Test result (two cases, not the check itself): field difference 5.5 and 6.7 % of ΔT, t90 later by 4.3 and
6.5 % on the fine mesh, in line with the six-case spot check. The PCs run the 4 November export_pcm_case.py
(md5 83074cda), which differs from the repository copy only in the project name in its docstring.

**2 (10 November, before any seed 3 or 4 result exists).** Following an external referee read of draft v1:
- *Material-transfer wording rule, fixed now:* with 5 seeds, "interpolation beats every network" may be written
  for a held-out material only if IDW is better than every network's 5-seed mean AND better than each of that
  network's 5 seeds, and the paired bootstrap over cases excludes zero. Otherwise the text says "no network
  beats interpolation" for that material. The same rule is applied to both materials.
- *Reading of Part A:* a "holds" verdict shows that a ranking is stable when the labels change from 0.5 to
  0.25 mm. It does not show that the labels are accurate, because every network was trained on 0.5 mm
  labels and so carries the same bias. The result will be worded that way.
- *Checkpoint count:* the 24 new checkpoints raise the released total from 204 to 228. The abstract,
  introduction, cover letter, data statement, CITATION.cff and the rescoring audit are updated together.
