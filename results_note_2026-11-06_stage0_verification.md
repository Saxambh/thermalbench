# Stage 0 verification result: PCM mesh spot check and PCM solver QC (2026-11-06)

Stage 0 of the verification plan agreed on 2026-11-06 (Saxam: "0 first"). Read-only: no simulation was started, stopped or changed, and no dataset file was edited. Analysis finished 21:03 Nepal time.

## 1. Questions

1. Is the PCM dataset mesh (h = 0.5 mm) converged for the quantities the benchmark uses?
2. After the pressure-solver fix, which finished PCM cases still show solver failure, and which flags are real?
3. Does the half-fixed P0124 run (p_rgh on PCG, p_rghFinal still on GAMG) differ from the fully fixed run?

## 2. Data and method

**Mesh spot check.**
- **Cases:** 6 PCM cases chosen by `scripts/spotcheck.py select` (seed 20261104), spread over material, fins and tilt.
- **Refined runs:** h = 0.25 mm, on pc4 with `pcm_batch.sh` and production settings otherwise. Finished 2026-11-06 12:15 Nepal.
- **Dataset partners:** 4 runs on pc4 and 2 on pc6 (P0131, P0301), all with DONE status.
- **Method** (`spotc.py`, adapted from `spotcheck.py compare pcm`):
  - The refined fields are interpolated linearly in time onto the dataset snapshot times, then averaged over 2 × 2 blocks onto the dataset grid. The block average is exact because h halves.
  - Field differences are reported as RMS in K and in % of ΔT (ΔT = superheat + subcooling), plus the maximum absolute difference.
  - Liquid fraction (alpha) is compared as RMS.
  - The melt curve is compared as the maximum absolute difference in liquid fraction, from the dense metric time series.
  - Melt time t99 is the first time the liquid fraction reaches 0.99.
- **Check on the method:** matching snapshots by index instead of by time changed no number by more than 0.01, so the snapshot time offsets (up to 41 s) do not affect the results.

