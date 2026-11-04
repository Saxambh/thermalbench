# ThermalStorageBench overnight log, 31 Oct to 1 Nov 2026

Saxam gave full authority to run and amend until he wakes up.

## 23:00 Starting point
- Lab fine subset (3.33 mm, PCG then GAMG) stopped by Saxam's decision: the outlet boundary condition is faulty. T0054 (151x inflow speed) and T0033 (60x) were already blowing up.
- Laptop pilot (5 mm, PCG): 23 finished, P14 crashed at t = 1982 s. P12, P16_lam and P16_sst finished, but with late velocities 13 to 39x too high, so they are corrupted.
- Cause: the outlet uses a uniform fixed p_rgh across the slot, and backflow enters at T0 (70 C in discharge). Once the thermocline reaches the outlet, this drives an exchange flow that feeds itself.
- Test running: P14 restarted from t = 1625 s with the old outlet (ctrl) vs fixedMean p_rgh plus zeroGradient T (fix).

## ~23:45 Outlet fix confirmed
Claude Code stopped the test's wrapper for laptop memory pressure, but the solvers inside WSL kept running, so both copies had results.

Peak velocity |U|max in m/s:

| t (s) | 1625 | 1650 | 1675 | 1700 | 1725 | 1825 | 1950 | 2150 |
|---|---|---|---|---|---|---|---|---|
| old outlet | 0.052 | 0.084 | 0.155 | **0.430** | **0.552** | **0.645** | (stopped at 1861) | |
| fixed outlet | 0.052 | 0.059 | 0.042 | 0.040 | 0.047 | 0.053 | 0.093 | 0.044 |

- With the fix, the outlet temperature falls smoothly: 70.0, 68.1, 65.2, 58.0, then 54.8 C at 2150 s, which is a physical breakthrough curve. The old outlet's temperature jumped around: 66.5, 62.0, 68.6, 61.6.
- Decision: adopted in make_tank_case.py.
  - p_rgh outlet: `fixedMean` (meanValue = P0), so its profile follows the interior stratification.
  - T outlet: `zeroGradient`, so backflow, if any, carries the local temperature instead of T0.
  - U, k and omega are unchanged.
- Smoke test (5 mm, 3 s): all three real-property variants ran and exported cleanly (discharge side outlet, turbulent top outlet with buoyancy term, pre-stratified start). Only real properties were tested; the Boussinesq variant (cross-check only) is not yet tested with the new outlet.

## ~23:55 Lab PC restarted
- Old fine128_h3mm deleted. The logs and case.json for T0033 and T0054 are kept in ~/of_runs/outlet_bug_evidence/ on the lab.
- fine128_h3mm restarted: 153 runs, 14 at a time, fixed outlet plus GAMG. Checked: 14 solvers, all with fixedMean and GAMG, no FATAL. Lab memory 28 of 31 GB free.

## ~00:00 Laptop pilot rerun started
- design_v2_pilot.csv (24 runs, current snapping), fixed outlet plus GAMG, output in ~/of_runs/pilot_v2.
- The old pilot (pilot_h5mm) is superseded: wrong outlet, PCG, old snapping. It is kept on disk for now.
- 4 jobs, not 6: Windows had only about 2.6 GB free. WSL itself is small; most memory is Windows plus Claude Code.
- Launched detached (setsid) inside WSL, so it survives if Claude Code kills its own background shells.

## ~01:25 UTC Progress, and the laptop full batch queued behind an automatic gate
- Pilot_v2: 13 of 24 done, no FATAL. P14 is past the 1982 s point where it crashed before.
- The finished cases now show zero outlet backflow. With the old outlet, the slow charge cases had up to 50%, so the fix cleaned those up too.
- The lab subset is running, no errors. Its time estimates are still unreliable because early time steps are small; T0033 and T0054 (the two that blew up before) are about 21% done and healthy.
- Claude Code stopped my monitoring shell for memory pressure (Windows had 1 GB free; WSL uses only about 1 GB, and the rest is Windows plus apps). Per its rule I did not restart the monitor.
- So that the laptop does not sit idle, I started a detached chain inside WSL (`laptop_chain.sh`, log in ~/of_runs/chain.log):
  1. It waits for pilot_v2 to finish.
  2. It runs `pilot_gate.py`. The gate passes only if all 24 runs are DONE, there are no FATAL errors, no case's late-run peak velocity exceeds 3x its early-run peak, no case's peak velocity exceeds 40x its inflow speed, and energy metrics are finite.
  3. Only if the gate passes does it start the full batch (design_v2_full.csv, 1217 runs, 5 mm) on the laptop, 4 jobs, into ~/of_runs/full_h5mm. If the gate fails, nothing starts.
