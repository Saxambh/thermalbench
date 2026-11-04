# ThermalStorageBench ML benchmark (tank family, 2D)

## Task: forward surrogate
Given a tank's inputs and a time t*, predict the temperature field at t*.

- **Inputs.** All of these are known before the run:
  - geometry: W, slot size, port offset, port type A/B;
  - operation: charge/discharge, inflow speed, ΔT, cold temperature, pre-stratified start and its interface height;
  - turbulence model flag, Re_in, Ri_H;
  - the initial field.
- **Target.** theta = (T − Tc)/(Th − Tc) on the native 5 mm grid (200 × W/0.005 cells). Snapshots are scored at every 10th of the 120 written times.

## Splits (`splits.py`)
Assignment is by design point, so laminar/SST twins stay together, and it is fixed by parameters or a hash.

| split | test set | tests |
|---|---|---|
| random | 10 % of design points by hash | interpolation |
| ood_flow | Re_in > 9007 (design 90th percentile) | faster inflow than seen |
| ood_geom | W < 0.33 m or W > 0.93 m | unseen tank shapes |
| ood_mode | all discharge cases (train on charging) | unseen operation |

## Metrics (`metrics.py`)
- `rmse_K`, `rmse_theta`: the full field.
- `profile_rmse`: the row-averaged profile, which is what a 1D tank model is judged on.
- `y_mid_err_m`: thermocline height.
- `energy_err`: stored energy error as a fraction of the tank's full capacity. It is not divided by the energy currently stored, which goes to about zero at the end of a discharge.
- `T_out_err_K`: outlet temperature error in K, what a system simulation takes from the tank.

Noise floor: two CFD solutions that differ only in solver settings drift apart by about 0.65 K RMS in 60 s and 1 to 2 K over minutes, because the buoyant jet is chaotic. Field errors below this are not meaningful.

## Baselines
| model | file | idea |
|---|---|---|
| initial | baselines.py | no change (lower bar) |
| ideal_stratified | baselines.py | plug flow with a sharp interface from the energy balance (MIX = 0) |
| knn | baselines.py | mean of the 5 nearest training runs in parameter space |
| fno | models.py | Fourier neural operator, 4 layers, width 32, 16 modes |
| unet | models.py | 4-level U-Net, base width 32 |

## Use
```bash
# environments (WSL): ~/venvs/tbml (CPU torch), ~/venvs/tbml-gpu (CUDA 12.6 torch, RTX 4060)
python evaluate.py --roots ~/of_runs/full_h5mm --split random           # non-neural baselines
python train.py --model fno --roots ~/of_runs/full_h5mm --split random --epochs 100
```
Results go to `results_<split>.json`.

Runs come from `data.index`, which skips runs that failed QC and the lab's MOVED_TO_LAPTOP placeholders. Both machines' `full_h5mm` folders must be merged before training on the full set.

## Final training plan (decided 2026-11-01)

1. **Freeze the run list** once the batch and QC are complete: `python freeze_manifest.py`. Every model then uses exactly the runs in `manifest_full_h5mm.json`.
2. **Epoch check:** `bash run_final.sh check`. This trains FNO hybrid on the random split at 60 and at 150 epochs. If the 150-epoch result is better by more than the seed spread, raise the epochs.
3. **Full set:** `bash run_final.sh <worker> <nworkers>` on each GPU machine.
   - Models: FNO and FNO hybrid at 60 epochs; U-Net and U-Net hybrid at 100 epochs (U-Net was still improving between 60 and 100 epochs in the test pass, by up to 17 %).
   - 4 splits × 3 seeds.
   - Settings: bf16, batch 16, data held on the GPU (`--gpu-data`).
   - Expected cost: about 111 GPU-hours, about 2.3 days on the laptop and pc3 GPUs.

**Measured speed** (RTX 4060 laptop GPU). The old loader ran at 27 ms per sample; `--gpu-data --amp --batch 16` runs at 8.7 ms per sample. The raw model benchmark (`bench_train.py`) gives 7.3 ms per sample for FNO and 7.9 ms for U-Net.

## Not done yet
- An autoregressive (rollout) task.
- KPI-curve regression (E, MIX, T_out vs t*).
- The 3.33 mm multi-fidelity task.
- A measured noise floor per case.

## PCM family (built 2026-11-02)

Separate modules that reuse the tank models (`models.py`, now with `cout`) and the hash helper:

- **`pcm_data.py`:** loads runs from `export_pcm_case.py` (`PCMRun`: T, alpha, mask with fins = 0, times).
  - Inputs: 13 scalar parameters (material, superheat, subcooling, W, fins, tilt, Ra, Ste, Pr, t_ref).
  - Time input is tau = t / t_ref, where **t_ref is an a priori melting-time scale** from the inputs only (energy over laminar Nu ~ Ra^0.25 heat rate, calibrated on Vogel and Kamkari, with fin and tilt factors). The true melting time is an output, so it is never an input.
  - Grid: 0.5 mm, H 100 mm, padded to W_MAX = 60 mm.
- **`pcm_splits.py`:** random, ood_fins (N = 4 or 5), ood_drive (superheat > 27.81 K, the design q90, both materials), ood_material and ood_material_r, ood_tilt.
- **`pcm_metrics.py`:** rmse_K, alpha_rmse, liquid_iou (melted region), melt_frac_err, energy_err (fraction of a full charge), t90_err (time to 90 % melted, relative).
- **`pcm_baselines.py`:**
  - initial (nothing melts);
  - stefan (conduction only, exact two-phase Neumann solution);
  - front (conduction-then-convection front: Stefan early, then f = min(1, s tau) with s fitted; the hybrid base);
  - knn.
- **`pcm_evaluate.py`, `pcm_train.py`** (`--hybrid` learns the correction to front). Results go to `results_pcm/<split>.json`.

**Tested 2026-11-02** on a 32-case development set: the real design at 1 mm, cut at 20 min (laptop `~/of_runs/pcm_mini`; results in `results_pcm_dev/`, not benchmark numbers).
- All six splits and all baselines ran.
- fno and fno_hybrid trained for 20 epochs on 24 runs. On the random test (3 runs), fno_hybrid gave 2.95 K, IoU 0.88, melt fraction error 0.019, against knn 4.72 K and front 6.21 K.
