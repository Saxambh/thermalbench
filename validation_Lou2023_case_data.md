# 3D validation case: Lou et al. (2023)
Source: Lou, Baudin, Roux, Fan, Luo, J. Energy Storage 71 (2023) 108017, doi:10.1016/j.est.2023.108017. Read through Saxam's Chrome on 1 Nov 2026 (ScienceDirect full text).

## Geometry (Section 2.2, Fig. 3, Fig. 6a)
- Cuboid tank, inner square cross-section W = 194 mm, inner height H = 390 mm. Polycarbonate walls 6 mm thick.
- Ports: one central port in the top cover (inlet) and one in the bottom cover (outlet), inner diameter d = 10 mm.
- Two perforated baffles, each 194 x 194 x 6 mm (polycarbonate), divide the tank as follows:

  | zone | height |
  |---|---|
  | upper manifold (top cover to upper baffle) | 33 mm |
  | upper baffle | 6 mm |
  | storage zone | 312 mm |
  | bottom baffle | 6 mm |
  | bottom manifold | 33 mm |
  | **total** | **390 mm** |

  Check: 33 + 6 + 312 + 6 + 33 = 390.
- **Uniform baffle (the validation case): 37 circular orifices, all of RADIUS 8.05 mm.**
  - The nomenclature uses r for the orifice radius. Porosity is stated as 0.20, and 37 x pi x 8.05^2 / 194^2 = 0.200 exactly. A diameter of 8.05 would give 0.05, so the value must be a radius.
  - Both baffles are uniform in the validation case. Only the upper baffle was later optimised.
- Orifice centres, read from Fig. 6a (one-eighth wedge, origin at the tank axis, x along a symmetry plane through the middle of a side, diagonal at 45 degrees). Coordinates in mm; the rest of the 37 follow from the square's 8-fold symmetry. Weights: centre 1, on-plane holes 4 each, interior holes 8 each, so 1 + 2x4 + 3x4 + 2x8 = 37.

  | hole | position | x | y |
  |---|---|---|---|
  | centre | origin | 0 | 0 |
  | on x-plane | 34.3 from centre | 34.3 | 0 |
  | on x-plane | 34.3 + 38.5 | 72.8 | 0 |
  | on diagonal | 34.3 along diagonal | 24.25 | 24.25 |
  | on diagonal | 68.6 along diagonal | 48.5 | 48.5 |
  | on diagonal | 102.9 along diagonal | 72.76 | 72.76 |
  | interior | 34.3 at 45 deg from (34.3, 0) | 58.55 | 24.25 |
  | interior | a further 34.3 at 45 deg | 82.8 | 48.5 |

  Placements were checked against pixel positions in the figure.
- Optimised baffle (Fig. 6b, for a later comparison only): centre r = 1.31, the others 8.06 to 8.28 mm.

## Operating case for validation (Section 2.7, Fig. 4, Fig. 5)
- Charging only. Tank initially at Tc = 293.15 K, at rest.
- Hot water Th = 333.15 K enters the top port at Qin = 1 L/min, v_in = 0.2122 m/s, uniform (plug) profile in their CFD.
- Outlet: bottom port, zero static pressure.
- Walls adiabatic. Baffles conduct (polycarbonate: rho 1200, cp 1200, lambda 0.2).
- Their CFD: Fluent 19.1, realizable k-epsilon with full buoyancy, 1/8 domain, about 1.1 M cells, dt = 1 ms.

## Measurement: jet penetration length h_j(t) (Fig. 5)
h_j is the distance from the top inlet port to the point on the centreline where the vertical velocity changes sign (from PIV, averaged over 50 images, 12.5 s).

Values below were read from the figure (accuracy about +-3 mm). They are checked against the text: the CFD-PIV gap is 33.9 mm (31%) at 50 s and 24.5 mm (12.1%) at 650 s. Our readings give 34 and 25 mm.

| t (s) | PIV test 1 (mm) | PIV test 2 (mm) | their CFD (mm) |
|---|---|---|---|
| 50 | 99 | 117 | 74 |
| 100 | 110 | 119 | 85 |
| 150 | 123 | 135 | 92 |
| 200 | 129 | 138 | 100 |
| 250 | 134 | 142 | 108 |
| 300 | 143 | 152 | 116 |
| 350 | 160 | 160 | 125 |
| 400 | 167 | 165 | 133 |
| 450 | 175 | 169 | 142 |
| 500 | 179 | 175 | 150 |
| 550 | 181 | 181 | 158 |
| 600 | 186 | 192 | 168 |
| 650 | 198 | 204 | 176 |
| 700 | (none) | 211 | 185 |

Origin, resolved from Fig. 3: the x-y axes start at the LOWER face of the upper baffle, with y pointing up. So y = 0 is 33 + 6 = 39 mm below the top cover.
- h_j is measured from the inlet port (top cover), so h_j = 39 mm + |y|.
- The text's "y = -160 mm at 700 s" corresponds to h_j of about 199 mm, which matches the PIV points (about 198 to 211). So the figure and text are consistent.
- Compare our CFD as h_j = 39 mm + (depth below the baffle face where the centreline v_y changes sign).