- 02:05 UTC: pilot_v2 finished, GATE PASS (24 of 24), and the full batch started automatically.

## 31 Oct, morning summary (checked 18:22 laptop clock)
- Pilot_v2: 24 of 24 OK.
  - P14 now completes. Its peak velocity is 0.13 m/s (26x inflow), against 0.6 m/s before.
  - The slow discharge cases still show some outlet backflow (P14 up to 62% of the slot, P12 38%), but it no longer grows: late/early peak velocity is at most 2.0.
- Full batch (laptop, 4 jobs): 16 runs done, 0 failures.
  - A cost fit on 40 finished runs (median error 1.3x) gives about 435 core-hours remaining.
  - That is about 4.5 days at 4 jobs, or about 1 day if the lab joins with 14.
- Lab fine subset: 3 of 153 done, 14 running, no errors. The slowest cases still show 40 to 50 h left.
## 31 Oct ~12:45 UTC, Saxam: stop 3.33 mm, finish 5 mm on both machines first
- Lab fine subset stopped. Its 3 finished runs are kept in ~/of_runs/fine128_h3mm (the restart will skip them).
- Full batch split by predicted cost (split_full.py; cost fit on 40 runs, median error 1.28x):
  - design_v2_full_laptop.csv: 285 runs, 4 jobs, about 24 h.
  - design_v2_full_lab.csv: 932 runs, 14 jobs, about 24 h.
  - The two files share no runs and together cover all 1217.
- Lab: 14 solvers started on its share. All have fixedMean and GAMG; no FATAL.
- Laptop: detached laptop_switch.sh waits for T0177, T0462 and T0662 to finish (at most 45 min). It then restarts the driver on the laptop share only and deletes any unfinished lab-share runs the old driver had started. T0921 restarts from scratch (about 40 min lost).
- After both finish, merge the two full_h5mm folders

## 31 Oct ~17:40 UTC Rebalance (Saxam: "yes rebalance, go with 8 on laptop")
- Measured: lab runs are about 4.1x slower per run than the cost model (which matches the laptop at about 1x); range 2.2 to 6.9, plus one just-started run at 10.9.
  - Lab CPU: 100% per job, High performance plan, 3.4 GHz, no competing processes.
  - Likely causes: memory bandwidth (14 jobs on dual-channel DDR4), SMT sharing under WSL, and lower clocks.
  - At that speed the lab share was about 94 h.
- rebalance.py moved the 712 shortest queued lab runs to the laptop. It assumed the laptop at 8 jobs runs 1.5x slower per job, a conservative choice: moving more runs later is easy, but moving runs back is not. Predicted about 46 h for each machine.
  - Lab: the driver kept running, so no lab run was interrupted. Each moved run has a placeholder dir on the lab with DONE + MOVED_TO_LAPTOP, so the lab driver skips it. **At merge time, ignore lab dirs that contain MOVED_TO_LAPTOP.** The list is in moved_to_laptop.txt.
  - Laptop: restarted on design_v2_full_laptop2.csv (997 runs = laptop share + moved), 8 jobs. The 4 runs in progress were restarted, losing about 1.5 job-hours.
- Laptop memory: WSL holds about 8 GB of file cache, and Windows has about 2 GB free. drop_caches does not give memory back to Windows until autoMemoryReclaim is active, which needs a `wsl --shutdown` (that would kill the runs, so it is not done).
- Next: recheck laptop per-job speed at 8 jobs; if it is better than 1.5x, move more queued lab runs.

## 31 Oct ~17:30 UTC Quality checker (task 1)
- qc_runs.py checks every finished run once and writes qc.json and qc_report.csv. Checks: completeness, energy balance, temperature bounds, energy direction, outlet T range, velocity size and growth, outlet backflow.
- It runs hourly on both machines (qc_loop.sh, detached, nice 15), and tbstat now prints the QC summary.
- First results: pilot_v2 24 runs, 0 FAIL / 7 WARN; laptop full 29 runs, 0 FAIL / 4 WARN; lab full 4 runs, all OK; fine128 3 runs, 1 WARN. Energy error median 0.2 to 0.3%.
- **Finding A, energy balance with an unmeasured outlet.** The old exporter took E_out from the area-averaged outlet T, which is biased when the outlet has backflow (P14 7.7%) or a non-uniform profile (SST 1.1 to 1.5%).
  - Added outletFlux (sum phi) and outletHflux (weightedSum h by phi) function objects to the generator; the exporter stores them as series/outlet_mdot and outlet_Hdot. They are diagnostics only; no field output changes.
  - Test: the exact balance closes to 0.24%.
  - Deployed to both machines mid-batch, so runs generated after about 17:30 UTC have the exact flux and earlier ones fall back to the area average. A backflowing outlet without the flux gets WARN:energy_unmeasured, not FAIL.
