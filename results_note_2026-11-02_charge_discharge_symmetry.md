# Results note: charge/discharge symmetry fixes the operating-mode split (2026-11-02)

**Status.** Interim result on 246 finished tank runs (frozen list: `thermbench_ml/results_modediag_2026-11-02/manifest.json`). To be confirmed in the final benchmark (all runs, 3 seeds, FNO and U-Net). Full tables: `results_modediag_2026-11-02/r2_report.md`.

## The problem

**The split.** `ood_mode` trains on charging runs only (156 train, 18 validation) and tests on all discharging runs (72).

**What happened.** In the interim benchmark of the same day:
- The hybrid FNO (plug flow + learned correction) reached 0.77 K on the random split.
- On `ood_mode` it got 2.9 K, worse than plug flow alone on stored energy, thermocline position and outlet temperature.
- The nearest-neighbour baseline failed completely (17 K).

**Why.** The model's `discharge` input is 0 in every training run, so at test time it meets a value it has never seen. The discharge runs also look different on screen:
- **Charging:** hot water enters at the top left, and the outlet is at the bottom right.
- **Discharging:** cold water enters at the bottom right, and the outlet is at the top left.

The corrections learned on charging land in the wrong places.

## The fix: canonical frame (`train.py --canon`)

**The symmetry.** A discharge run is a charge run turned by 180 degrees with hot and cold swapped (theta -> 1 − theta).
- Under the Boussinesq approximation with constant properties this is exact: turning the tank upside down reverses gravity, and swapping hot and cold reverses the buoyancy again.
- With the real, temperature-dependent water properties used here it is approximate.

**Implementation.**
- Discharge runs are rotated and inverted into the charge frame on the way in: initial field, port maps, plug-flow base and target.
- Their `discharge` flag is set to 0.
- The prediction is transformed back before scoring, so all metrics are in the run's own frame and comparable with every other model.
- Network, training and data are otherwise unchanged.

**Checks before training.**
- The transform is its own inverse (round-trip error 3e-8, float32 rounding).
- A discharge run in the charge frame has its inlet at the top left (88–90 % of the height; charge runs have 83–86 %).

## Results

### Unseen discharging runs (72 test runs, 3 seeds each)

| Model | Field RMSE [95 % CI] | Field R² | Outlet T MAE | Thermocline MAE | Stored-energy MAE |
|---|---|---|---|---|---|
| **Hybrid FNO, canonical frame** | **0.68 ± 0.02 K** (seeds 0.66 / 0.70 / 0.68; CI of each about ±0.1) | 0.993 | 0.90–0.98 K | 4 mm | 0.3 % |
| Hybrid FNO, plain | 2.86 ± 0.10 K (seeds 2.98 / 2.80 / 2.80; CI of each about ±0.5) | 0.91–0.92 | 1.8–2.9 K | 22–37 mm | 2.7–3.7 % |
| Plug flow (physics only) | 3.93 K [3.28, 4.61] | 0.865 | 1.53 K | 17 mm | 2.2 % |
| Nearest neighbour | 17.4 K | −1.41 | 8.9 K | 528 mm | 54 % |

- The canonical frame cuts the field error by a factor of **4.2**. The confidence intervals do not overlap: canonical seeds [0.56, 0.81] K, plain seeds [2.27, 3.53] K.
- The plain hybrid also loses track of the thermocline: it finds no thermocline in 9–22 % of snapshots, against 1.3–1.5 % for the canonical frame.

### Random split (21 test runs, seed 0, same frozen run list)

| Model | Field RMSE [95 % CI] | Field R² | Outlet T MAE | Thermocline MAE |
|---|---|---|---|---|
| Hybrid FNO, canonical frame | 0.65 K [0.49, 0.83] | 0.997 | 0.72 K | 3 mm |
| Hybrid FNO, plain | 0.75 K [0.56, 0.96] | 0.996 | 1.00 K | 3 mm |
| Plug flow | 4.18 K [3.15, 5.35] | 0.867 | 1.49 K | 14 mm |

- No harm, and probably a gain: in the charge frame every discharge run counts as extra charging data.
- The intervals overlap, since this is one seed on 21 runs. Confirm with 3 seeds in the final benchmark, ideally with a paired comparison on the same test runs.

### Ablation: symmetry and physics base, separately (ood_mode, seed 0, same run list; 2026-11-02 19:10 UTC)

| | No physics base (plain FNO) | With plug-flow base (hybrid FNO) |
|---|---|---|
| Run's own frame | **18.0 K** (R² field −1.9: total failure, as bad as predicting the initial state) | 2.98 K |
| Canonical frame | **1.75 K** | **0.66 K** |
| Physics baseline, for reference | 3.93 K | |

- **Symmetry alone** turns the plain FNO from total failure (18.0 K) into a usable model (1.75 K), a factor of 10.
- **Physics base alone** helps the most when there is no symmetry, from 18.0 to 2.98 K (factor 6). It does not transfer the learned correction to the new mode.
- **Both together** give 0.66 K. The two are complementary:
  - the base supplies the large-scale energy and front position;
  - the canonical frame lets the learned correction transfer to the new mode.
- **Decision:** the final benchmark is a full 2 × 2 ablation for both architectures. `run_final.sh` now has 8 models: plain, canon, hybrid and hybrid_canon, for FNO and for U-Net.

## Interpretation

1. **What caused the failure.** The model did not know the symmetry. Unknown physics was not the issue. A model that has never seen a discharge run predicts them at the level of the CFD noise floor (about 0.65 K).
2. **The water-property asymmetry is negligible.** Real, temperature-dependent water properties do not break the charge/discharge mirror enough to matter over our temperature range.
3. **Practical consequence.** A surrogate needs simulations of one operating mode only, which halves the simulation cost of building one.
4. **For the benchmark.** The `ood_mode` split separates generic from physics-aware surrogates. Both are reported:
   - the plain hybrid as the generic ML result;
   - the canonical-frame hybrid as the physics-aware one.

## Novelty position

See `novelty_recheck_2026-11-02.md`, addendum: Scopus S5–S8.
- **Established:** building symmetries into networks for fluids (Wang, Walters & Yu 2021, 2022; Siddani et al. 2021; Lino et al. 2022). We do not claim the method.
- **Not found in Scopus:** any use of the charge/discharge symmetry, or any symmetry, in ML for thermal storage; any test of charge-to-discharge transfer.
- **Safe wording:** "the tank's charge/discharge symmetry, applied as a simple change of frame, lets a surrogate trained only on charging predict discharging at the CFD noise level".
- **Before submission:** check arXiv.

## Decisions (2026-11-02, Saxam)

- **Main model.** The canonical-frame hybrid is the main model in the final benchmark. `run_final.sh` trains eight models (the 2 × 2 ablation, see above):
  - fno, fno_canon, fno_hybrid, fno_hybrid_canon;
  - unet, unet_canon, unet_hybrid, unet_hybrid_canon;
  - each × 4 splits × 3 seeds.
- **Code.** `train.py --canon`; `train.py` and `evaluate.py` have `--outdir`. Backup of the previous train.py: scratchpad `train.py.bak_canon`.

## Open points

- **Limits of the symmetry.** It breaks with heat losses through the walls, with diffusers that differ between the top and bottom ports, and possibly at temperature differences larger than ours. Say so in the paper.
- **Plain FNO.** Done (2026-11-02): it gains from the canonical frame too, 18.0 to 1.75 K (see the ablation above). Confirm with 3 seeds in the final runs.
- **Flow split.** `ood_flow` still has no test runs; the fast-inflow cases are not finished.
