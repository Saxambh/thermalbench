# ThermalStorageBench: figure inventory (8 November 2026)

**Purpose.** List the figures the paper will need, what exists, and the result file behind each, so the
outline can start once the last result (Lou outlet) is in. Nothing here is drawn yet; this is a plan.
Every figure is made by a committed script from committed result files, never by hand.

**Status key:** EXISTS (usable as is), REDO (exists but out of date or not paper style), NEW (not drawn).

## Main paper (proposed, about 10 figures)

| # | Figure | Status | Data source | Script |
|---|---|---|---|---|
| 1 | Benchmark overview: the two families (tank geometry with inlet/outlet; PCM cavity with fins and tilt), parameter ranges, split scheme | NEW (parts exist) | `ThermBench_tank_parameter_plan.md`, `ThermBench_pcm_parameter_plan.md`, `pcm_splits.py`, `splits.py`; meshes in `figures_mesh/tankA_*`, `tankB_*` | `scripts/geometry_figure.py` (tank geometry only) |
| 2 | Example fields: tank charging/discharging snapshots (T) and PCM melting (T, liquid fraction), with the ML prediction and error for one test run each | NEW | h5 runs; checkpoints in `results_merged/ckpt`, `results_pcm_release/ckpt` | `predict.py`, `pcm_predict.py` |
| 3 | Tank validation: Lou et al. 3D jet depth h_j(t) and outlet T*(t), ours vs experiment and their CFD | NEW (outlet waits for the Lou run) | `validation_Lou2023_case_data.md`, `verification_data/lou_outlet_2026-11-07/` | to write |
| 4 | PCM validation: melt fraction vs time against Kamkari (plain wall, 1 and 3 fins, tilt) and Vogel & Thess | NEW | `validation_Kamkari2014_fins.md` (digitised Fig. 6, 11, 12), `validation_Vogel2019_pcm.md` | to write |
| 5 | Verification summary: mesh and settings differences against the pre-registered limits (tank designs T0221, T0243, T0408, T0551, T0211; PCM mesh/time step) | REDO | `figures_verification/` (per-design maps and settings, 7 Nov), `verification_data/*.json`, `verification_data/pcm_timestep_t99.md` | per-design scripts exist; a single summary panel is new |
| 6 | Tank ML results: all models and variants on the four splits | REDO (add multi-node 1D model; final style) | `results_merged/tables.md`, `stats_2026-11-07/`, `multinode_2026-11-08/compare.json` | `figures.py` (`fig_main`, `fig_ablation`) |
| 7 | Charge/discharge symmetry: ood_mode error with and without the canonical frame; confirmation subset | NEW | `stats_2026-11-07/design_ci.md`, `confirmation_discharge_2026-11-07/RESULT.md` | to write |
| 8 | PCM ML results: three architectures, plain/hybrid, six splits, against IDW and the best baseline, seeds shown | REDO (add Transolver, show seeds) | `pcm_final_2026-11-08/result.json`, `extra_baselines_2026-11-08/result_ts.json` | `figures.py` (`fig_main` for pcm) |
| 9 | Material transfer: per-seed field RMSE in both directions against IDW, plus t90 crossing rates | NEW | `pcm_final_2026-11-08/RESULT.md` (seed table), `extra_baselines_2026-11-08/RESULT_ts_tables.md` | to write |
| 10 | Field accuracy vs melt time: per-model field RMSE against t90 error on held-out fins (rank change U-Net / Transolver) | NEW | `extra_baselines_2026-11-08/result_ts.json` | to write |

## Supporting information (proposed)

| # | Figure | Status | Data source |
|---|---|---|---|
| S1 | Meshes (tank A/B full and zooms; Lou 3D) | EXISTS | `figures_mesh/` (11 files, 1 Nov) |
| S2 | Per-design verification maps (field difference, settings) | EXISTS | `figures_verification/` (10 files, 7 Nov) |
| S3 | Per-run error distributions, tank and PCM | EXISTS (PCM REDO for Transolver) | `results_merged/figures/fig_perrun_tank`, `results_pcm_merged/figures/fig_perrun_pcm` |
| S4 | Tank variant ablation (plain, canonical, hybrid, hybrid + canonical) | EXISTS | `results_merged/figures/fig_ablation_tank` |
| S5 | Data efficiency (training-set size, random split) | EXISTS | `thermbench_ml/figures/dataeff_random` (6 Nov) |
| S6 | Seed spread vs error and calibrated bounds (tank) | NEW | `stats_2026-11-07/` |
| S7 | Capacity / speed examples | EXISTS (check need) | `capacity_2026-11-07/` (6 runs), `SPEED.md` |
| S8 | Multi-node 1D model vs surrogates: profile and near-outlet error per split | NEW | `multinode_2026-11-08/compare.json` |
| S9 | Alternative-reference study (T0211, T0052) | NEW (table may suffice) | `altref_2026-11-07/RESULT.md` |
| S10 | PCM WARN sensitivity | table only | `pcm_final_2026-11-08/RESULT_tables.md` |

## Notes for drawing

- One style for all figures (the existing `figures.py` style); colour-blind-safe palette; same model colours
  in every figure (FNO, U-Net, Transolver, IDW, best baseline, multi-node).
- Material-transfer and seed figures show individual seeds, not only means (review, 8 November).
- Captions use the full name ThermalStorageBench.
- Out of date: `results_pcm_merged/figures` (no Transolver); `results_pcm_rehearsal/figures` and
  `results_interim_2026-11-02` are not benchmark numbers and are not used.
