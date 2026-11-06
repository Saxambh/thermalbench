# PCM: solver-fix reruns vs originals, and the series repair of resumed cases (2026-11-07, about 00:40 Nepal)

## 1. Corrected reruns (PCG + DIC for both pressure solves) vs the original runs

Script `scripts/pcm_rerun_compare.py`, data `verification_data/pcm_rerun_vs_orig.json`. Same grid; the rerun
is interpolated in time onto the original snapshots.

| Case | Configuration | t99 change | Melt curve, max abs diff | Field RMSE (% ΔT, K) | Max abs (K) | Energy balance error, original → rerun |
|---|---|---|---|---|---|---|
| P0181 | octadecane, 5 fins of 1.0 mm, tilt 90 | +0.9 % | 0.010 | 3.3 % (1.47 K) | 24.7 | 0.28 → 0.23 % |
| P0371 | lauric, 5 fins of 1.5 mm, tilt 90 | −0.9 % | 0.032 | 8.0 % (2.24 K) | 20.2 | 0.18 → 0.18 % |
| P0228 | lauric, 2 fins of 1.5 mm | −0.9 % | 0.006 | 1.9 % (0.62 K) | 15.7 | 60 % (series bug, below) → 0.10 % |
| P0273 | octadecane, 5 fins of 1.0 mm, tilt 45 | −2.1 % | 0.028 | 6.2 % (2.08 K) | 30.7 | 1.13 → 0.14 % |

- None of the reruns' pressure solves reached the 2,000-iteration limit. Mean initial residual 0.007 to 0.026.
- Melt time and melt curve barely change. Local fields (the melt-front position) change by 2 to 8 % of ΔT, as
  much as the 0.5 vs 0.25 mm mesh difference.
- Decision: the failed originals are replaced by their reruns at the PCM freeze.

## 2. Series bug in resumed cases, and its repair

**Found** from P0228's 60 % energy-balance error.
- 41 cases resumed after an interruption (27 on the laptop, 14 on pc3) kept their postProcessing series
  in two or more start-time folders.
- The 0/ file was partly overwritten with NUL bytes by the interrupted write.
- `export_pcm_case.py` reads the first .dat file only, so t_melt was NaN, and Q, Nu and the energy balance
  covered only the time before the first restart (errors of 1.3 to 98.7 %).
- The fields, and the snapshot liquid fraction and energy, were complete and correct: every melt curve
  rises to 0.995 with no drop larger than 0.003.

**Repair** (`scripts/pcm_repair_series.py`, applied 2026-11-07 about 00:30 Nepal, approved by Saxam):
- Merge the series across folders (NUL lines dropped, a later folder wins from its start time on).
- Recompute q_wall, E_in, t_melt, Nu and the energy balance exactly as the exporter does.
- Rewrite only tstar, metrics/Q_W_per_m, metrics/Nu, metrics/energy_balance_err and series/* in
  thermbench.h5, plus metrics.json. A line is added to export.log and an attribute to the h5.
- Backups: `thermbench.h5.series_bug` and `metrics.json.series_bug`. The old qc.json was kept as
  `qc.json.pre_repair`.

**Result.** All 41 cases now have energy-balance errors of 0.01 to 0.5 % (P0143: 1.3 %; it is a
failed-solver original being rerun anyway) and a melt time.

## 3. QC rerun on all machines

| Machine | Cases | OK | WARN | FAIL |
|---|---|---|---|---|
| laptop | 52 | 47 | 4 | 1 (P0143: rerun running) |
| pc3 | 34 | 31 | 2 | 1 (P0495) |
| lab | 34 | 33 | 1 | 0 |
| pc4 | 267 | 261 | 5 | 1 (P0273: replaced by rerun) |
| pc6 | 116 | 113 | 3 | 0 |
| pc7 | 11 | 10 | 1 | 0 |

The pc3 cases had never been through pcm_qc.py before. Counts include cases present on two machines.

**P0495 is physically broken.**
- It was resumed at t = 570 s on pc3 (2026-11-06). The continuation's series merge crashed on a NUL line.
- From about 2,000 s on, temperatures exceed the wall temperature (up to 72.6 °C against Tw 66.75 °C); 52 %
  of cells are out of bounds at the end.
- It needs a fresh rerun.
