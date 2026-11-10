# Label noise floor (inlet velocity x 1.0001) vs network error, 24 test-side tank runs

| run | Ri | closure | floor field % dT | floor energy % | floor outlet % dT | FNO hc % dT | U-Net hc % dT |
|---|---|---|---|---|---|---|---|
| T0524_sst | 0.8 | kOmegaSST | 0.01 | 0.01 | 0.01 | 24.56 | 26.31 |
| T0019_sst | 2.9 | kOmegaSST | 0.02 | 0.01 | 0.01 | 11.61 | 10.41 |
| T0336_lam | 4.2 | laminar | 11.84 | 1.44 | 10.64 | 9.86 | 9.01 |
| T0180_lam | 4.5 | laminar | 7.88 | 1.63 | 6.77 | 9.24 | 9.39 |
| T0992_sst | 7.5 | kOmegaSST | 0.01 | 0.01 | 0.02 | 4.72 | 4.39 |
| T0496_lam | 8.2 | laminar | 0.07 | 0.02 | 0.19 | 5.33 | 5.08 |
| T0672_lam | 8.5 | laminar | 9.65 | 1.99 | 8.37 | 8.41 | 8.58 |
| T0228_sst | 8.8 | kOmegaSST | 0.04 | 0.01 | 0.04 | 7.53 | 14.02 |
| T0984_sst | 38.5 | kOmegaSST | 0.02 | 0.01 | 0.02 | 3.06 | 2.93 |
| T0194_lam | 41.8 | laminar | 2.74 | 0.16 | 1.80 | 3.67 | 3.68 |
| T0810_lam | 45.8 | laminar | 0.00 | 0.00 | 0.00 | 3.63 | 4.71 |
| T0626_sst | 50.0 | kOmegaSST | 0.02 | 0.01 | 0.03 | 4.19 | 4.05 |
| T0975_sst | 65.3 | kOmegaSST | 0.04 | 0.01 | 0.04 | 3.00 | 3.07 |
| T0306_lam | 76.7 | laminar | 4.01 | 0.32 | 2.10 | 3.32 | 3.11 |
| T0999_sst | 128.0 | kOmegaSST | 0.01 | 0.01 | 0.02 | 2.63 | 2.29 |
| T0119_lam | 154.0 | laminar | 0.25 | 0.02 | 0.36 | 2.36 | 2.19 |
| T0733_sst | 224.2 | kOmegaSST | 0.03 | 0.01 | 0.02 | 3.02 | 6.08 |
| T0189_lam | 233.6 | laminar | 3.18 | 0.14 | 2.21 | 3.31 | 3.13 |
| T1021_lam | 251.9 | laminar | 5.06 | 0.27 | 2.80 | 5.36 | 5.02 |
| T0085_sst | 536.3 | kOmegaSST | 0.06 | 0.01 | 0.04 | 2.54 | 7.27 |
| T0821_sst | 754.9 | kOmegaSST | 0.05 | 0.01 | 0.17 | 2.01 | 1.92 |
| T0645_sst | 856.4 | kOmegaSST | 0.03 | 0.01 | 0.02 | 2.33 | 1.91 |
| T0369_lam | 1448.4 | laminar | 0.32 | 0.02 | 0.09 | 1.88 | 1.46 |
| T0665_lam | 2338.4 | laminar | 0.24 | 0.06 | 1.70 | 1.30 | 0.96 |

{
 "n": 24,
 "floor_field_pct_median": 0.055854307094898394,
 "floor_field_pct_max": 11.841432494185373,
 "rho_floor_logRi": 0.13391304347826086,
 "by_closure": {
  "laminar": {
   "median": 2.9599080377160787,
   "max": 11.841432494185373
  },
  "kOmegaSST": {
   "median": 0.025742451634385845,
   "max": 0.05715604636187542
  }
 },
 "model_over_floor_median": 75.21749817410272,
 "share_runs_model_error_below_2x_floor": 0.2916666666666667
}