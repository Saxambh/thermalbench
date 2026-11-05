# PCM family validation case: Vogel & Thess (2019)

**Source.** J. Vogel, A. Thess, "Validation of a numerical model with a benchmark experiment for melting governed by natural convection in latent thermal energy storage", Appl. Therm. Eng. 148 (2019) 147–159. doi:10.1016/j.applthermaleng.2018.11.032. The open manuscript is at elib.dlr.de/123839.

**Experiment.** Vogel & Bauer, Int. J. Heat Mass Transf. 127 (2018) 1264–1276. doi:10.1016/j.ijheatmasstransfer.2018.06.084.

## Set-up (as stated in the paper)

**Geometry and conditions**
- **Domain.** n-octadecane in a box heated from both vertical sides, so half width W = 25 mm with a symmetry plane at mid-width.
  - Height H = 100 mm, the average of liquid 105 mm and solid 95 mm. Depth 50 mm.
  - Aspect ratio A = 4.
- **Temperatures.** Initial T0 = 27 °C, which is 1 K of subcooling. Tmelt = 28 °C. Heated walls Tw = 38 °C, so ΔT = 10 K.
- **Other boundaries.** The bottom is an adiabatic wall. In the B-2D model the top is a symmetry (slip) surface.
- **Dimensionless groups.** Ra_H = 2.0e8, Ste = 0.092, Pr = 52, Fo at full melt = 0.11. The flow is laminar.

**Properties (Table 3, from Galione et al. 2015)**
- Density: solid 863 kg/m³; liquid 778.466 kg/m³ at Tm.
- Specific heat cp: solid 1942 J/(kg K); liquid 1394.560 + 2.7186 T [K].
- Conductivity k: solid 0.3362 W/(m K); liquid 0.2067352 − 1.841779e-4 T.
- Viscosity: μ = 0.02966723 − 8.533286e-5 T [K]. Checked against the published version in ScienceDirect on 2026-11-01: the exponents are 1.2463e-4 (density), 1.841779e-4 (k) and 8.533286e-5 (μ). The cp and k formulas take T in K, which reproduces the stated liquid values at Tm.
- **B-2D property choice, confirmed from Table 5 of the published version.**
  - Mean density and mean cp of solid and liquid.
  - **k = liquid value at Tm (0.151215).**
  - μ at Tm + ΔT/2.
  - The validation runs V1–V3 (started 17:01) used k at 33 °C (0.15035, 0.6 % lower). That difference is well inside the ±0.02 digitising accuracy. The generator is now fixed for all later runs.
- **Small conjugate parts in their 2D domain.** It includes 1 mm of steel heater and 2 mm of acrylic bottom wall. Ours does not; this is a minor effect.
- β = 8.9e-4 1/K. Latent heat L = 242.454 kJ/kg.

**B-2D model, which is what make_pcm_case.py reproduces**
- Constant properties: mean density and cp; liquid k and μ at the mean liquid temperature.
- Boussinesq buoyancy relative to Tm.
- Enthalpy-porosity "melting point" model with mushy constant 1e6 and ε = 1e-3.
- Mesh 0.25 mm (about 40k cells for the half domain), dt 0.1 s, second-order upwind, PISO.

**Paper's findings**
- B-2D and the detailed V-2D model differ by 1.4 % (mean) in liquid fraction.
- Their B-3D model with measured boundary conditions agrees with the experiment within 4 % (mean) in liquid fraction, 10 % at most, at the start.

## Digitised curves (read off by eye from the figures, ±0.02 in f_l, ±2 W in Q)

### Fig. 7: B-2D liquid fraction and heat flow

The heat flow is per half domain per metre of depth (Fluent 2D convention). The energy check works: ∫Q dt ≈ 0.5 MJ, the same as melting 0.025 × 0.1 × 1 m³.

| t (h) | 0.25 | 0.5 | 1.0 | 1.5 | 2.0 | 2.5 | 3.0 | 3.5 |
|---|---|---|---|---|---|---|---|---|
| f_l, B-2D | 0.16 | 0.27 | 0.47 | 0.66 | 0.80 | 0.90 | 0.965 | 1.00 |
| Q, B-2D (W/m) | 59 | 63 | 60 | 50 | 37 | 26 | 15 | 7 |

### Fig. 11: experiment (with uncertainty bars about ±0.04) and B-3D

| t (h) | 0.167 | 0.333 | 0.5 | 0.667 | 0.833 | 1.0 | 1.167 | 1.333 | 1.5 | 1.667 | 1.833 | 2.0 | 2.167 | 2.333 | 2.5 | 2.667 | 2.833 | 3.0 | 3.167 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f_l, experiment | 0.03 | 0.155 | 0.25 | 0.34 | 0.425 | 0.505 | 0.58 | 0.65 | 0.71 | 0.765 | 0.81 | 0.85 | 0.885 | 0.91 | 0.94 | 0.96 | 0.975 | 0.985 | 0.99 |

B-3D simulation: f_l = 0.33, 0.56, 0.74, 0.87, 0.95 and 0.99 at t = 0.5, 1, 1.5, 2, 2.5 and 3 h.

### Notes for the comparison
- B-2D reaches full melt at about 3.5 h. The experiment and B-3D reach it at about 3.1 h, because the real cell gains heat through its other walls and the top.
- The ideal-boundary 2D model is therefore checked code-to-code against B-2D (Fig. 7). The experiment is a secondary check, where a 2D model with ideal walls is expected to melt somewhat slower.

## Re-run with the final solver set-up (2026-11-05)

**Why.** All 500 PCM cases were rerun with the pressure fix (p_rghFinal relTol 0 + maxIter 200, option A, 2026-11-04). This re-run checks that the validation still holds with exactly that set-up.

**Run.** `vogel_fix` on pc4 (`scripts/pcm_validate_fix.sh`, make_pcm_case md5 917e2754): 0.5 mm, dt 0.1 s, melting range 27.99 to 28.01 °C, mushy constant 1e6, end 3.5 h. Compared with `scripts/valfix_compare.py`.

| t (h) | 0.25 | 0.5 | 1.0 | 1.5 | 2.0 | 2.5 | 3.0 |
|---|---|---|---|---|---|---|---|
| B-2D (Fig. 7) | 0.16 | 0.27 | 0.47 | 0.66 | 0.80 | 0.90 | 0.965 |
| **re-run** | 0.154 | 0.259 | 0.475 | 0.665 | 0.814 | 0.915 | 0.974 |

- **Against B-2D:** mean absolute deviation 0.009, mean +0.004, largest +0.015 at 2.5 h. Inside the ±0.02 digitising accuracy. Full melt (0.995) at 201 min, against about 210 min for B-2D.
- **Against the experiment (Fig. 11):** mean absolute deviation 0.030, mean −0.016. The largest gap, +0.09, is at the first point (10 min), where the experiment's heater is still warming up. After that the re-run runs slightly slow, as expected for ideal 2D walls (see the notes above).
- **No temperature overshoot:** across all 42 snapshots the highest temperature is at the wall temperature (max T − T_wall = +0.000 K). Before the fix, production cases reached +16 to 19 K.

**Verdict:** the fix leaves the Vogel validation unchanged, and the overshoot is gone.
