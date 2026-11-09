# Lou et al. (2023) outlet temperature: final comparison (9 November 2026)

**Case:** uniform baffle, 1 L/min, 333.15 K into 293.15 K, our 3D OpenFOAM SST run (lab, 8 ranks).
- **Run:** 0 to 750 s (`ours_outletT_0_750s.dat`), then extended from 750 to 1,275 s = t* 1.507
  (`ours_outletT_750_1275s.dat`, `sst_ext`). The extension ended normally ("EXIT 0", 2026-11-08 21:00 UTC).
- **Experiment:** Fig. 15a, Ri_bulk, digitised, converted by T*_out = 1 - Ri/Ri0 (`compare.py`,
  `fig15_333K_initial.json`).
- **Scripts:** `compare.py` (`compare.json`), `beta_sens.py` (property assumption in Ri_bulk), `sigma_cmp.py`
  (Lou's charging efficiency σ).

## Results

| t* | 0.70 | 0.80 | 0.85 | 0.90 | 1.00 | 1.10 | 1.20 | 1.30 | 1.45 |
|---|---|---|---|---|---|---|---|---|---|
| Lou, constant β | 0.027 | 0.108 | 0.221 | 0.293 | 0.459 | 0.592 | 0.685 | 0.753 | 0.824 |
| Lou, β at mean T | 0.043 | 0.160 | 0.301 | 0.383 | 0.552 | 0.673 | 0.754 | 0.809 | 0.866 |
| Ours | 0.006 | 0.088 | 0.226 | 0.400 | 0.658 | 0.792 | 0.864 | 0.917 | 0.957 |

- **Breakthrough onset (T* = 0.1):** t* 0.806 (ours) vs 0.796 (Lou): 8.6 s later, within 0.01 t*.
- **Before and at breakthrough (t* 0.50 to 0.85):** within 0.024 (constant β).
- **After breakthrough (t* 0.90 to 1.45):** ours is warmer:
  - +0.11 to +0.20 with constant β (mean +0.10 and RMS 0.13 over all 20 compared points from t* 0.50);
  - +0.08 to +0.12 from t* 0.95 with β at the mean of inlet and outlet temperature.
  - β at the outlet temperature is not a valid reading (T* 0.43 on the plateau).
- **50 % crossing:** t* 0.932 (ours) vs 1.045 (constant β) / about 0.97 (β at mean T): ours is earlier by
  0.04 to 0.11 t* (30 to 96 s).
- **Charging efficiency σ (independent of the β question):**
  - Lou's σ rises with slope 0.81 on the pre-breakthrough plateau, where a loss-free, perfectly measured
    tank gives 1.0;
  - it stays below ours: 0.750 vs 0.919 at t* 1.0, and 0.850 vs 0.985 at t* 1.5.

## Reading

- Breakthrough timing is reproduced.
- After breakthrough the simulated outlet is 0.08 to 0.20 warmer in T*. The exact figure depends on an
  unstated property assumption in the published Ri_bulk.
- The sign matches heat loss from the experiment's uninsulated tank. Lou's σ also points to a deficit of
  this kind (plateau slope 0.81).
- Our walls are adiabatic. Wall loss is not modelled, because the paper gives no heat-transfer coefficient,
  and fitting one to this curve would be tuning to the validation target.
- The published data do not allow a tighter bound.
- For the dataset (2D, adiabatic) this is a statement about the solver set-up, as for the jet depth h_j.
  It is not direct validation of the 2D tank labels.
