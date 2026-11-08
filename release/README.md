# Release preparation (state of 8 November 2026)

What a user needs to reproduce or reuse ThermalStorageBench, collected ahead of the release. The license,
version tag and DOI are decided at the end. The name is **ThermalStorageBench**, always in full (never
"ThermBench"); code, folder and file names (`thermbench_ml`, `thermbench.h5`) are renamed at release.

## Frozen manifests (in the repository)

| Family | File | Runs | md5 |
|---|---|---|---|
| Tank (2D, OpenFOAM) | `thermbench_ml/manifest_full_h5mm.json` | 1,212 | `0e8b6d8ddfc9be4b882e25762c26b3ec` |
| PCM (2D, OpenFOAM) | `thermbench_ml/manifest_pcm.json` | 500 | `19397b78801e26909fe8d0e369cd9bca` |

Each entry gives the run id, its h5 size and md5. The PCM entries also give the source machine and path, and
the evidence that the run used the final solver set-up. `thermbench_ml/check_data.py <manifest>` verifies a
local copy against these md5s.

## Software environment

| File | What |
|---|---|
| `env_laptop.txt` | OS, Python, PyTorch/CUDA, h5py/HDF5, numpy and OpenFOAM versions on the hub machine |
| `requirements_gpu_freeze.txt` | `pip freeze` of the training environment (PyTorch 2.14.1 + CUDA 12.6, Python 3.12.3) |
| `requirements_cpu_freeze.txt` | `pip freeze` of the analysis environment |

**Machines (checked 8 November; identical software on all six):** Ubuntu 24.04 under WSL2, Python 3.12.3,
PyTorch 2.14.1+cu126 (CUDA 12.6), numpy 1.26.4, h5py 3.10.0, OpenFOAM v2606. The laptop's `pip freeze` is
byte-identical to `requirements_gpu_freeze.txt`.

| Machine | CPU | GPU (memory, driver) | Used for |
|---|---|---|---|
| lab | AMD Ryzen 9 5950X, 32 threads | RTX 4070 Ti (12 GB, 576.80) | CFD, ML training |
| pc4 | AMD Threadripper PRO 5955WX, 32 threads | RTX 4070 Ti (12 GB, 610.88) | CFD, ML training |
| pc3 | Intel i7-14700K, 28 threads | RTX 4060 (8 GB, 610.88) | CFD, ML training |
| pc6 | Intel i7-14700K, 28 threads | RTX 4060 (8 GB, 610.88) | CFD, ML training |
| pc7 | Intel i7-14700K, 28 threads | RTX 4060 (8 GB, 610.88) | CFD, ML training |
| laptop | Intel i9-13900HX, 32 threads | RTX 4060 Laptop (8 GB, 591.86) | hub, ML training, all rescoring |

(pc5, used for part of the tank CFD and early ML jobs, is no longer available.)

The CFD was run with OpenFOAM v2606 (`/usr/lib/openfoam/openfoam2606`, buoyantPimpleFoam). The case
generators are `scripts/make_tank_case.py` and `scripts/make_pcm_case.py`; every run's `case.json` (also
stored in its h5 as `case_json`) gives all inputs.

## Reading the data

`load_example.py` reads one run with h5py and numpy only (tested on T0014_lam):
```
python load_example.py <run folder>
```
The benchmark code (`thermbench_ml/`) has the full pipeline: data access (`data.py`, `pcm_data.py`), splits,
metrics, baselines, training and evaluation; see `thermbench_ml/README.md`.

## Checkpoints to ship

Rule (from the tank rebuild, `thermbench_ml/repro_all_2026-11-08/RESULT.md`): every released checkpoint is
taken from the worker that produced its stored score, and is rescored from the frozen data before upload.

| Family | Checkpoints | Folder | Rescored |
|---|---|---|---|
| Tank (FNO, U-Net; 4 variants; 3 seeds; 4 splits) | 96 | `thermbench_ml/results_merged/ckpt` | 96 of 96 exact (`repro_all_2026-11-08`) |
| PCM (FNO, U-Net, Transolver; plain and hybrid; 3 seeds; 6 splits) | 108 | `thermbench_ml/results_pcm_release/ckpt` (`repro_pcm_2026-11-08/collect_ckpt.sh`, sources and md5 in `ckpt_sources.tsv`) | `repro_pcm_2026-11-08` |

Do not ship `results_merged/ckpt_unet_s2_ood_flow.pt.WRONG_SOURCE_532c650e`, `results_pcm_merged/ckpt` (an
earlier copy of the FNO hybrid checkpoints made by globbing all workers) or any pilot folder.

## Documentation to ship

- **Tank:** dataset card `DATASET_CARD_tank_draft.md` and boundary conditions
  `verification_data/tank_boundary_conditions.md`.
- **PCM:** dataset card `DATASET_CARD_pcm_draft.md` (with benchmark results, 8 November).
- **Verification and validation:** `verification_criteria_2026-11-06.md`, `verification_data/`,
  `validation_Lou2023_case_data.md`.
- **Label flags:** `thermbench_ml/label_flags_tank.json`.

## Still to do before release

- License.
- Version tag and DOI.
- Rename code, folder and file names to ThermalStorageBench; GitHub repos `thermalbench` and
  `thermalbench-data` (renamed by Saxam on github.com).
- The data archive itself (h5 files, about 61 GB for the tank and 9.7 GB for PCM) with its hosting.
