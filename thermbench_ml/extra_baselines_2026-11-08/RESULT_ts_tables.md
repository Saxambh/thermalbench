# PCM with the 4x4-patch Transolver baseline: tables (8 November 2026)

Reconciliation: all 36 Transolver entries match the frozen test splits and sizes.

Neural rows: mean of the 3 seeds (± seed SD of the field RMSE), then the three seeds' field RMSE. t90 error is relative, conditional on the prediction crossing a liquid fraction of 0.9 within tau <= 3 t_ref. Last column: field RMSE without the 39 retained solver-WARN cases (change in brackets). FNO, U-Net and baseline rows are the same numbers as pcm_final_2026-11-08.

## random: 52 test runs (3 solver-WARN)

| Model | Field RMSE, K (seed mean ± SD) | per seed | Liquid IoU | Energy err | Crossed t90 (of n) | t90 err, crossed | RMSE without WARN |
|---|---|---|---|---|---|---|---|
| initial | 21.80 |  | 0.000 | 67.7 % | 0.0 / 52 | nan % | 21.96 (+0.16) |
| stefan | 14.00 |  | 0.336 | 45.1 % | 0.0 / 52 | nan % | 14.05 (+0.05) |
| front | 10.21 |  | 0.741 | 8.6 % | 52.0 / 52 | 18.3 % | 10.22 (+0.01) |
| knn | 2.54 |  | 0.894 | 2.9 % | 52.0 / 52 | 11.9 % | 2.51 (-0.03) |
| nn | 3.08 |  | 0.883 | 3.0 % | 51.0 / 52 | 12.0 % | 2.99 (-0.09) |
| idw | 2.55 |  | 0.901 | 3.2 % | 52.0 / 52 | 12.9 % | 2.51 (-0.04) |
| rbf | 1.98 |  | 0.918 | 1.9 % | 52.0 / 52 | 9.1 % | 1.97 (-0.01) |
| fno | 0.82 ± 0.00 | 0.82 / 0.82 / 0.81 | 0.982 | 0.5 % | 52.0 / 52 | 1.5 % | 0.82 (-0.00) |
| unet | 0.59 ± 0.01 | 0.58 / 0.60 / 0.60 | 0.989 | 0.3 % | 52.0 / 52 | 1.1 % | 0.59 (-0.00) |
| **transolver** | 0.66 ± 0.02 | 0.64 / 0.68 / 0.66 | 0.986 | 0.3 % | 52.0 / 52 | 0.8 % | 0.67 (+0.00) |
| fno_hybrid | 0.86 ± 0.01 | 0.85 / 0.87 / 0.86 | 0.982 | 0.4 % | 52.0 / 52 | 1.2 % | 0.86 (-0.00) |
| unet_hybrid | 0.68 ± 0.03 | 0.66 / 0.66 / 0.71 | 0.986 | 0.4 % | 52.0 / 52 | 1.1 % | 0.68 (+0.00) |
| **transolver_hybrid** | 0.72 ± 0.01 | 0.74 / 0.72 / 0.71 | 0.985 | 0.3 % | 52.0 / 52 | 0.7 % | 0.72 (-0.00) |

## ood_fins: 139 test runs (15 solver-WARN)

