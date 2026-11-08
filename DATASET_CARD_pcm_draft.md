# Dataset card (draft): HeatStoreBench, PCM melting family

Draft of 8 November 2026. Name: HeatStoreBench (decided 8 November 2026). The license is decided at release.

## What it is

500 two-dimensional OpenFOAM simulations of a phase-change material (PCM) melted from a heated wall, with
0 to 5 conducting fins: the basic cell of plate and finned latent-heat stores.
- **Use:** benchmark surrogate models that predict the temperature and liquid-fraction fields, the melt
  front and the melt time from the design inputs.
- **Frozen manifest:** `thermbench_ml/manifest_pcm.json`, md5 `19397b78801e26909fe8d0e369cd9bca`. It lists
  500 runs, each with h5 md5, source machine and path, and solver evidence.

## Design (Sobol, `scripts/pcm_full.csv`), as frozen

| Input | Values in the frozen set |
|---|---|
| Material | n-octadecane 250 (melting point 28 °C) / lauric acid 250 (melting range 43.5 to 48.2 °C) |
| Wall superheat | 8.0 to 30 K (median 19) above the melting point (range midpoint for lauric acid) |
| Initial subcooling | 0.5 to 22.3 K (median 11.4) |
| Width W (height 100 mm) | 20 to 60 mm (median 40) |
| Fins on the heated wall | 0: 150, 1: 69, 2: 71, 3: 71, 4: 70, 5: 69; length 0.2 to 0.8 W, thickness 1 to 4 mm |
| Orientation | side-heated 350, tilted 45° 75, heated from below (90°) 75 |
| Dimensionless | Ra_H 1.5e8 to 9.0e8 (median 4.0e8), laminar; Ste 0.07 to 0.37 (median 0.19) |

**Coverage limit:** gentle heating below 8 K superheat and widths above 60 mm were dropped on 2 November,
for cost (from about 12,400 to about 3,100 core-hours).

## Numerical model

- **Solver:** buoyantPimpleFoam (OpenFOAM v2606) with OpenFOAM's enthalpy-porosity melting source
  (Voller & Prakash).
- **Properties:** constant (the Vogel & Thess "B-2D" set); Boussinesq buoyancy about the melting point.
- **Mushy-zone constant:** 1e6 for octadecane, taken from Vogel & Thess before any run. 5e6 with the
  melting range for lauric acid, chosen after the plain-wall comparison with Kamkari & Shokouhmand Fig. 6,
  so that experiment informed it.
- **Fins:** conducting aluminium (k = 130 W/m K).
- **Mesh and time step:**
  - uniform **0.5 mm** mesh (200 rows; the ML loader pads to W = 60 mm);
  - adjustable time step, maxCo 1.0, maxDeltaT 0.5 s (Courant-limited in practice).
- **Pressure:** p_rghFinal relTol 0, maxIter 200 (the pressure fix of 4 November). 34 cases whose pressure
  solve failed were rerun with PCG + DIC.
- **End:** each run stops automatically at liquid fraction 0.995.

## Per run

One `thermbench.h5` (median 19.9 MB; 10.3 GB in total) with:
- 88 to 204 snapshots (median 122) of T and the liquid fraction alpha on the native grid;
- the PCM/fin mask;
- per snapshot: stored energy, Nusselt number, heat input, mean T, liquid fraction and energy-balance
  error;
- dense series of the liquid fraction, mean T, Nusselt number and heat input, every 10 solver steps;
- `case.json` with all inputs, also in the h5 as `case_json`.

Simulated time is 0.33 to 11 h (median 1.75 h).

## Quality control and acceptance

- **Inventory:** 703 case folders on seven machines reduce to exactly one accepted output per case
  (`pcm_inventory_2026-11-07.csv`). The acceptance rules are in the validation dossier, §12.
- **QC verdicts:** field QC (`pcm_qc.py`) 498 OK, 2 WARN; solver QC (`pcm_solver_qc.sh`) failures were never
  accepted.
- **Solver WARN cases:**
  - 39 kept under a pre-registered sensitivity rule;
  - the 17 cases of the one kind that changed materially were rerun.
- **Repairs:** 41 resumed cases with split series were repaired (fields were complete), and one corrupted
  case (P0495) was rerun from t = 0.
- **Freeze check (7 November):** every file was checked against the inventory before the manifest was
  written: presence, size, QC status and solver setting.
  - 494 runs show relTol 0 in their own `system/fvSolution`.
  - The 6 pc5-archive copies have no `system/` folder. Their origin batch and case date establish the
    setting.

## Verification

- **Mesh, three levels, G131** (lauric acid, unfinned; a width-rounded variant of P0131):
  - t99 from the dense series is 4198.6 / 4515.0 / 4704.3 s at 1.0 / 0.5 / 0.25 mm;
  - observed order 0.74; GCI 13.06 % on the 0.5 mm production mesh and 7.5 % at 0.25 mm; the 0.5 mm run is
    9.5 % early against the extrapolation and 4.0 % early against the 0.25 mm run;
  - this is one scalar in one configuration, from a combined space-and-time refinement (the time step
    halves with the mesh).
- **Mesh, G301** (octadecane): order about 0.15, not shown to be in the asymptotic range; no GCI. The 0.5 mm
  run melts 6.76 % earlier than the 0.25 mm run.
