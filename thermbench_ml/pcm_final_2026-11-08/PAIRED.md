# PCM: paired differences, neural vs baselines (descriptive)

Baseline minus neural (positive: the neural model is better), mean over test runs with a 95 % percentile bootstrap interval over runs. Neural scores are the per-run mean of 3 seeds. 'Best baseline' is chosen on the test set by mean field RMSE. t90: runs where both models cross in every seed.

## random (52 runs; best baseline: rbf)

| Neural | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| fno | idw | +1.73 [+1.40, +2.08], neural better | +2.69 [+1.95, +3.47], neural better | +11.35 [+6.94, +16.35], neural better (n 52) |
| fno | rbf | +1.17 [+0.91, +1.43], neural better | +1.44 [+1.01, +1.90], neural better | +7.52 [+4.24, +11.52], neural better (n 52) |
| unet | idw | +1.96 [+1.60, +2.33], neural better | +2.82 [+2.09, +3.60], neural better | +11.82 [+7.40, +16.79], neural better (n 52) |
| unet | rbf | +1.39 [+1.12, +1.68], neural better | +1.57 [+1.13, +2.04], neural better | +8.00 [+4.67, +12.03], neural better (n 52) |
| fno_hybrid | idw | +1.69 [+1.35, +2.04], neural better | +2.74 [+2.00, +3.53], neural better | +11.66 [+7.24, +16.68], neural better (n 52) |
| fno_hybrid | rbf | +1.12 [+0.87, +1.39], neural better | +1.49 [+1.04, +1.96], neural better | +7.83 [+4.53, +11.83], neural better (n 52) |
| unet_hybrid | idw | +1.87 [+1.51, +2.26], neural better | +2.75 [+2.00, +3.54], neural better | +11.74 [+7.28, +16.75], neural better (n 52) |
| unet_hybrid | rbf | +1.31 [+1.02, +1.60], neural better | +1.49 [+1.04, +1.97], neural better | +7.91 [+4.61, +11.90], neural better (n 52) |

## ood_fins (139 runs; best baseline: idw)

| Neural | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| fno | idw | +1.11 [+0.86, +1.38], neural better | +3.14 [+2.47, +3.81], neural better | +19.51 [+15.44, +23.79], neural better (n 139) |
| unet | idw | +3.14 [+2.88, +3.40], neural better | +5.12 [+4.56, +5.69], neural better | +25.74 [+21.54, +30.10], neural better (n 139) |
| fno_hybrid | idw | +1.85 [+1.64, +2.08], neural better | +4.14 [+3.57, +4.74], neural better | +28.10 [+23.76, +32.63], neural better (n 139) |
| unet_hybrid | idw | +3.08 [+2.83, +3.34], neural better | +4.95 [+4.38, +5.54], neural better | +24.91 [+20.85, +29.14], neural better (n 139) |

## ood_drive (51 runs; best baseline: rbf)

| Neural | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| fno | idw | +2.73 [+2.23, +3.24], neural better | +2.66 [+1.94, +3.46], neural better | +14.13 [+9.03, +20.18], neural better (n 51) |
| fno | rbf | +2.62 [+2.18, +3.08], neural better | +1.87 [+1.42, +2.36], neural better | +6.35 [+3.91, +9.04], neural better (n 51) |
| unet | idw | +3.08 [+2.52, +3.64], neural better | +2.86 [+2.12, +3.68], neural better | +14.94 [+9.77, +21.02], neural better (n 51) |
| unet | rbf | +2.97 [+2.47, +3.48], neural better | +2.06 [+1.60, +2.56], neural better | +7.16 [+4.72, +9.88], neural better (n 51) |
| fno_hybrid | idw | +2.64 [+2.13, +3.16], neural better | +2.73 [+2.02, +3.54], neural better | +14.21 [+9.21, +20.11], neural better (n 51) |
| fno_hybrid | rbf | +2.53 [+2.08, +2.99], neural better | +1.94 [+1.50, +2.42], neural better | +6.44 [+4.07, +9.06], neural better (n 51) |
| unet_hybrid | idw | +3.00 [+2.44, +3.57], neural better | +2.79 [+2.05, +3.61], neural better | +14.68 [+9.55, +20.70], neural better (n 51) |
| unet_hybrid | rbf | +2.89 [+2.39, +3.41], neural better | +2.00 [+1.54, +2.50], neural better | +6.90 [+4.52, +9.59], neural better (n 51) |

## ood_tilt (150 runs; best baseline: idw)

| Neural | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| fno | idw | +1.51 [+1.39, +1.63], neural better | +3.71 [+3.20, +4.21], neural better | +5.91 [+3.75, +8.18], neural better (n 150) |
| unet | idw | +1.00 [+0.90, +1.11], neural better | +2.24 [+1.76, +2.71], neural better | +6.31 [+4.16, +8.61], neural better (n 150) |
| fno_hybrid | idw | +1.01 [+0.91, +1.12], neural better | +2.61 [+2.09, +3.12], neural better | +7.19 [+4.98, +9.52], neural better (n 150) |
| unet_hybrid | idw | +0.55 [+0.45, +0.66], neural better | +0.38 [-0.07, +0.82], no clear difference | +3.06 [+0.79, +5.43], neural better (n 150) |

## ood_material (250 runs; best baseline: idw)

| Neural | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| fno | idw | -7.55 [-7.94, -7.17], baseline better | -22.62 [-23.39, -21.82], baseline better | -53.52 [-55.95, -51.06], baseline better (n 250) |
| unet | idw | -0.57 [-0.81, -0.33], baseline better | -5.18 [-5.94, -4.44], baseline better | -19.21 [-21.67, -16.75], baseline better (n 250) |
| fno_hybrid | idw | -3.47 [-3.74, -3.19], baseline better | -5.88 [-6.37, -5.39], baseline better | -38.20 [-40.10, -36.32], baseline better (n 250) |
| unet_hybrid | idw | -0.26 [-0.43, -0.10], baseline better | -3.08 [-3.52, -2.66], baseline better | -36.00 [-39.26, -32.60], baseline better (n 250) |

## ood_material_r (250 runs; best baseline: idw)

| Neural | vs | field RMSE, K | energy error, pp | t90 error, pp |
|---|---|---|---|---|
| fno | idw | -30.90 [-32.20, -29.61], baseline better | -60.20 [-60.85, -59.54], baseline better | n/a |
| unet | idw | -5.65 [-5.96, -5.33], baseline better | -14.26 [-14.91, -13.60], baseline better | -51.30 [-62.24, -40.31], baseline better (n 84) |
| fno_hybrid | idw | -8.06 [-8.43, -7.69], baseline better | -5.52 [-5.94, -5.11], baseline better | +5.53 [+0.46, +10.79], neural better (n 100) |
| unet_hybrid | idw | -3.94 [-4.21, -3.67], baseline better | -3.55 [-3.97, -3.13], baseline better | -2.52 [-6.08, +1.05], no clear difference (n 250) |