| Model | Field RMSE, K (seed mean ± SD) | per seed | Liquid IoU | Energy err | Crossed t90 (of n) | t90 err, crossed | RMSE without WARN |
|---|---|---|---|---|---|---|---|
| initial | 22.58 |  | 0.000 | 71.4 % | 0.0 / 139 | nan % | 22.65 (+0.07) |
| stefan | 15.63 |  | 0.237 | 53.5 % | 0.0 / 139 | nan % | 15.55 (-0.08) |
| front | 10.50 |  | 0.731 | 12.0 % | 139.0 / 139 | 26.2 % | 10.39 (-0.11) |
| knn | 4.96 |  | 0.767 | 7.1 % | 139.0 / 139 | 35.9 % | 4.89 (-0.08) |
| nn | 5.52 |  | 0.753 | 7.5 % | 139.0 / 139 | 36.4 % | 5.43 (-0.09) |
| idw | 4.90 |  | 0.772 | 7.0 % | 139.0 / 139 | 36.0 % | 4.81 (-0.09) |
| rbf | 7.30 |  | 0.738 | 6.4 % | 131.0 / 139 | 55.5 % | 7.15 (-0.15) |
| fno | 3.79 ± 0.13 | 3.78 / 3.92 / 3.66 | 0.859 | 3.9 % | 139.0 / 139 | 16.5 % | 3.68 (-0.10) |
| unet | 1.76 ± 0.07 | 1.72 / 1.84 / 1.73 | 0.956 | 1.9 % | 139.0 / 139 | 10.2 % | 1.71 (-0.05) |
| **transolver** | 2.31 ± 0.06 | 2.38 / 2.25 / 2.32 | 0.895 | 1.7 % | 139.0 / 139 | 5.6 % | 2.27 (-0.04) |
| fno_hybrid | 3.05 ± 0.19 | 3.10 / 2.84 / 3.20 | 0.880 | 2.9 % | 139.0 / 139 | 7.9 % | 2.97 (-0.07) |
| unet_hybrid | 1.82 ± 0.01 | 1.81 / 1.81 / 1.83 | 0.952 | 2.1 % | 139.0 / 139 | 11.1 % | 1.77 (-0.05) |
| **transolver_hybrid** | 2.70 ± 0.13 | 2.73 / 2.82 / 2.56 | 0.892 | 2.5 % | 139.0 / 139 | 7.7 % | 2.64 (-0.07) |

## ood_drive: 51 test runs (4 solver-WARN)

| Model | Field RMSE, K (seed mean ± SD) | per seed | Liquid IoU | Energy err | Crossed t90 (of n) | t90 err, crossed | RMSE without WARN |
|---|---|---|---|---|---|---|---|
| initial | 27.45 |  | 0.000 | 66.1 % | 0.0 / 51 | nan % | 27.35 (-0.11) |
| stefan | 20.28 |  | 0.309 | 46.7 % | 0.0 / 51 | nan % | 20.12 (-0.16) |
| front | 14.04 |  | 0.735 | 9.5 % | 51.0 / 51 | 15.8 % | 14.03 (-0.01) |
| knn | 4.25 |  | 0.868 | 3.4 % | 51.0 / 51 | 16.0 % | 3.90 (-0.35) |
| nn | 4.81 |  | 0.852 | 3.3 % | 51.0 / 51 | 16.0 % | 4.23 (-0.58) |
| idw | 4.13 |  | 0.873 | 3.3 % | 51.0 / 51 | 16.2 % | 3.81 (-0.32) |
| rbf | 4.02 |  | 0.872 | 2.5 % | 51.0 / 51 | 8.4 % | 3.72 (-0.30) |
| fno | 1.40 ± 0.02 | 1.39 / 1.42 / 1.38 | 0.978 | 0.6 % | 51.0 / 51 | 2.0 % | 1.32 (-0.08) |
| unet | 1.05 ± 0.06 | 1.00 / 1.02 / 1.12 | 0.987 | 0.4 % | 51.0 / 51 | 1.2 % | 0.99 (-0.06) |
| **transolver** | 1.11 ± 0.01 | 1.11 / 1.13 / 1.11 | 0.984 | 0.3 % | 51.0 / 51 | 1.0 % | 1.05 (-0.06) |
| fno_hybrid | 1.49 ± 0.01 | 1.50 / 1.48 / 1.48 | 0.978 | 0.5 % | 51.0 / 51 | 2.0 % | 1.40 (-0.09) |
| unet_hybrid | 1.12 ± 0.02 | 1.14 / 1.10 / 1.13 | 0.985 | 0.5 % | 51.0 / 51 | 1.5 % | 1.07 (-0.06) |
| **transolver_hybrid** | 1.19 ± 0.01 | 1.19 / 1.18 / 1.18 | 0.983 | 0.3 % | 51.0 / 51 | 1.1 % | 1.12 (-0.06) |

