# Design-level 95 % intervals, tank benchmark (descriptive)

Seed means per run (dossier 8.4 basis, every 10th snapshot), averaged per design, designs equally weighted; percentile bootstrap over designs, 10,000 resamples, marginal intervals. Field error in % of ΔT.

## random (131 runs, 110 designs)

| Model | Seeds | Mean, run-weighted | Mean, design-weighted [95 %] |
|---|---|---|---|
| fno | 3 | 4.13 | 4.23 [3.73, 4.78] |
| fno_canon | 3 | 3.92 | 4.00 [3.50, 4.57] |
| fno_hybrid | 3 | 4.17 | 4.26 [3.72, 4.86] |
| fno_hybrid_canon | 3 | 4.02 | 4.10 [3.57, 4.68] |
| unet | 3 | 3.68 | 3.76 [3.26, 4.32] |
| unet_canon | 3 | 3.48 | 3.53 [3.06, 4.06] |
| unet_hybrid | 3 | 3.83 | 3.89 [3.38, 4.46] |
| unet_hybrid_canon | 3 | 3.62 | 3.69 [3.18, 4.27] |
| ideal_stratified | 1 | 15.27 | 15.14 [13.78, 16.50] |
| rbf | 1 | 8.66 | 9.09 [7.90, 10.29] |

| Paired difference (positive: second is better) | Mean, pp [95 %] | Designs where second is better |
|---|---|---|
| FNO minus U-Net (hybrid + canonical) | +0.41 [+0.34, +0.48] | 95 % |
| FNO: plain minus canonical | +0.22 [+0.12, +0.32] | 77 % |
| FNO: plain minus hybrid | -0.03 [-0.14, +0.08] (includes 0) | 35 % |
| FNO: hybrid minus hybrid + canonical | +0.16 [+0.08, +0.25] | 66 % |
| FNO: canonical minus hybrid + canonical | -0.09 [-0.18, -0.00] | 30 % |
| U-Net: plain minus canonical | +0.23 [+0.12, +0.35] | 66 % |
| U-Net: plain minus hybrid | -0.13 [-0.23, -0.03] | 23 % |
| U-Net: hybrid minus hybrid + canonical | +0.20 [+0.12, +0.29] | 76 % |
| U-Net: canonical minus hybrid + canonical | -0.16 [-0.23, -0.09] | 25 % |
| ideal stratification minus FNO hybrid + canonical | +11.05 [+9.90, +12.20] | 100 % |
| RBF interpolation minus FNO hybrid + canonical | +4.99 [+3.84, +6.20] | 96 % |

## ood_geom (224 runs, 189 designs)

| Model | Seeds | Mean, run-weighted | Mean, design-weighted [95 %] |
|---|---|---|---|
| fno | 3 | 4.70 | 4.80 [4.27, 5.36] |
| fno_canon | 3 | 4.48 | 4.56 [4.09, 5.05] |
| fno_hybrid | 3 | 4.76 | 4.85 [4.30, 5.43] |
| fno_hybrid_canon | 3 | 4.44 | 4.52 [4.02, 5.05] |
| unet | 3 | 7.02 | 7.05 [6.31, 7.77] |
| unet_canon | 3 | 5.48 | 5.52 [4.95, 6.10] |
| unet_hybrid | 3 | 5.39 | 5.48 [4.92, 6.05] |
| unet_hybrid_canon | 3 | 6.23 | 6.28 [5.63, 6.92] |
| ideal_stratified | 1 | 16.00 | 16.29 [15.09, 17.47] |
| rbf | 1 | 10.77 | 10.78 [9.71, 11.84] |

| Paired difference (positive: second is better) | Mean, pp [95 %] | Designs where second is better |
|---|---|---|
| FNO minus U-Net (hybrid + canonical) | -1.76 [-2.29, -1.26] | 44 % |
| FNO: plain minus canonical | +0.25 [+0.14, +0.36] | 63 % |
| FNO: plain minus hybrid | -0.05 [-0.14, +0.04] (includes 0) | 40 % |
| FNO: hybrid minus hybrid + canonical | +0.33 [+0.26, +0.41] | 78 % |
| FNO: canonical minus hybrid + canonical | +0.04 [-0.07, +0.13] (includes 0) | 51 % |
| U-Net: plain minus canonical | +1.53 [+1.29, +1.78] | 92 % |
| U-Net: plain minus hybrid | +1.57 [+1.20, +1.96] | 73 % |
| U-Net: hybrid minus hybrid + canonical | -0.80 [-1.08, -0.53] | 39 % |
| U-Net: canonical minus hybrid + canonical | -0.77 [-1.01, -0.54] | 26 % |
| ideal stratification minus FNO hybrid + canonical | +11.76 [+10.82, +12.68] | 99 % |
| RBF interpolation minus FNO hybrid + canonical | +6.25 [+5.24, +7.32] | 96 % |