- **Spot check, 6 dataset designs, 0.5 vs 0.25 mm:**
  - the finer mesh melts later in all 6, by 1.0 to 8.7 % (median 4.9 %);
  - field differences 4.2 to 7.6 % of ΔT, concentrated at the melt front, with front shifts of 0.3 to
    0.8 mm.
- **Labels are not mesh-converged.** The 0.5 mm melt times are early by a few percent, and the size varies
  by case. Fine-mesh runs are released as a separate fidelity subset.

Details: `verification_data/pcm_timestep_t99.md`, `verification_data/spotcheck_pcm_stage0.json`, and the
validation dossier, §11.

## Validation against experiments (at the dataset settings)

- **n-octadecane, Vogel & Thess (2019):**
  - liquid-fraction deviation 0.009 against their 2D model;
  - 0.030 against the experiment, whose real cell gains heat through the other walls.
- **Lauric acid, Kamkari & Shokouhmand (2014), plain wall:** mean absolute deviation 0.028; full melt 194.7
  against about 195 min. This may partly reflect cancellation between mesh and model error.
- **Finned walls (1 and 3 fins):**
  - about 0.1 too fast in the first hour, then converging;
  - 3-fin full melt 8 % early at 0.5 mm.
  - The remaining difference combines residual discretisation, properties, boundary conditions,
    experimental uncertainty and model form, which these runs do not separate.
- **Tilted cases:** within ±0.08.

## Splits (`thermbench_ml/pcm_splits.py`; by parameters or a hash of the case id)

| Split | Test set | Train / val / test |
|---|---|---|
| random | 10 % by hash | 389 / 59 / 52 |
| ood_fins | 4 or 5 fins (train on 0 to 3) | 320 / 41 / 139 |
| ood_drive | superheat above the design 90th percentile (27.81 K) | 398 / 51 / 51 |
| ood_material | lauric acid (train on octadecane) | 219 / 31 / 250 |
| ood_material_r | octadecane (train on lauric acid) | 226 / 24 / 250 |
| ood_tilt | 45° and heated from below (train on side heating) | 317 / 33 / 150 |

## Benchmark results (8 November; `thermbench_ml/pcm_final_2026-11-08/`, `thermbench_ml/extra_baselines_2026-11-08/`)

Three neural architectures (FNO, U-Net, a 4x4-patch Transolver), each plain and with a front-model prior
(hybrid), 3 seeds each, 108 jobs; 7 non-neural baselines. Field RMSE in K, mean of 3 seeds:

| Split | FNO | U-Net | Transolver | Best hybrid | IDW | Best baseline |
|---|---|---|---|---|---|---|
| random | 0.82 | **0.59** | 0.66 | U-Net 0.68 | 2.55 | RBF 1.98 |
| ood_fins | 3.79 | **1.76** | 2.31 | U-Net 1.82 | 4.90 | IDW 4.90 |
| ood_drive | 1.40 | **1.05** | 1.11 | U-Net 1.12 | 4.13 | RBF 4.02 |
| ood_tilt | **6.17** | 6.67 | 6.41 | FNO 6.66 | 7.67 | IDW 7.67 |
| ood_material | 12.90 | 5.92 | 6.11 | U-Net 5.61 | **5.35** | IDW 5.35 |
| ood_material_r | 34.45 | 9.19 | 16.66 | U-Net 7.48 | **3.55** | IDW 3.55 |

- **Within one material** (random, fins, drive, tilt), every neural variant has lower field RMSE than IDW.
- **Across materials,** IDW has lower field RMSE than the three-seed mean of every neural variant in both
  directions; on held-out n-octadecane it beats every seed of every variant. Material transfer is the open
  problem this family poses.
- **Field accuracy and melt time can rank models differently:** on held-out fins U-Net has the lower field
  RMSE and Transolver the lower t90 error (5.6 against 10.2 %, all runs crossing).
- Seed spread is large on the material splits (FNO ± 8.7 and ± 9.6 K), so single-seed rankings there are not
  reliable. Report seeds, not only means.
- The 39 retained solver-WARN cases change no ordering or conclusion when excluded from scoring.

## Known limitations

- **2D:** ideal adiabatic side walls, no 3D damping and constant properties.
- **One mesh (0.5 mm), with known early melting** (see Verification). Rankings of models that differ by less
  than this sensitivity should be read with care.
- **Fin surfaces:** fins are resolved on the cell grid, so 1 mm fins span two cells and the no-slip
  surface sits at cell centres.
- **Energy metric:** the ML `energy_err` covers sensible and latent energy in the PCM cells, normalised by
  their full-charge capacity. It excludes energy stored in the metal fins.
- **Melt-time metrics:** t99 (liquid fraction 0.99), the run end (0.995) and experimental "full melt" are
  different quantities. The ML reference t90 is interpolated between field snapshots; on all six test sets it
  matches the dense liquid-fraction series to within 0.10 % (median 0.001 to 0.003 %,
  `thermbench_ml/pcm_t90_ref_check.json`). ML melt-time scores use an input-only time horizon of 3 t_ref and report the share
  of runs that reach 90 %.

## Still missing for the release

License, version tag and DOI, data hosting. The PCM ML results are in (above); release
checkpoints are taken from the worker that trained each one and checked by rescoring.