## ood_material: 250 test runs (24 solver-WARN)

| Model | Field RMSE, K (seed mean ± SD) | per seed | Liquid IoU | Energy err | Crossed t90 (of n) | t90 err, crossed | RMSE without WARN |
|---|---|---|---|---|---|---|---|
| initial | 22.46 |  | 0.000 | 66.9 % | 0.0 / 250 | nan % | 22.61 (+0.15) |
| stefan | 14.33 |  | 0.340 | 43.9 % | 1.0 / 250 | 243.0 % | 14.38 (+0.05) |
| front | 9.71 |  | 0.751 | 8.3 % | 250.0 / 250 | 26.3 % | 9.73 (+0.02) |
| knn | 5.53 |  | 0.838 | 5.8 % | 250.0 / 250 | 17.1 % | 5.64 (+0.11) |
| nn | 5.96 |  | 0.823 | 6.7 % | 250.0 / 250 | 19.5 % | 6.07 (+0.11) |
| idw | 5.35 |  | 0.844 | 5.7 % | 250.0 / 250 | 16.9 % | 5.45 (+0.10) |
| rbf | 56.96 |  | 0.557 | 24.4 % | 177.0 / 250 | 57.1 % | 56.63 (-0.33) |
| fno | 12.90 ± 8.72 | 8.49 / 22.95 / 7.27 | 0.560 | 28.3 % | 250.0 / 250 | 70.4 % | 12.92 (+0.02) |
| unet | 5.92 ± 0.61 | 5.63 / 5.51 / 6.62 | 0.766 | 10.9 % | 250.0 / 250 | 36.1 % | 5.99 (+0.07) |
| **transolver** | 6.11 ± 0.29 | 5.86 / 6.43 / 6.05 | 0.730 | 9.3 % | 250.0 / 250 | 24.3 % | 6.16 (+0.05) |
| fno_hybrid | 8.82 ± 3.02 | 7.68 / 12.25 / 6.53 | 0.762 | 11.6 % | 250.0 / 250 | 55.1 % | 8.87 (+0.05) |
| unet_hybrid | 5.61 ± 1.38 | 7.20 / 4.68 / 4.96 | 0.854 | 8.8 % | 250.0 / 250 | 52.9 % | 5.68 (+0.07) |
| **transolver_hybrid** | 7.51 ± 0.22 | 7.28 / 7.54 / 7.70 | 0.768 | 6.9 % | 250.0 / 250 | 23.7 % | 7.57 (+0.06) |

## ood_material_r: 250 test runs (15 solver-WARN)