## Other data in the paper (not yet extracted)
- Section 4: charging tests at Qin 0.3 to 1.5 L/min and Th 323 to 343 K. Reports capacity ratio, charging efficiency, Ri_bulk, and inlet/outlet PT100 temperatures for uniform vs optimised baffles. Useful as a second, global validation target.
- Appendix A: PIV vs CFD velocity profiles at several heights and times.
- Water properties (Table 2) are polynomials in T (293 to 333 K). Ours (IAPWS fits) are used instead.

## Result: 3D OpenFOAM run vs PIV (2026-11-05)

**Run.** `~/of_runs/lou3d/sst` on the laptop:
- quarter-symmetry 3D, 230,156 cells, kOmegaSST, buoyantPimpleFoam, max Co 2;
- baffle holes r = 8.00 mm (upper) and 8.12 mm (lower), open-area ratio 1.006 and 1.010 of the target;
- simulated to 750 s.

h_j from `scripts/lou3d_hj.py`: centreline v_y averaged over ±6.25 s, as in Lou's PIV.

| t (s) | 50 | 100 | 150 | 200 | 250 | 300 | 350 | 400 | 450 | 500 | 550 | 600 | 650 | 700 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PIV mean (mm) | 108 | 114.5 | 129 | 133.5 | 138 | 147.5 | 160 | 166 | 172 | 177 | 181 | 189 | 201 | 211 |
| Lou CFD (Fluent) | 74 | 85 | 92 | 100 | 108 | 116 | 125 | 133 | 142 | 150 | 158 | 168 | 176 | 185 |
| **ours (3D SST)** | 105.8 | 113.7 | 120.5 | 128.5 | 138.1 | 146.3 | 156.1 | 165.5 | 173.8 | 183.7 | 193.1 | 202.0 | 211.5 | 222.5 |

**Agreement with the PIV mean over 14 times**
- **Ours:** bias +2.4 mm, RMS 7.2 mm. Up to 450 s it is within ±9 mm (mostly within ±4); after that it runs 7 to 12 mm deeper.
- **Lou's own Fluent CFD:** bias −29.7 mm.
- The two PIV tests differ by up to 18 mm, so our deviation is within the measurement spread.

**What it shows.** The same solver and turbulence choices as the tank dataset (buoyantPimpleFoam, kOmegaSST with the corrected buoyancy source, real water properties) reproduce a measured buoyant jet in a real tank in 3D. They do so better than the original authors' CFD.

## Mesh sensitivity: run `sst_finelow` (lab, 2026-11-06)

**Run.** `~/of_runs/lou3d/sst_finelow` on the lab: the same case with the lower baffle region refined like the upper one (`make_lou3d.py --fine-lower`), 326,932 cells instead of 230,156, 8 cores. It ran to the shortened end of 300 s (finished 2026-11-06 00:48 UTC, exit 0; fields to t = 296.65 s, not yet reconstructed). Running on to 750 s would take about 37 h more at ~12 s simulated per hour.

**h_j, 50 to 300 s** (`scripts/lou3d_hj.py ~/of_runs/lou3d/sst ~/lou3d_fine`):

| t (s) | 50 | 100 | 150 | 200 | 250 | 300 |
|---|---|---|---|---|---|---|
| PIV mean (mm) | 108 | 114.5 | 129 | 133.5 | 138 | 147.5 |
| coarse `sst` | 105.8 | 113.7 | 120.5 | 128.5 | 138.1 | 146.3 |
| fine `sst_finelow` | 105.8 | 113.7 | 120.4 | 128.4 | 138.0 | 146.2 |

- Fine vs PIV mean over these 6 times: bias −3.0 mm, RMS 4.2 mm; coarse vs fine: at most 0.1 mm apart.
- Tank mean temperature: identical to 0.001 K up to 300 s. Outlet temperature: 20.000 °C in both (the hot front has not reached the lower baffle yet; in the coarse run the outlet starts to rise only after ~550 s: 20.3 °C at 600 s, 26.2 at 700 s, 34.2 at 750 s).

**What it shows, and what it does not.** Refining the lower baffle changes nothing in the first 300 s, so the jet result (h_j) does not depend on the lower-region mesh. It is not a refinement of the jet region itself (the upper manifold and baffle are refined ×2 in both runs), and the lower refinement can only matter once the front reaches the lower baffle (after ~550 s), which this run did not reach. For the paper: report h_j vs PIV from the coarse run over 14 times, and this run as a check that the lower-region mesh does not affect it up to 300 s; state the limits.

**Still to do.** Outlet-temperature / charging comparison with Lou Section 4 (data not yet extracted from the paper), using the coarse run to 750 s.

## Plan
- 3D OpenFOAM case, quarter or eighth symmetry: buoyantPimpleFoam, real properties, kOmegaSST + buoyancyTurbSource (compressible path, correct sign), and laminar for comparison. Baffles as solid zones (chtMultiRegionFoam) or as thin adiabatic walls first.
- Compare h_j(t) with PIV, and outlet temperature and charging efficiency with Section 4.
- Run after the 5 mm batch, which uses all cores.
