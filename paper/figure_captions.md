# Figure captions

**Fig. 1.** ThermalStorageBench overview (schematic, not to scale). (a) Tank family: two-dimensional tank of height 1 m and width 0.25 to 1.0 m with side-wall (type A) or lid-and-bottom (type B) slots; charging shown, discharging reverses flow and temperatures. (b) PCM family: cell of height 100 mm and width 20 to 60 mm with 0 to 5 conducting fins on the heated wall, in three orientations. (c) The test splits and what each holds out of training.

**Fig. 2.** Validation. (a) Jet penetration in the Lou et al. tank [18]: two PIV tests, their CFD and our three-dimensional SST run. (b) Outlet temperature in the same test: our run and the experimental curve reconstructed from the published Richardson number with constant β and with β at the mean of inlet and outlet temperature. (c) Liquid fraction for the plain wall, one fin and three fins of Kamkari and Shokouhmand [17] at the dataset settings (the final pressure-solver setting moves these curves by less than 0.005). (d) Liquid fraction for the plain wall of Vogel and Thess [16]: experiment, their two-dimensional model and our run.

**Fig. 3.** Tank. (a) Field error on discharge, training on charging only, for each FNO and U-Net variant: dots are training seeds, bars the mean of three seeds; lines mark the best interpolation on this split (IDW), the multi-node model and ideal stratification. (b) Field error of each test case (seed mean) for the two hybrid canonical models against the bulk Richardson number Ri = gβΔT H/u², pooled over the four splits (821 run-split pairs; a run can appear in more than one test set); filled markers SST runs, open markers laminar runs.

**Fig. 4.** PCM material transfer. Field RMSE of each training seed (dots; filled plain, open hybrid) and the seed mean (bar) for every neural variant, against IDW (dashed). Right: share of test runs whose prediction reaches 90 % melting. Two U-Net seeds on held-out n-octadecane score 8.57 K and overlap.

**Fig. 5.** The preferred model depends on the quantity. (a) PCM, held-out fin counts: field RMSE against t90 error for every model that reaches t90 in all 139 runs (seed means). (b) Tank: vertical-profile error against near-outlet temperature error per split for the multi-node model and the two hybrid canonical surrogates; grey lines connect each split's surrogate to the multi-node model.

**Fig. 6.** Typical predictions: the median-error test run of each family at 25, 50 and 75 % of the run. Top: tank T0554 (discharge, U-Net hybrid canonical, mean of three seeds). Bottom: PCM P0401 (held-out fins, U-Net, mean of three seeds). Columns: CFD, prediction, absolute error in the normalised temperature θ (tank: (T − T_c)/(T_h − T_c); PCM: (T − T_0)/(T_w − T_0)).