| Model | Field RMSE, K (seed mean ± SD) | per seed | Liquid IoU | Energy err | Crossed t90 (of n) | t90 err, crossed | RMSE without WARN |
|---|---|---|---|---|---|---|---|
| initial | 20.64 |  | 0.000 | 67.2 % | 0.0 / 250 | nan % | 20.67 (+0.03) |
| stefan | 13.75 |  | 0.320 | 46.3 % | 2.0 / 250 | 264.4 % | 13.68 (-0.07) |
| front | 10.44 |  | 0.725 | 10.5 % | 250.0 / 250 | 17.6 % | 10.39 (-0.05) |
| knn | 3.60 |  | 0.855 | 5.6 % | 250.0 / 250 | 27.8 % | 3.58 (-0.02) |
| nn | 4.40 |  | 0.823 | 6.5 % | 246.0 / 250 | 27.6 % | 4.37 (-0.03) |
| idw | 3.55 |  | 0.859 | 5.6 % | 250.0 / 250 | 27.9 % | 3.51 (-0.03) |
| rbf | 21.95 |  | 0.673 | 10.1 % | 223.0 / 250 | 32.9 % | 21.86 (-0.09) |
| fno | 34.45 ± 9.59 | 45.53 / 29.00 / 28.83 | 0.226 | 65.8 % | 83.3 / 250 | 100.0 % | 34.52 (+0.07) |
| unet | 9.19 ± 1.08 | 8.57 / 10.44 / 8.57 | 0.710 | 19.8 % | 194.7 / 250 | 108.5 % | 9.26 (+0.07) |
| **transolver** | 16.66 ± 3.48 | 20.52 / 15.68 / 13.78 | 0.217 | 42.0 % | 5.0 / 250 | 218.8 % | 16.69 (+0.03) |
| fno_hybrid | 11.61 ± 3.36 | 10.78 / 8.74 / 15.31 | 0.726 | 11.1 % | 196.7 / 250 | 32.0 % | 11.63 (+0.02) |
| unet_hybrid | 7.48 ± 1.42 | 7.07 / 9.07 / 6.32 | 0.759 | 9.1 % | 250.0 / 250 | 30.4 % | 7.52 (+0.03) |
| **transolver_hybrid** | 15.77 ± 3.33 | 19.17 / 15.61 / 12.52 | 0.596 | 18.4 % | 16.7 / 250 | 281.5 % | 15.76 (-0.00) |

## ood_tilt: 150 test runs (11 solver-WARN)

| Model | Field RMSE, K (seed mean ± SD) | per seed | Liquid IoU | Energy err | Crossed t90 (of n) | t90 err, crossed | RMSE without WARN |
|---|---|---|---|---|---|---|---|
| initial | 18.88 |  | 0.000 | 59.8 % | 0.0 / 150 | nan % | 18.72 (-0.17) |
| stefan | 12.22 |  | 0.318 | 41.5 % | 0.0 / 150 | nan % | 11.91 (-0.31) |
| front | 7.71 |  | 0.715 | 10.4 % | 150.0 / 150 | 34.7 % | 7.51 (-0.20) |
| knn | 7.71 |  | 0.731 | 11.8 % | 150.0 / 150 | 20.9 % | 7.67 (-0.05) |
| nn | 8.00 |  | 0.720 | 12.2 % | 145.0 / 150 | 21.7 % | 7.94 (-0.06) |
| idw | 7.67 |  | 0.733 | 11.8 % | 150.0 / 150 | 20.7 % | 7.62 (-0.06) |
| rbf | 12.84 |  | 0.662 | 10.1 % | 138.0 / 150 | 29.5 % | 12.24 (-0.60) |
| fno | 6.17 ± 0.58 | 6.46 / 5.50 / 6.55 | 0.794 | 8.1 % | 150.0 / 150 | 14.8 % | 6.10 (-0.06) |
| unet | 6.67 ± 0.13 | 6.55 / 6.65 / 6.80 | 0.791 | 9.6 % | 150.0 / 150 | 14.4 % | 6.61 (-0.06) |
| **transolver** | 6.41 ± 0.33 | 6.79 / 6.25 / 6.18 | 0.796 | 7.7 % | 150.0 / 150 | 13.8 % | 6.34 (-0.07) |
| fno_hybrid | 6.66 ± 0.34 | 6.73 / 6.97 / 6.29 | 0.795 | 9.2 % | 150.0 / 150 | 13.5 % | 6.59 (-0.07) |
| unet_hybrid | 7.12 ± 0.11 | 7.24 / 7.08 / 7.04 | 0.778 | 11.4 % | 150.0 / 150 | 17.6 % | 7.07 (-0.05) |
| **transolver_hybrid** | 6.94 ± 0.10 | 6.99 / 6.83 / 6.99 | 0.788 | 9.7 % | 150.0 / 150 | 13.6 % | 6.87 (-0.07) |


# Paired differences: other model minus Transolver (descriptive)