**Solver QC.**
- **Script:** `scripts/pcm_solver_qc.sh`, run on every finished case (DONE, not a moved-away placeholder) on the laptop, lab, pc3, pc4, pc6 and pc7. pc5 is offline, so its 8 cases keep their earlier result.
- **Flags:** FAIL if more than 20 % of p_rgh solves are capped or the mean initial residual is above 0.2; WARN if more than 2 % are capped or the residual is above 0.05.
- **Earlier scan:** kept in `first_scan_1106\`.

## 3. Results

### 3.1 Mesh spot check (0.25 mm refined vs 0.5 mm dataset)

| Case | Material | Fins (n, thickness) | Tilt | t99 dataset (s) | t99 refined (s) | t99 difference | Melt curve max diff | Field RMS (K) | Field RMS (% ΔT) | Max abs (K) | alpha RMS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P0021 | octadecane | 0 | 90° | 1,530 | 1,545 | +1.0 % | 0.014 | 2.46 | 7.6 | 16.3 | 0.15 |
| P0131 | lauric | 0 | 0° | 4,452 | 4,620 | +3.8 % | 0.015 | 1.75 | 4.2 | 25.4 | 0.08 |
| P0083 | lauric | 1, 1.5 mm | 0° | 4,205 | 4,408 | +4.8 % | 0.029 | 2.09 | 6.3 | 23.4 | 0.11 |
| P0422 | octadecane | 4, 1.5 mm | 90° | 2,788 | 2,924 | +4.9 % | 0.036 | 1.59 | 4.9 | 11.6 | 0.17 |
| P0301 | octadecane | 0 | 0° | 3,840 | 4,120 | +7.3 % | 0.031 | 2.95 | 7.1 | 27.7 | 0.14 |
| P0437 | octadecane | 4, 3.5 mm | 0° | 1,768 | 1,921 | +8.7 % | 0.029 | 1.47 | 5.8 | 19.8 | 0.13 |

- **The refined mesh melts later in all 6 cases:** +1.0 to +8.7 %, median +4.9 %. The sign is the same every time, so the 0.5 mm mesh has a systematic bias towards faster melting. This is not random scatter.
- **The melt curves differ by at most 0.036 in liquid fraction.**
- **The instantaneous fields differ by 4 to 8 % of ΔT RMS, with local maxima of 12 to 28 K.** These local maxima sit at the melt front: a front that is slightly displaced gives large local temperature and alpha differences (alpha RMS 0.08 to 0.17).
- **The bias is not specific to thin fins.** The two largest t99 differences are an unfinned case (P0301) and a thick-fin case (P0437, 3.5 mm). The tilted unfinned case (P0021, mostly conduction) has the smallest.

### 3.2 Solver QC of all 481 finished cases

| Machine | Cases | ok | WARN | FAIL |
|---|---|---|---|---|
| pc4 | 266 | 237 | 26 | 3 |
| pc6 | 84 | 79 | 5 | 0 |
| laptop | 52 | 37 | 12 | 3 |
| lab | 34 | 31 | 2 | 1 |
| pc3 | 33 | 25 | 7 | 1 |
| pc7 | 11 | 8 | 2 | 1 |
| pc5 (earlier scan, offline) | 8 | 4 | 3 | 1 |
| **Unique cases** | **481** | | **56** | **10** |

**FAIL cases, by status:**

| Status | Cases | Share of p_rgh solves capped | Mean initial residual |
|---|---|---|---|
| Known, rerun with the full fix in progress (laptop) | P0181 | 59.5 % | 0.21 |
| | P0143 | 50.5 % | 0.10 |
| | P0044 | 42.5 % | 0.26 |
| | P0362 | 30.7 % | 0.16 |
| | P0224 | 26.2 % | 0.40 |
| | P0294 | 25.0 % | 0.31 |
| | P0371 | 21.5 % | 0.28 |
| **New, not yet rerun** | **P0228** (pc3) | 38.0 % | 0.33 |
| | **P0273** (pc4) | 52.5 % | 0.17 |
| False alarm (see below) | P0124 (pc7) | 82.3 % | 0.033 |

**Why P0124 is a false alarm.**
- The QC script counts a solve as capped when it takes 200 or more iterations, which is the GAMG limit of the production setup.
- The P0124 rerun uses PCG + DIC with a 2,000-iteration limit. PCG legitimately needs more than 200 iterations: 77,186 of 93,780 solves did, but **none reached 2,000**.
- Its mean initial residual is 0.033, inside the healthy range.
- The QC script therefore misjudges every rerun made with the fixed `pcm_rerun.sh`. It needs to count against the maxIter of the run's own solver.

**Other findings.**
- **WARN went from 46 to 56 unique cases** because more cases have finished. The 10 new WARN cases are P0032, P0067, P0075, P0133, P0164, P0256, P0259, P0403, P0451 and P0469. The 3 new FAIL cases (P0124, P0228, P0273) are in the table above.
- **Breakdown of the earlier 46 WARN cases:**
  - 27 capped only (residual ≤ 0.05), 11 capped with a high residual, 8 high residual only;
  - 43 of 350 finned cases are flagged (12 %), against 3 of 150 unfinned (2 %);
  - all 7 original FAIL cases have fins 1.0 to 1.5 mm thick.
- **7 cases are finished on two machines with identical QC numbers:** P0110, P0116, P0173, P0259, P0260, P0281 and P0342. They are copies of the same run, so one copy of each is kept at the freeze.

### 3.3 P0124: fully fixed vs half-fixed run

| Run | Final pressure solves at the cap | t99 (s) | t_melt from the export (s) | Energy balance max error |
|---|---|---|---|---|
| Half fix (p_rghFinal on GAMG) | 8.1 % | 10,494 | 10,434 | 0.09 % |
| Full fix (both on PCG + DIC) | 0 % | 10,494 | 10,441 | 0.10 % |

- The two melt curves differ by at most 0.0009 in liquid fraction.
- The full-fix run took 40 min on 4 cores on pc7.
- **For this case, capping 8 % of the final pressure solves did not change any physical output.**

## 4. Interpretation

1. **The PCM dataset is internally consistent but not mesh-converged for melt time.** All 500 cases use the same mesh and settings, so they remain a valid benchmark of the 0.5 mm model. For physical statements, the paper should state a mesh uncertainty in melt time of about 5 % (range 1 to 9 %, finer mesh slower), or narrow it with a third mesh level (0.125 mm or a 0.354 mm intermediate level) on 2 or 3 cases to estimate a grid convergence index.
2. **The fin-thickness risk is about solver failures, not mesh error.** Thin fins (1.0 to 1.5 mm, i.e. 2 to 3 cells at 0.5 mm) collect every FAIL case, while the mesh bias appears in unfinned and thick-fin cases alike.
3. **Capped-only WARN cases are probably harmless, but this is not yet shown.** P0124 is one case with 8 % capping. The 7 FAIL reruns (25 to 60 % capping) will show whether heavy failure changes the melt curve. Until then, no WARN case should be rerun or removed.
4. **Two more cases need the corrected rerun**: P0228 and P0273.

## 5. Limitations

- Six cases only, and two refinement levels: the spot check gives the size and sign of the mesh error, not a converged value.
- The ΔT used for the % figures is superheat + subcooling from `scripts/pcm_full.csv`.
- pc5's 8 cases come from the earlier scan; pc5 is offline.
- The tank half of the spot check is **not** available: its 6 started runs at 2.5 mm all stopped at the same moment, 2026-11-05 15:57 Nepal, at 1 to 80 % of their end times; the other 4 were never started. None finished.

## 6. Decisions requested

1. Rerun P0228 and P0273 with the fixed `pcm_rerun.sh` (pc3 and pc4, about 1 h each).
2. Fix `pcm_solver_qc.sh` to count capped solves against each run's own maxIter.
3. Start stage 1A (the tank pilot of iteration count, time step and a repeat run; 6 designs, 21 runs, about 70 core-hours on pc4).
4. Stage 1B: replace the planned thin-fin mesh runs with a third mesh level on 2 or 3 PCM cases, and keep the validation rerun at the dataset's mushy-zone constant (5e6).

## 7. Files

- `D:\ThermBench_data\qc\spotcheck_pcm_stage0.json`: per-case mesh comparison.
- `D:\ThermBench_data\qc\spotc.py`: the comparison script.
- `D:\ThermBench_data\qc\solver_<machine>.txt`: QC per case (case, capped %, mean residual, mean time step, flag).
- `D:\ThermBench_data\qc\first_scan_1106\`: the earlier scan (385 cases).
- Refined PCM runs: pc4 `~/of_runs/spot_pcm/`.
- P0124 runs: pc7 `~/of_runs/pcm_full/runs/P0124` (full fix) and `~/of_runs/pcm_full/halffix/P0124` (half fix).
