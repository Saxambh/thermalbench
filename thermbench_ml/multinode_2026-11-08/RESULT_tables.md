# Multi-node 1D baseline vs the field surrogates (design-level, descriptive)

Mean per model (runs weighted equally), and the paired difference other minus multinode averaged per design (positive: multinode better) with a marginal 95 % bootstrap interval over designs.

## random (131 runs, 110 designs)

| Metric | multinode | ideal_stratified | rbf | fno_hybrid_canon | unet_hybrid_canon |
|---|---|---|---|---|---|
| field, % dT | **7.07** | 15.27 (+7.97 [+6.77, +9.19], MN better) | 8.66 (+1.92 [+0.67, +3.23], MN better) | 4.02 (-3.08 [-3.30, -2.86], MN worse) | 3.62 (-3.49 [-3.74, -3.25], MN worse) |
| profile, % dT | **6.21** | 15.64 (+9.22 [+7.85, +10.64], MN better) | 7.27 (+1.43 [+0.07, +2.88], MN better) | 2.53 (-3.68 [-3.93, -3.42], MN worse) | 2.26 (-3.94 [-4.21, -3.66], MN worse) |
| energy, % of charge | **0.55** | 2.59 (+2.00 [+1.59, +2.43], MN better) | 0.77 (+0.28 [+0.05, +0.54], MN better) | 0.50 (-0.04 [-0.10, +0.03], n.s.) | 0.38 (-0.15 [-0.21, -0.09], MN worse) |
| outlet T, K | **0.83** | 1.75 (+0.89 [+0.73, +1.06], MN better) | 2.13 (+1.39 [+0.93, +1.90], MN better) | 0.85 (+0.01 [-0.09, +0.10], n.s.) | 0.67 (-0.16 [-0.24, -0.07], MN worse) |
| midpoint, mm | **12.72** | 22.20 (+8.68 [+6.31, +11.14], MN better) | 19.64 (+7.41 [+1.93, +13.05], MN better) | 6.77 (-6.61 [-9.70, -4.12], MN worse) | 6.03 (-7.33 [-10.81, -4.62], MN worse) |

## ood_geom (224 runs, 189 designs)

| Metric | multinode | ideal_stratified | rbf | fno_hybrid_canon | unet_hybrid_canon |
|---|---|---|---|---|---|
| field, % dT | **7.56** | 16.00 (+8.55 [+7.64, +9.48], MN better) | 10.77 (+3.04 [+1.88, +4.23], MN better) | 4.44 (-3.22 [-3.48, -2.97], MN worse) | 6.23 (-1.46 [-2.04, -0.88], MN worse) |
| profile, % dT | **6.65** | 16.43 (+9.93 [+8.88, +11.02], MN better) | 9.36 (+2.57 [+1.35, +3.83], MN better) | 2.89 (-3.85 [-4.11, -3.59], MN worse) | 3.11 (-3.61 [-3.91, -3.33], MN worse) |
| energy, % of charge | **0.70** | 2.96 (+2.34 [+2.00, +2.71], MN better) | 1.34 (+0.62 [+0.31, +0.95], MN better) | 0.56 (-0.16 [-0.30, -0.04], MN worse) | 0.85 (+0.12 [-0.06, +0.27], n.s.) |
| outlet T, K | **0.95** | 1.87 (+0.90 [+0.77, +1.03], MN better) | 2.72 (+1.72 [+1.30, +2.17], MN better) | 1.01 (+0.03 [-0.06, +0.14], n.s.) | 2.01 (+1.13 [+0.75, +1.54], MN better) |
| midpoint, mm | **16.23** | 25.56 (+9.72 [+7.95, +11.60], MN better) | 26.17 (+9.57 [+4.67, +14.59], MN better) | 8.66 (-8.15 [-11.27, -5.58], MN worse) | 9.57 (-7.17 [-9.85, -4.92], MN worse) |

## ood_mode (363 runs, 303 designs)

| Metric | multinode | ideal_stratified | rbf | fno_hybrid_canon | unet_hybrid_canon |
|---|---|---|---|---|---|
| field, % dT | **7.58** | 16.52 (+9.00 [+8.25, +9.76], MN better) | 64.16 (+56.11 [+55.01, +57.19], MN better) | 4.48 (-3.22 [-3.52, -2.94], MN worse) | 4.37 (-3.35 [-3.72, -2.99], MN worse) |
| profile, % dT | **6.63** | 16.87 (+10.32 [+9.47, +11.18], MN better) | 67.86 (+60.74 [+59.69, +61.75], MN better) | 2.90 (-3.81 [-4.11, -3.51], MN worse) | 3.02 (-3.69 [-4.06, -3.32], MN worse) |
| energy, % of charge | **0.73** | 3.13 (+2.46 [+2.18, +2.76], MN better) | 52.47 (+51.44 [+50.34, +52.47], MN better) | 0.53 (-0.23 [-0.35, -0.13], MN worse) | 0.55 (-0.19 [-0.33, -0.08], MN worse) |
| outlet T, K | **0.98** | 1.88 (+0.92 [+0.82, +1.02], MN better) | 9.56 (+8.64 [+8.03, +9.26], MN better) | 1.17 (+0.17 [+0.02, +0.34], MN better) | 1.29 (+0.31 [+0.12, +0.52], MN better) |
| midpoint, mm | **15.12** | 27.06 (+11.98 [+10.30, +13.75], MN better) | 518.31 (+500.78 [+491.70, +509.56], MN better) | 7.74 (-8.18 [-10.53, -6.09], MN worse) | 8.23 (-7.66 [-10.06, -5.54], MN worse) |

## ood_flow (103 runs, 103 designs)

| Metric | multinode | ideal_stratified | rbf | fno_hybrid_canon | unet_hybrid_canon |
|---|---|---|---|---|---|
| field, % dT | **13.61** | 22.76 (+9.15 [+8.25, +10.04], MN better) | 15.09 (+1.47 [+0.06, +2.98], MN better) | 9.83 (-3.79 [-4.44, -3.21], MN worse) | 9.21 (-4.40 [-5.09, -3.78], MN worse) |
| profile, % dT | **9.60** | 21.12 (+11.52 [+10.45, +12.59], MN better) | 11.06 (+1.46 [-0.11, +3.14], n.s.) | 5.51 (-4.09 [-4.71, -3.52], MN worse) | 5.46 (-4.14 [-4.71, -3.61], MN worse) |
| energy, % of charge | **2.04** | 5.30 (+3.26 [+2.80, +3.71], MN better) | 2.13 (+0.09 [-0.33, +0.48], n.s.) | 1.28 (-0.76 [-1.25, -0.35], MN worse) | 1.45 (-0.59 [-0.95, -0.28], MN worse) |
| outlet T, K | **1.46** | 3.37 (+1.91 [+1.67, +2.14], MN better) | 3.09 (+1.62 [+1.09, +2.22], MN better) | 1.80 (+0.33 [+0.22, +0.44], MN better) | 1.62 (+0.15 [+0.04, +0.27], MN better) |
| midpoint, mm | **47.02** | 53.78 (+6.75 [+3.50, +9.92], MN better) | 44.03 (-2.99 [-8.90, +3.06], n.s.) | 27.89 (-19.14 [-25.31, -13.81], MN worse) | 30.84 (-16.18 [-21.29, -11.49], MN worse) |
