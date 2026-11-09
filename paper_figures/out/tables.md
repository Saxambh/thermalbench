**Table 1.** The two families of ThermalStorageBench.

| | Stratified water tank (sensible) | PCM melting cell (latent) |
|---|---|---|
| Geometry | 2D rectangular tank, height 1 m, width 0.25 to 1.0 m; side-wall slots (A) or lid and bottom slots (B), slot height 20 to 80 mm, port offset 0 to 0.2 H | 2D enclosure, height 100 mm, width 20 to 60 mm, heated wall with 0 to 5 conducting aluminium fins (length 0.2 to 0.8 W, thickness 1 to 4 mm) |
| Operation | Charging (849 runs) or discharging (363); uniform (853) or pre-stratified (359) start; inlet velocity 0.005 to 0.2 m/s, ΔT 5 to 50 K | Melting from a heated wall; side heating (350), tilted 45° (75), heated from below (75); wall superheat 8 to 30 K, subcooling 0.5 to 22.3 K |
| Material | Water, temperature-dependent (real) properties | n-octadecane (250) and lauric acid (250), constant properties, enthalpy-porosity melting |
| Flow regime | Laminar (Re < 1,500), k-ω SST (Re > 3,000), both between: 432 laminar-only, 396 SST-only, 192 with both | Laminar natural convection, Ra_H 1.5 × 10⁸ to 9.0 × 10⁸, Ste 0.07 to 0.37 |
| Solver and mesh | OpenFOAM v2606 buoyantPimpleFoam, uniform 5 mm mesh | OpenFOAM v2606 buoyantPimpleFoam with enthalpy-porosity source, uniform 0.5 mm mesh |
| Runs (design points) | 1,212 (1,020) | 500 (500) |
| Output per run | 121 snapshots of T, p_rgh, u (and k, ω, ν_t for SST); stored energy, exergy, MIX, thermocline midpoint and thickness, outlet temperature | 88 to 204 snapshots of T and liquid fraction; stored energy, Nusselt number, heat input, liquid fraction |
| Quality control | 1,211 OK, 1 WARN; 5 planned runs excluded by pre-set rules | 498 OK, 2 WARN (field QC); 39 solver-WARN cases kept under a pre-registered rule; 34 reruns |
| Size, frozen manifest | 54.4 GB, md5 0e8b6d8d… | 10.3 GB, md5 19397b78… |

**Table 2.** Tank family: temperature-field RMSE on the test runs, in % of the run's temperature difference ΔT. Neural models: mean ± SD over three training seeds. Lowest value per split in bold. Test runs: random 131, unseen width 224, discharge 363, faster inflow 103.

| Model | Random | Unseen width | Discharge | Faster inflow |
|---|---|---|---|---|
| *Baselines* | | | | |
| Initial field (no change) | 67.32 | 64.84 | 63.59 | 62.04 |
| 1D ideal stratification | 15.27 | 16.00 | 16.52 | 22.76 |
| Multi-node 1D (calibrated) | 7.07 | 7.56 | 7.58 | 13.61 |
| k-nearest neighbours | 9.50 | 11.87 | 63.73 | 15.45 |
| Inverse-distance weighting | 9.32 | 11.92 | 63.50 | 15.24 |
| Radial basis functions | 8.66 | 10.77 | 64.16 | 15.09 |
| *Neural operators* | | | | |
| FNO | 4.13 ± 0.17 | 4.70 ± 0.05 | 64.76 ± 0.47 | 10.21 ± 0.10 |
| FNO, canonical | 3.92 ± 0.05 | 4.48 ± 0.06 | 12.36 ± 0.69 | 9.57 ± 0.10 |
| FNO, hybrid | 4.17 ± 0.06 | 4.76 ± 0.05 | 12.98 ± 0.11 | 10.38 ± 0.05 |
| FNO, hybrid + canonical | 4.02 ± 0.09 | **4.44 ± 0.03** | 4.48 ± 0.07 | 9.83 ± 0.11 |
| U-Net | 3.68 ± 0.07 | 7.02 ± 0.43 | 66.97 ± 1.21 | 9.48 ± 0.06 |
| U-Net, canonical | **3.48 ± 0.05** | 5.48 ± 0.29 | 9.85 ± 0.46 | **9.02 ± 0.17** |
| U-Net, hybrid | 3.83 ± 0.15 | 5.39 ± 0.36 | 13.34 ± 0.70 | 9.95 ± 0.17 |
| U-Net, hybrid + canonical | 3.62 ± 0.10 | 6.23 ± 0.25 | **4.37 ± 0.28** | 9.21 ± 0.13 |