## ood_mode (363 runs, 303 designs)

| Model | Seeds | Mean, run-weighted | Mean, design-weighted [95 %] |
|---|---|---|---|
| fno | 3 | 64.76 | 64.55 [63.70, 65.40] |
| fno_canon | 3 | 12.36 | 12.64 [10.87, 14.55] |
| fno_hybrid | 3 | 12.98 | 13.27 [12.42, 14.12] |
| fno_hybrid_canon | 3 | 4.48 | 4.59 [4.25, 4.95] |
| unet | 3 | 66.97 | 66.78 [65.94, 67.61] |
| unet_canon | 3 | 9.85 | 10.05 [8.74, 11.47] |
| unet_hybrid | 3 | 13.34 | 13.67 [12.76, 14.59] |
| unet_hybrid_canon | 3 | 4.37 | 4.46 [4.13, 4.81] |
| ideal_stratified | 1 | 16.52 | 16.81 [15.89, 17.73] |
| rbf | 1 | 64.16 | 63.93 [63.13, 64.72] |

| Paired difference (positive: second is better) | Mean, pp [95 %] | Designs where second is better |
|---|---|---|
| FNO minus U-Net (hybrid + canonical) | +0.13 [+0.01, +0.24] | 81 % |
| FNO: plain minus canonical | +51.92 [+49.54, +54.14] | 95 % |
| FNO: plain minus hybrid | +51.28 [+49.71, +52.85] | 100 % |
| FNO: hybrid minus hybrid + canonical | +8.68 [+7.99, +9.38] | 97 % |
| FNO: canonical minus hybrid + canonical | +8.05 [+6.32, +9.92] | 44 % |
| U-Net: plain minus canonical | +56.73 [+54.80, +58.51] | 98 % |
| U-Net: plain minus hybrid | +53.11 [+51.50, +54.73] | 100 % |
| U-Net: hybrid minus hybrid + canonical | +9.20 [+8.45, +9.95] | 96 % |
| U-Net: canonical minus hybrid + canonical | +5.59 [+4.39, +6.91] | 60 % |
| ideal stratification minus FNO hybrid + canonical | +12.22 [+11.45, +12.99] | 99 % |
| RBF interpolation minus FNO hybrid + canonical | +59.34 [+58.33, +60.33] | 100 % |

## ood_flow (103 runs, 103 designs)

| Model | Seeds | Mean, run-weighted | Mean, design-weighted [95 %] |
|---|---|---|---|
| fno | 3 | 10.21 | 10.21 [9.25, 11.28] |
| fno_canon | 3 | 9.57 | 9.57 [8.79, 10.42] |
| fno_hybrid | 3 | 10.38 | 10.38 [9.41, 11.46] |
| fno_hybrid_canon | 3 | 9.83 | 9.83 [8.95, 10.78] |
| unet | 3 | 9.48 | 9.48 [8.49, 10.58] |
| unet_canon | 3 | 9.02 | 9.02 [8.21, 9.90] |
| unet_hybrid | 3 | 9.95 | 9.95 [8.99, 11.03] |
| unet_hybrid_canon | 3 | 9.21 | 9.21 [8.32, 10.21] |
| ideal_stratified | 1 | 22.76 | 22.76 [21.02, 24.62] |
| rbf | 1 | 15.09 | 15.09 [13.69, 16.62] |

| Paired difference (positive: second is better) | Mean, pp [95 %] | Designs where second is better |
|---|---|---|
| FNO minus U-Net (hybrid + canonical) | +0.61 [+0.39, +0.82] | 84 % |
| FNO: plain minus canonical | +0.64 [+0.37, +0.95] | 70 % |
| FNO: plain minus hybrid | -0.16 [-0.34, -0.01] | 39 % |
| FNO: hybrid minus hybrid + canonical | +0.55 [+0.32, +0.83] | 76 % |
| FNO: canonical minus hybrid + canonical | -0.25 [-0.42, -0.10] | 44 % |
| U-Net: plain minus canonical | +0.46 [+0.16, +0.81] | 58 % |
| U-Net: plain minus hybrid | -0.47 [-0.74, -0.22] | 26 % |
| U-Net: hybrid minus hybrid + canonical | +0.74 [+0.48, +1.03] | 73 % |
| U-Net: canonical minus hybrid + canonical | -0.19 [-0.39, -0.00] | 49 % |
| ideal stratification minus FNO hybrid + canonical | +12.94 [+11.80, +14.12] | 99 % |
| RBF interpolation minus FNO hybrid + canonical | +5.26 [+4.05, +6.61] | 86 % |