Positive: Transolver better. Mean over test runs with a 95 % percentile bootstrap interval over runs (10,000, seed 20261108). Neural scores are the per-run mean of 3 seeds. Plain Transolver is compared with plain FNO and U-Net, hybrid with hybrid. t90: runs where both models cross in every seed (n given).

## random (52 runs)

| Transolver | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| transolver | fno | +0.15 [+0.10, +0.21], Transolver better | +0.22 [+0.16, +0.27], Transolver better | +0.74 [+0.51, +0.96], Transolver better (n 52) |
| transolver | unet | -0.07 [-0.11, -0.04], Transolver worse | +0.09 [+0.03, +0.14], Transolver better | +0.27 [+0.04, +0.51], Transolver better (n 52) |
| transolver | idw | +1.89 [+1.53, +2.26], Transolver better | +2.91 [+2.16, +3.70], Transolver better | +12.09 [+7.66, +17.13], Transolver better (n 52) |
| transolver_hybrid | fno_hybrid | +0.14 [+0.09, +0.19], Transolver better | +0.13 [+0.08, +0.17], Transolver better | +0.50 [+0.28, +0.72], Transolver better (n 52) |
| transolver_hybrid | unet_hybrid | -0.05 [-0.09, -0.01], Transolver worse | +0.12 [+0.07, +0.16], Transolver better | +0.42 [+0.25, +0.58], Transolver better (n 52) |
| transolver_hybrid | idw | +1.83 [+1.47, +2.20], Transolver better | +2.87 [+2.12, +3.66], Transolver better | +12.16 [+7.72, +17.18], Transolver better (n 52) |

## ood_fins (139 runs)

| Transolver | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| transolver | fno | +1.47 [+1.27, +1.68], Transolver better | +2.17 [+1.71, +2.63], Transolver better | +10.92 [+8.27, +13.69], Transolver better (n 139) |
| transolver | unet | -0.55 [-0.64, -0.47], Transolver worse | +0.18 [+0.01, +0.36], Transolver better | +4.69 [+3.43, +6.01], Transolver better (n 139) |
| transolver | idw | +2.58 [+2.35, +2.83], Transolver better | +5.30 [+4.68, +5.95], Transolver better | +30.43 [+25.60, +35.41], Transolver better (n 139) |
| transolver_hybrid | fno_hybrid | +0.34 [+0.22, +0.47], Transolver better | +0.36 [+0.06, +0.67], Transolver better | +0.22 [-0.87, +1.34], no clear difference (n 139) |
| transolver_hybrid | unet_hybrid | -0.88 [-0.98, -0.79], Transolver worse | -0.45 [-0.62, -0.29], Transolver worse | +3.41 [+1.97, +4.96], Transolver better (n 139) |
| transolver_hybrid | idw | +2.20 [+1.96, +2.45], Transolver better | +4.50 [+3.86, +5.15], Transolver better | +28.32 [+23.61, +33.24], Transolver better (n 139) |

## ood_drive (51 runs)

| Transolver | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| transolver | fno | +0.28 [+0.21, +0.36], Transolver better | +0.26 [+0.17, +0.36], Transolver better | +1.01 [+0.69, +1.35], Transolver better (n 51) |
| transolver | unet | -0.07 [-0.13, -0.01], Transolver worse | +0.06 [-0.01, +0.12], no clear difference | +0.20 [-0.03, +0.40], no clear difference (n 51) |
| transolver | idw | +3.01 [+2.48, +3.56], Transolver better | +2.92 [+2.19, +3.72], Transolver better | +15.14 [+9.95, +21.21], Transolver better (n 51) |
| transolver_hybrid | fno_hybrid | +0.30 [+0.24, +0.38], Transolver better | +0.18 [+0.10, +0.26], Transolver better | +0.90 [+0.48, +1.34], Transolver better (n 51) |
| transolver_hybrid | unet_hybrid | -0.06 [-0.13, +0.00], no clear difference | +0.12 [+0.06, +0.18], Transolver better | +0.43 [+0.17, +0.73], Transolver better (n 51) |
| transolver_hybrid | idw | +2.94 [+2.41, +3.48], Transolver better | +2.91 [+2.18, +3.72], Transolver better | +15.11 [+9.96, +21.17], Transolver better (n 51) |