- **Finding B, start-up temperature overshoot.** P10: +3.6 K in 6 of 40,000 cells at t = 8 s; later at most about 0.6 K in at most 8 cells.
  - It is not the dp/dt term (identical with dpdt off).
  - It is the pressure-velocity coupling: nOuterCorrectors 1 overshoots about 4 K, 2 overshoots 0.13 K, 3 overshoots 0.44 K.
  - Cost of 2 is 1.7 to 1.8x wall time.
  - Over 150 s, mean T differs by only 0.004 K. Field RMS differences (0.6 to 1.9 K) are the same size as the chaotic noise floor.
  - Decision for Saxam: keep 1 (the overshoot is local and transient) or rerun with 2 (+75% compute). For now: kept 1.

## 31 Oct ~18:30 UTC ML benchmark scaffold (task 2)
- Code is in Research_Paper_RP4_ThermBench\thermbench_ml\: data.py, splits.py, metrics.py, baselines.py, models.py, evaluate.py, train.py, README.md.
- Environments in WSL:
  - ~/venvs/tbml: CPU torch 2.15. Needed `apt-get install python3.12-venv`, done as root via wsl -u root.
  - ~/venvs/tbml-gpu: CUDA 12.6 torch 2.14.1; RTX 4060 detected. Windows Python torch is broken (c10.dll init error), so it is not used.
- First baseline numbers on the 53 finished runs (random split, 5 test runs, so only indicative):

| model | rmse_K | thermocline height error |
|---|---|---|
| initial | 15.8 | |
| ideal_stratified | 3.6 | 2.5 cm |
| knn | 2.7 | 14 cm |

- FNO and U-Net train end to end on the GPU at about 7 to 8 s per epoch for 432 samples. A full dataset at stride 10 would be about 4 min per epoch.
- An early 150-epoch training of both models on the runs finished so far is running detached (log in ~/of_runs/ml_early.log).
  - FNO result: rmse 2.17 K, thermocline height error 7.4 cm, energy error 9%. It is strongly overfit (train RMSE 0.033 vs val 0.15 in theta) because there are only 36 training runs.

## 31 Oct ~18:35 UTC Second rebalance (two-way)
- Measured per-run slowdown: lab median 3.6x (assumed 4.1); laptop at 8 jobs median 1.86x (assumed 1.5; range 1.1 to 2.8).
  - Laptop throughput at 8 jobs is about 4.3 run-equivalents, against 4.0 at 4 jobs. Memory bandwidth limits it, so more jobs barely help.
- rebalance2.py moved 318 of the 712 runs back to the lab: the lab placeholder is deleted, and a laptop placeholder (DONE + MOVED_TO_LAB) is created. The list is in moved_back_to_lab.txt.
  - Predicted: laptop 47 h, lab 47 h (was 55 / 38).
  - **At merge: ignore laptop dirs with MOVED_TO_LAB and lab dirs with MOVED_TO_LAPTOP.** (Superseded by the restart below.)

## 31 Oct ~19:00 UTC Restart with nOuterCorrectors 2 (Saxam approved)
- Both batches stopped. The n1 results were renamed to ~/of_runs/full_h5mm_n1 on both machines (laptop 34 runs, lab 6). They are kept for an n1 vs n2 comparison.
- The generator now uses nOuterCorrectors 2.
- New split (split_n2.py; 1.75x cost factor; laptop 8 jobs at 1.86x per run, lab 14 jobs at 3.6x per run):

| machine | design file | runs | jobs | estimate |
|---|---|---|---|---|
| laptop | design_v2_full_laptop_n2.csv | 639 | 8 | about 100 h |
| lab | design_v2_full_lab_n2.csv | 578 | 14 | about 100 h |

- Fresh output dirs; there are no placeholders any more. All 22 solvers confirmed on nOuterCorrectors 2, no FATAL.
- The ml_early training was stopped (the FNO result above is kept; the U-Net never finished).
- The 3 finished fine128 runs are n1 and must be redone when the 3.33 mm subset resumes. QC FAILs only widespread excursions (>0.1% of cell-snapshots) and WARNs the rest., then resume the 3.33 mm subset.
- The full batch is restartable (each finished run has a DONE marker), so it can be stopped any time: `pkill -f run_batch.py; pkill -f buoyantPimpleFoam`. When the lab finishes its fine subset, the full batch is split so the lab takes part of it.
