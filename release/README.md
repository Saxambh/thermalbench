# Release preparation (state of 7 November 2026)

What a user needs to reproduce or reuse HeatStoreBench, collected ahead of the release. The license,
version tag, DOI and final project name are decided at the end (the renaming happens last).

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

## Documentation to ship

- **Tank:** dataset card `DATASET_CARD_tank_draft.md` and boundary conditions
  `verification_data/tank_boundary_conditions.md`.
- **PCM:** dataset card `DATASET_CARD_pcm_draft.md` (drafted 8 November).
- **Verification and validation:** `verification_criteria_2026-11-06.md`, `verification_data/`,
  `validation_Lou2023_case_data.md`.
- **Label flags:** `thermbench_ml/label_flags_tank.json`.

## Still to do before release

- License.
- Version tag and DOI.
- The final project name.
- The data archive itself (h5 files, about 61 GB for the tank and 9.7 GB for PCM) with its hosting.
