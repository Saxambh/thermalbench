# Flow-weighted vs near-outlet temperature error (K), tank test runs

Mean over runs; in brackets the design-level paired difference other minus multinode (positive: multinode better) with its 95 % bootstrap interval.

## random (131 runs)

| model | near-outlet | flow-weighted | near, breakthrough | flow-weighted, breakthrough |
|---|---|---|---|---|
| multinode | 0.835 | 0.934 | 2.005 | 2.498 |
| ideal_stratified | 1.748 (+0.889 [+0.724, +1.057]) | 1.693 (+0.720 [+0.565, +0.878]) | 8.212 (+6.096 [+5.187, +7.067]) | 7.891 (+5.293 [+4.471, +6.164]) |
| rbf | 2.124 (+1.386 [+0.928, +1.905]) | 2.278 (+1.436 [+0.960, +1.974]) | 3.408 (+1.466 [+0.660, +2.419]) | 3.682 (+1.247 [+0.384, +2.275]) |
| fno_hybrid_canon_mean | 0.850 (+0.007 [-0.090, +0.105]) | 0.891 (-0.050 [-0.148, +0.050]) | 2.974 (+0.879 [+0.274, +1.532]) | 2.902 (+0.371 [-0.205, +1.003]) |
| unet_hybrid_canon_mean | 0.674 (-0.158 [-0.245, -0.072]) | 0.690 (-0.242 [-0.329, -0.158]) | 2.530 (+0.489 [-0.032, +1.075]) | 2.517 (+0.024 [-0.523, +0.627]) |

Snapshots with no outflow in the outlet cells: 0 of 1572; breakthrough snapshots: 280.

## ood_geom (224 runs)

| model | near-outlet | flow-weighted | near, breakthrough | flow-weighted, breakthrough |
|---|---|---|---|---|
| multinode | 0.954 | 1.017 | 2.232 | 2.482 |
| ideal_stratified | 1.870 (+0.901 [+0.772, +1.034]) | 1.823 (+0.780 [+0.658, +0.905]) | 8.099 (+5.772 [+5.089, +6.500]) | 8.051 (+5.449 [+4.770, +6.174]) |
| rbf | 2.685 (+1.682 [+1.273, +2.135]) | 2.857 (+1.796 [+1.364, +2.270]) | 4.410 (+2.089 [+1.461, +2.786]) | 4.685 (+2.144 [+1.477, +2.863]) |
| fno_hybrid_canon_mean | 1.007 (+0.032 [-0.058, +0.138]) | 1.053 (+0.015 [-0.079, +0.128]) | 2.998 (+0.768 [+0.340, +1.232]) | 3.094 (+0.633 [+0.217, +1.088]) |
| unet_hybrid_canon_mean | 2.010 (+1.128 [+0.761, +1.541]) | 2.057 (+1.108 [+0.740, +1.521]) | 3.594 (+1.401 [+0.991, +1.840]) | 3.760 (+1.295 [+0.883, +1.728]) |

Snapshots with no outflow in the outlet cells: 0 of 2688; breakthrough snapshots: 540.

## ood_mode (363 runs)

| model | near-outlet | flow-weighted | near, breakthrough | flow-weighted, breakthrough |
|---|---|---|---|---|
| multinode | 0.984 | 1.066 | 2.380 | 2.797 |
| ideal_stratified | 1.885 (+0.917 [+0.814, +1.021]) | 1.833 (+0.768 [+0.665, +0.874]) | 7.750 (+5.430 [+4.926, +5.940]) | 7.638 (+4.894 [+4.402, +5.395]) |
| rbf | 9.558 (+8.644 [+8.027, +9.276]) | 9.658 (+8.677 [+8.058, +9.316]) | 14.756 (+12.152 [+11.342, +12.987]) | 15.277 (+12.296 [+11.493, +13.127]) |
| fno_hybrid_canon_mean | 1.167 (+0.173 [+0.027, +0.335]) | 1.227 (+0.148 [-0.004, +0.319]) | 2.660 (+0.281 [+0.037, +0.542]) | 2.892 (+0.125 [-0.148, +0.403]) |
| unet_hybrid_canon_mean | 1.287 (+0.308 [+0.120, +0.515]) | 1.377 (+0.313 [+0.114, +0.531]) | 2.769 (+0.413 [+0.159, +0.681]) | 3.133 (+0.383 [+0.109, +0.670]) |

Snapshots with no outflow in the outlet cells: 0 of 4356; breakthrough snapshots: 880.

## ood_flow (103 runs)

| model | near-outlet | flow-weighted | near, breakthrough | flow-weighted, breakthrough |
|---|---|---|---|---|
| multinode | 1.464 | 1.652 | 2.922 | 3.617 |
| ideal_stratified | 3.370 (+1.906 [+1.675, +2.138]) | 3.144 (+1.492 [+1.262, +1.721]) | 9.093 (+6.171 [+5.506, +6.836]) | 8.821 (+5.204 [+4.529, +5.872]) |
| rbf | 3.027 (+1.563 [+1.052, +2.153]) | 3.288 (+1.636 [+1.065, +2.291]) | 4.436 (+1.514 [+0.866, +2.211]) | 4.825 (+1.208 [+0.414, +2.056]) |
| fno_hybrid_canon_mean | 1.797 (+0.332 [+0.221, +0.443]) | 1.845 (+0.192 [+0.084, +0.299]) | 3.646 (+0.725 [+0.465, +0.990]) | 3.988 (+0.371 [+0.090, +0.645]) |
| unet_hybrid_canon_mean | 1.617 (+0.153 [+0.038, +0.273]) | 1.687 (+0.035 [-0.085, +0.158]) | 3.455 (+0.533 [+0.283, +0.793]) | 3.851 (+0.234 [-0.100, +0.559]) |

Snapshots with no outflow in the outlet cells: 0 of 1236; breakthrough snapshots: 352.
