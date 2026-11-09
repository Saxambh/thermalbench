# ThermalStorageBench: data deposit README (draft, 9 November 2026)

To be placed in the repository record next to the archives. Fill in the [bracketed] items at release.

ThermalStorageBench is an open benchmark of transient two-dimensional CFD simulations for machine learning
in thermal energy storage. It accompanies the article "ThermalStorageBench: A CFD benchmark for machine
learning in sensible and latent thermal energy storage" [journal, DOI].

## Contents

| Archive | What it holds | Size |
|---|---|---|
| `tank_runs_01.tar` to `tank_runs_11.tar` | 1,212 stratified-tank runs (1,020 design points), one folder per run | 54.5 GB |
| `pcm_runs_01.tar`, `pcm_runs_02.tar` | 500 PCM melting runs, one folder per run | 10.3 GB |
| `checkpoints.tar` | 96 tank and 108 PCM network checkpoints (FNO, U-Net, Transolver; 3 seeds), with provenance tables | 4.2 GB |
| `manifests.tar` | frozen manifests with the md5 of every run's h5 file, split code, label flags, dataset cards | < 0.01 GB |
| `SHA256SUMS` | SHA-256 of every archive | |

Sizes in decimal GB.

**Each run folder** contains:
- `thermbench.h5`;
- `case.json` (all inputs);
- `metrics.json`;
- `qc.json`;
- `system/` (the OpenFOAM solver dictionaries).

**Tank `thermbench.h5`:**
- `fields/T`, `p_rgh`, `ux`, `uy` (and `k`, `omega`, `nut` for SST runs) at 121 snapshots on the native
  5 mm grid;
- `metrics/` per snapshot: stored energy `E_J`, exergy `Ex_J`, `MIX`, `Str`, mean and outlet temperature,
  thermocline midpoint and thickness;
- `series/`: dense outlet temperature, outlet mass and enthalpy flow, and mean temperature;
- `times_s` and `tstar`.

**PCM `thermbench.h5`:**
- `fields/T`, `alpha` (liquid fraction), `ux`, `uy` at 88 to 204 snapshots on the 0.5 mm grid;
- `mask` (PCM = 1, fin = 0);
- `metrics/` per snapshot: stored energy, Nusselt number, heat input, mean temperature, liquid fraction and
  energy-balance error;
- `series/`: dense series of the same quantities;
- `times_s` and `tstar`.

## Verify a download

```bash
sha256sum -c SHA256SUMS                         # archives
python check_data.py manifest_full_h5mm.json    # every tank h5 against its md5 (benchmark code)
python check_data.py manifest_pcm.json
```

## Use

- **Code:** [repository URL, code DOI]. The benchmark code loads the runs, applies the fixed splits, scores
  models with the paper's metrics and runs the released checkpoints. `example_evaluate.py` reproduces table
  values of the paper and shows how to score a new model.
- **One run with h5py only:** `load_example.py`.

## Known limitations

- Two-dimensional, adiabatic walls.
- One mesh per family, not mesh-converged: the PCM labels melt early by up to 8.7 % relative to a 0.25 mm
  mesh.
- Two tank runs carry a numerical-setting uncertainty of about 7 % of ΔT and are flagged
  (`label_flags_tank.json`).
- PCM: melting only, constant properties.

See the dataset cards and the article.

## Licence and citation

- **Data and checkpoints:** [CC BY 4.0, proposed].
- **Code:** [MIT, proposed].
- Please cite the article and this record (https://doi.org/10.5281/zenodo.24087719); see CITATION.cff.