## ood_material (250 runs)

| Transolver | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| transolver | fno | +6.79 [+6.49, +7.10], Transolver better | +18.99 [+18.40, +19.57], Transolver better | +46.11 [+43.50, +48.79], Transolver better (n 250) |
| transolver | unet | -0.19 [-0.33, -0.07], Transolver worse | +1.56 [+1.13, +1.99], Transolver better | +11.80 [+10.02, +13.55], Transolver better (n 250) |
| transolver | idw | -0.76 [-0.93, -0.59], Transolver worse | -3.63 [-4.16, -3.10], Transolver worse | -7.41 [-9.31, -5.43], Transolver worse (n 250) |
| transolver_hybrid | fno_hybrid | +1.31 [+1.21, +1.42], Transolver better | +4.68 [+4.19, +5.18], Transolver better | +31.39 [+28.89, +33.92], Transolver better (n 250) |
| transolver_hybrid | unet_hybrid | -1.89 [-2.05, -1.73], Transolver worse | +1.88 [+1.36, +2.39], Transolver better | +29.18 [+26.79, +31.57], Transolver better (n 250) |
| transolver_hybrid | idw | -2.16 [-2.37, -1.94], Transolver worse | -1.20 [-1.59, -0.82], Transolver worse | -6.81 [-9.37, -4.11], Transolver worse (n 250) |

## ood_material_r (250 runs)

| Transolver | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| transolver | fno | +17.79 [+17.03, +18.56], Transolver better | +23.81 [+23.30, +24.31], Transolver better | n/a |
| transolver | unet | -7.47 [-7.86, -7.07], Transolver worse | -22.13 [-22.96, -21.29], Transolver worse | n/a |
| transolver | idw | -13.11 [-13.71, -12.50], Transolver worse | -36.39 [-36.96, -35.79], Transolver worse | n/a |
| transolver_hybrid | fno_hybrid | -4.16 [-4.39, -3.92], Transolver worse | -7.31 [-8.23, -6.37], Transolver worse | n/a |
| transolver_hybrid | unet_hybrid | -8.28 [-8.62, -7.94], Transolver worse | -9.28 [-10.02, -8.51], Transolver worse | n/a |
| transolver_hybrid | idw | -12.22 [-12.75, -11.68], Transolver worse | -12.83 [-13.54, -12.11], Transolver worse | n/a |

## ood_tilt (150 runs)

| Transolver | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| transolver | fno | -0.24 [-0.28, -0.20], Transolver worse | +0.38 [+0.24, +0.52], Transolver better | +0.96 [+0.59, +1.33], Transolver better (n 150) |
| transolver | unet | +0.26 [+0.21, +0.31], Transolver better | +1.85 [+1.72, +1.98], Transolver better | +0.56 [+0.06, +1.07], Transolver better (n 150) |
| transolver | idw | +1.26 [+1.16, +1.38], Transolver better | +4.09 [+3.60, +4.56], Transolver better | +6.87 [+4.67, +9.22], Transolver better (n 150) |
| transolver_hybrid | fno_hybrid | -0.28 [-0.31, -0.24], Transolver worse | -0.52 [-0.59, -0.44], Transolver worse | -0.08 [-0.49, +0.32], no clear difference (n 150) |
| transolver_hybrid | unet_hybrid | +0.18 [+0.14, +0.22], Transolver better | +1.72 [+1.57, +1.87], Transolver better | +4.05 [+3.53, +4.57], Transolver better (n 150) |
| transolver_hybrid | idw | +0.74 [+0.64, +0.84], Transolver better | +2.10 [+1.60, +2.58], Transolver better | +7.11 [+4.94, +9.40], Transolver better (n 150) |
