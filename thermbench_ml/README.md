# ThermalStorageBench: benchmark code

Code for loading the data, the fixed splits, the metrics, the baselines, training and evaluation of
ThermalStorageBench. It has two families:
- the **stratified water tank** (sensible storage): 1,212 runs;
- the **PCM melting cell** (latent storage): 500 runs.

The paper describes the dataset, its verification and validation, and the results. Development history
is in `DEVELOPMENT_NOTES.md`.

## Quick start: score your model

```bash
python example_evaluate.py --family tank --split random --model idw    # 9.32 % of dT (paper, Table 2)
python example_evaluate.py --family pcm  --split random --model idw    # 2.55 K (paper, Table 3)
python example_evaluate.py --family tank --split ood_mode --model mine # your model: edit MyTankModel
```

A model needs `fit(train_runs)` and `predict(run, idx)`; see the docstring of `example_evaluate.py`.
Scoring uses the same functions that produced every number in the paper.

## Data

- **Frozen manifests:** `manifest_full_h5mm.json` (tank, md5 0e8b6d8d...) and `manifest_pcm.json` (PCM,
  md5 19397b78...).
  - They list every run with the md5 of its h5 file.
  - `check_data.py <manifest>` verifies a local copy.
- **Per run:** one `thermbench.h5` with the fields and per-snapshot quantities, plus `case.json` with all
  inputs.
- **Loading:** `data.index(roots, manifest=...)` (tank) and `pcm_data.index(...)` (PCM) return run objects:
  - `run.params()`: the design inputs;
  - `run.times()`: the times;
  - `run.field("T", idx, theta=True)`: the normalised temperature;
  - PCM also `run.field("alpha", idx)` and `run.mask()`.
- **Reading one run with h5py only:** `../release/load_example.py`.

## Tasks

| Family | Input | Predict | Scored snapshots |
|---|---|---|---|
| Tank | design inputs, initial field, t* = tQ/V | θ = (T − T_c)/(T_h − T_c) on the native 5 mm grid | every 10th of 120 |
| PCM | design inputs, τ = t/t_ref (t_ref from the inputs only) | temperature (as θ) and liquid fraction on the 0.5 mm grid | every 5th, plus melt time on a fixed grid up to τ = 3 |

## Splits (`splits.py`, `pcm_splits.py`)

Assigned by design point (laminar and SST twins stay together), fixed by parameters or a hash of the
case id. Do not change them; validation data come from the training side of each split.

| Family | Split | Test set |
|---|---|---|
| Tank | `random` | 10 % of design points |
| | `ood_geom` | width outside 0.33 to 0.93 m |
| | `ood_mode` | all discharging runs (train on charging) |
| | `ood_flow` | inlet Re above 9,007 (all SST) |
| PCM | `random` | 10 % of cases |
| | `ood_fins` | 4 and 5 fins (train on 0 to 3) |
| | `ood_drive` | superheat above 27.81 K |
| | `ood_tilt` | 45° and heated from below |
| | `ood_material` | lauric acid (train on n-octadecane) |
| | `ood_material_r` | n-octadecane (train on lauric acid) |

## Metrics (`metrics.py`, `pcm_metrics.py`)

- **Tank:**
  - `rmse_theta` (field, fraction of ΔT) and `rmse_K`;
  - `profile_rmse` (horizontally averaged);
  - `y_mid_err_m` (thermocline midpoint; `y_mid_missing` counts snapshots without one);
  - `energy_err` (fraction of a full charge, constant-ρc_p proxy);
  - `T_out_err_K` (area-averaged outlet temperature).
- **PCM:**
  - `rmse_K`, `alpha_rmse`, `liquid_iou`, `melt_frac_err`, `energy_err`;
  - `t90_reached` (share of runs whose prediction reaches 90 % melting within τ = 3);
  - `t90_err` (relative, over those runs only).

## Baselines and models

- **Baselines:** `baselines.py` (tank: initial, ideal stratification, kNN, NN, IDW, RBF), `multinode.py`
  (calibrated 1D model), `pcm_baselines.py` (initial, Stefan, front, kNN, NN, IDW, RBF).
- **Neural models:** `models.py` (FNO, U-Net, Transolver).
- **Training:** `train.py` / `pcm_train.py` with `--hybrid` (learn the correction to the physics base) and,
  for the tank, `--canon` (charge/discharge frame).
- **Settings used in the paper:** batch 16, bf16, 60 epochs (FNO, Transolver) or 100 (U-Net); 3 seeds.

## Released checkpoints

- 96 tank and 108 PCM checkpoints, each taken from the machine that trained it and rescored from the frozen
  data (`repro_all_2026-11-08/`, `repro_pcm_2026-11-08/`).
- Rescoring on the same GPU type reproduces every stored score exactly; across GPU types, expect agreement
  to about 1e-4 K.
- `predict.py` and `pcm_predict.py` run a checkpoint on a dataset run (`--from-run`) or on a new design.

## Reporting results

So that results stay comparable with the paper:
- report every metric, per training seed as well as the mean;
- for PCM, give the share of runs reaching t90 next to the t90 error;
- report the two flagged tank runs (`label_flags_tank.json`: T0211_sst, T0052_sst) separately or note them.

## Environment

Python 3.12.3, PyTorch 2.14.1 (CUDA 12.6), numpy 1.26.4, h5py 3.10.0; the CFD used OpenFOAM v2606. Full
package list: `../release/requirements_gpu_freeze.txt`.
