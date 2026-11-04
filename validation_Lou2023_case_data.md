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

## Plan
- 3D OpenFOAM case, quarter or eighth symmetry: buoyantPimpleFoam, real properties, kOmegaSST + buoyancyTurbSource (compressible path, correct sign), and laminar for comparison. Baffles as solid zones (chtMultiRegionFoam) or as thin adiabatic walls first.
- Compare h_j(t) with PIV, and outlet temperature and charging efficiency with Section 4.
- Run after the 5 mm batch, which uses all cores.