**Table 3.** PCM family. (a) Temperature-field RMSE (K) on the test runs. (b) Relative melt-time (t90) error in %, over the runs whose prediction reaches a liquid fraction of 0.9 within the input-only horizon (3 t_ref); the share of runs that reach it is given when it is below 100 %, and the error is not reported when fewer than 10 % of runs reach it. Neural models: mean ± SD over three training seeds (field RMSE). Bold: lowest field RMSE, and lowest t90 error among models reaching t90 in at least 90 % of runs. Test runs: random 52, held-out fins 139, stronger heating 51, unseen tilt 150, held-out lauric acid 250, held-out n-octadecane 250.

| Model | Random | Held-out fins | Stronger heating | Unseen tilt | Held-out lauric acid | Held-out n-octadecane |
|---|---|---|---|---|---|---|
| **(a) Field RMSE, K** | | | | | | |
| *Baselines* | | | | | | |
| Initial field (no change) | 21.80 | 22.58 | 27.45 | 18.88 | 22.46 | 20.64 |
| Stefan (conduction) | 14.00 | 15.63 | 20.28 | 12.22 | 14.33 | 13.75 |
| Front model | 10.21 | 10.50 | 14.04 | 7.71 | 9.71 | 10.44 |
| k-nearest neighbours | 2.54 | 4.96 | 4.25 | 7.71 | 5.53 | 3.60 |
| Inverse-distance weighting | 2.55 | 4.90 | 4.13 | 7.67 | **5.35** | **3.55** |
| Radial basis functions | 1.98 | 7.30 | 4.02 | 12.84 | 56.96 | 21.95 |
| *Neural operators* | | | | | | |
| FNO | 0.82 ± 0.00 | 3.79 ± 0.13 | 1.40 ± 0.02 | **6.17 ± 0.58** | 12.90 ± 8.72 | 34.45 ± 9.59 |
| FNO, hybrid | 0.86 ± 0.01 | 3.05 ± 0.19 | 1.49 ± 0.01 | 6.66 ± 0.34 | 8.82 ± 3.02 | 11.61 ± 3.36 |
| U-Net | **0.59 ± 0.01** | **1.76 ± 0.07** | **1.05 ± 0.06** | 6.67 ± 0.13 | 5.92 ± 0.61 | 9.19 ± 1.08 |
| U-Net, hybrid | 0.68 ± 0.03 | 1.82 ± 0.01 | 1.12 ± 0.02 | 7.12 ± 0.11 | 5.61 ± 1.38 | 7.48 ± 1.42 |
| Transolver | 0.66 ± 0.02 | 2.31 ± 0.06 | 1.11 ± 0.01 | 6.41 ± 0.33 | 6.11 ± 0.29 | 16.66 ± 3.48 |
| Transolver, hybrid | 0.72 ± 0.01 | 2.70 ± 0.13 | 1.19 ± 0.01 | 6.94 ± 0.10 | 7.51 ± 0.22 | 15.77 ± 3.33 |
| **(b) t90 error, %** | | | | | | |
| *Baselines* | | | | | | |
| Initial field (no change) | none | none | none | none | none | none |
| Stefan (conduction) | none | none | none | none | (0.4 % reach) | (0.8 % reach) |
| Front model | 18.3 | 26.2 | 15.8 | 34.7 | 26.3 | **17.6** |
| k-nearest neighbours | 11.9 | 35.9 | 16.0 | 20.9 | 17.1 | 27.8 |
| Inverse-distance weighting | 12.9 | 36.0 | 16.2 | 20.7 | **16.9** | 27.9 |
| Radial basis functions | 9.1 | 55.5 (94 % reach) | 8.4 | 29.5 (92 % reach) | 57.1 (71 % reach) | 32.9 (89 % reach) |
| *Neural operators* | | | | | | |
| FNO | 1.5 | 16.5 | 2.0 | 14.8 | 70.4 | 100.0 (33 % reach) |
| FNO, hybrid | 1.2 | 7.9 | 2.0 | **13.5** | 55.1 | 32.0 (79 % reach) |
| U-Net | 1.1 | 10.2 | 1.2 | 14.4 | 36.1 | 108.5 (78 % reach) |
| U-Net, hybrid | 1.1 | 11.1 | 1.5 | 17.6 | 52.9 | 30.4 |
| Transolver | 0.8 | **5.6** | **1.0** | 13.8 | 24.3 | (2.0 % reach) |
| Transolver, hybrid | **0.7** | 7.7 | 1.1 | 13.6 | 23.7 | (6.7 % reach) |
