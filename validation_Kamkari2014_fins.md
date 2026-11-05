# PCM fin validation case: Kamkari & Shokouhmand (2014)

**Source.** B. Kamkari, H. Shokouhmand, "Experimental investigation of phase change material melting in rectangular enclosures with horizontal partial fins", Int. J. Heat Mass Transf. 78 (2014) 839–851. doi:10.1016/j.ijheatmasstransfer.2014.07.056.

- Cited 422 times. Read in full via Lund University Libraries, 2026-11-01.
- Properties are from Shokouhmand & Kamkari, Exp. Therm. Fluid Sci. 50 (2013) 201–212.

## Set-up (as stated)

**Enclosure and fins**
- **Enclosure.** Inner size 50 mm wide × 120 mm high × 120 mm deep, transparent.
  - Heated isothermally from one side; all other walls insulated.
- **Fins.** Horizontal partial fins milled from the aluminium heater, so there is no contact resistance.
  - Thickness 4 mm, length 25 mm (half the width).
  - 0, 1 or 3 fins; the 1-fin case has its fin at mid-height.
  - Al conductivity 130 W/m K. The tip is visibly cooler than the base, so the fins are not isothermal.
- **Fin positions in the 3-fin case.** Read from Fig. 1(c) on 2026-11-01.
  - Fin centres are at **y = 29.0, 60.0 and 91.0 mm**, on the thermocouple rows, so they are spaced 31 mm apart, not 30.
  - The 1-fin case has its fin at y = 60.0 mm.
  - The fins span from the hot wall to mid-width, and the thermocouples are on a 15.5 mm vertical pitch.
  - Our runs use `--fin-y 0.029,0.060,0.091`. The first 3-fin run used 30/60/90 mm; it was restarted at 18:23 UTC with the measured positions.

**Conditions**
- PCM starts solid at 25 °C.
- Wall at 55, 60 or 70 °C (Ra_H = 3.6e8 to 8.3e8).
- Each run continued until fully melted.

**Lauric acid (Table 1)**
- Specific heat cp, solid/liquid: 2.18/2.39 kJ/(kg K).
- Melting range 43.5–48.2 °C; the paper treats the interface as the 43.5 °C isotherm.
- Latent heat 187.21 kJ/kg.
- Conductivity k, solid/liquid: 0.16/0.14 W/(m K).
- Density, solid/liquid: 940/885 kg/m³.
- Kinematic viscosity ν = 6.7e-6 m²/s; Pr = 100.7.

**β (not stated in the paper)**
- Backed out from the paper's own Rayleigh numbers, defined as Ra = gβ(Tw − Tm)H³/(να) with liquid properties.
- At 55 °C, Ra = 3.6e8 gives β = 8.2e-4 1/K; at 70 °C, Ra = 8.3e8 also gives β = 8.2e-4 1/K. The two are consistent.
- Value used: **β = 8.2e-4 1/K**.

**Uncertainty (maximum).** Melt fraction 2.3 %, heat transfer rate 4.6 %, Nusselt number 11.3 %.

## Results

### Table 3: melting time ratio, finned over unfinned

| Tw | 0 fins | 1 fin | 3 fins |
|---|---|---|---|
| 70 °C | 1 | 0.82 | 0.64 |
| 60 °C | 1 | 0.83 | 0.62 |
| 55 °C | 1 | 0.81 | 0.63 |

### Fig. 6: melt fraction vs time at Tw = 70 °C

Digitised by eye, ±0.02.

| t (min) | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 | 120 | 140 | 160 | 180 | end |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plain wall | 0.06 | 0.12 | 0.18 | 0.25 | 0.32 | 0.40 | 0.48 | 0.55 | 0.62 | 0.68 | 0.80 | 0.89 | 0.95 | 0.98 | 1.0 at ~195 |
| 1 fin | 0.09 | 0.18 | 0.27 | 0.35 | 0.45 | 0.56 | 0.65 | 0.73 | 0.79 | 0.83 | 0.89 | 0.95 | 1.0 | | 1.0 at ~160 |
| 3 fins | 0.17 | 0.35 | 0.49 | 0.61 | 0.71 | 0.79 | 0.86 | 0.91 | 0.94 | 0.97 | 1.0 | | | | 1.0 at ~125 |

**Total melting times at 70 °C**
- Plain wall: about 195 min.
- 1 fin: about 160 min, a ratio of 0.82.
- 3 fins: about 125 min, a ratio of 0.64.
- These match Table 3.

## Inclination: Kamkari, Shokouhmand & Bruno (2014)

**Source.** B. Kamkari, H. Shokouhmand, F. Bruno, "Experimental investigation of the effect of inclination angle on convection-driven melting of phase change material in a rectangular enclosure", Int. J. Heat Mass Transf. 72 (2014) 186–200. doi:10.1016/j.ijheatmasstransfer.2014.01.014. Read via Lund on 2026-11-01.

**Same rig, unfinned.**
- 50 × 120 mm, 120 mm deep, lauric acid, starting at 25 °C.
- One wall isothermal (55, 60 or 70 °C); the other walls are 25 mm Plexiglas (k = 0.17) with 3 cm of extra insulation.

**Angle convention: the paper's θ is the opposite of ours.**
- Paper: θ = 90° is vertical (heated from the side) and θ = 0° is horizontal (heated from below).
- `make_pcm_case.py --tilt` uses the reverse: 0 is side-heated and 90 is heated from below. So tilt = 90 − θ.

### Table 2: melting time ratios (relative to vertical)

| Tw | θ = 90° (side) | 45° | 0° (from below) |
|---|---|---|---|
| 70 °C | 1 | 0.62 | 0.46 |
| 60 °C | 1 | 0.68 | 0.48 |
| 55 °C | 1 | 0.65 | 0.47 |

### Fig. 12: total melting times (min), read off the figure

| Tw | 90° | 45° | 0° |
|---|---|---|---|
| 70 °C | ~195 | ~120 | ~90 |
| 60 °C | ~330 | ~225 | ~160 |
| 55 °C | ~535 | ~345 | ~255 |

### Fig. 11: melt fraction at 70 °C (±0.02)

| t (min) | 20 | 40 | 60 | 80 | 100 | 120 | end |
|---|---|---|---|---|---|---|---|
| θ = 90° (vertical) | 0.12 | 0.25 | 0.40 | 0.55 | 0.68 | 0.80 | 1.0 at ~195 |
| θ = 45° | 0.17 | 0.35 | 0.52 | 0.68 | 0.83 | 0.98 | 1.0 at ~122 |
| θ = 0° (from below) | 0.20 | 0.42 | 0.63 | 0.85 | | | 1.0 at ~92 |

The vertical curve is the same as the plain wall in the fin paper (Fig. 6), which is consistent.

**Bottom heating.** The melt-front line becomes wavy, a sign of Bénard cells. The melt fraction rises nearly linearly until the end, because the heat rate does not drop as the melt layer thickens. A 2D model can only represent the Bénard cells as rolls.

## Cross-check against Kamkari's own simulations (2026-11-01)

**Source.** Safari, Kamkari, Hooman & Khodadadi, Energy 255 (2022) 124521. doi:10.1016/j.energy.2022.124521. It is a numerical model of the same 50 × 120 mm lauric acid unit, read via Lund.

**Confirmed**
- **Fin positions.** Their Table 1 gives a 27 mm gap between the 4 mm fins of the 3-fin wall. This puts the fin centres at exactly 29, 60 and 91 mm, matching Fig. 1(c).
- **Their model.** 2D Boussinesq, ε = 0.001, dt 0.1 s, about 32k cells (0.1–0.8 mm), heated wall at 70 °C, other walls adiabatic.
- **Their result.** The 3-fin melt fraction agrees with the experiment within 5.4 % (maximum, at 46 min). This sets the bar a good 2D model reaches.

**Differences from our model**
- **Melting range vs melting point.** They model the 43.5–48.2 °C range, with a linear liquid fraction, and use Tm = 45.85 °C (the midpoint) for Nu. OpenFOAM's solidificationMeltingSource is isothermal.
  - We run Tm = 43.5 °C (the paper's interface temperature and its Ra) as the main case.
  - The sensitivity run `kamkari_70_n0_tm4585` (laptop, started 2026-11-01 ~18:18 UTC) uses Tm = 45.85 °C.
- **Conjugate fins.** They solve heat conduction in the Al fins; ours are isothermal.
- **Mushy constant.** They use A_mush = 5e6; we use 1e6. Vogel & Thess found the result insensitive to this for melting-point materials.
- **Initial temperature.** They use 24 °C; the experiment paper states 25 °C. We use 25 °C.

**β.** Not stated in any of the three Kamkari papers checked: the 2014 fins paper, the 2014 inclination paper (Table 1) and the 2022 Energy paper. Our 8.2e-4 1/K, backed out from the stated Ra at two wall temperatures, stays.

**Heater warm-up (inclination paper, Fig. 3).** The heat exchanger surface needs about 4 min to reach 70 °C (2.5 min at 60 °C, 2 min at 55 °C). We step the wall instantly. Expect our early melt fractions to run slightly ahead, worth about 1–2 % of the melting time.

**Heat loss.** The total heat loss through the insulated walls is under 2.7 % of the absorbed energy (inclination paper, section 2.2), so adiabatic walls are fair.

## Interim comparison (2026-11-01 20:40 UTC) and the melting-range model

**Interim liquid fractions at 70 °C (ours vs experiment)**
- No fins: 0.38 vs 0.25 at 40 min. With the heater warm-up modelled it is unchanged; with Tm = 45.85 °C it is 0.24 vs 0.18 at 30 min.
- 1 fin: 0.44 vs 0.27 at 30 min.
- 3 fins: 0.70 vs 0.49 at 30 min.
- 45°: 0.18 vs 0.17 at 20 min.
- Heated from below: 0.30 vs 0.20 at 20 min.
- Our isothermal model therefore melts about 40–60 % too fast.
- The heater warm-up is NOT the cause (it changes the result by about 0.01).

**Vogel (n-octadecane, a true melting point).** It matches the B-2D curve with a mean deviation of 0.000. So the solver set-up is right, and the gap is specific to lauric acid and Kamkari's rig.

**Melting-range model** (`--melt-range Ts,Tl`, built 2026-11-01). Two coded fvOptions:
- the Voller-Swaminathan source update over [Ts, Tl];
- the Darcy sink and Boussinesq buoyancy relative to the range midpoint.

Verification on a small case:
- A ±0.01 K range reproduces OpenFOAM's isothermal source to 4 decimals in liquid fraction (0.1402 vs 0.1403 at 300 s).
- The energy balance closes within 0.03 % of a full charge.

On that small case the real 43.5–48.2 range melts slightly *faster* than isothermal at 45.85 (0.1446 vs 0.1403 at 300 s): melting starts earlier, and the box is too small for convection damping to show. So the range alone may not close the gap.

**Test runs on the lab, started 20:48 UTC, with auto-stop at 99.5 % melted**
- `kamkari_70_n0_range`
- `kamkari_70_n0_range_cu5e6`: mushy constant 5e6, as in Safari/Kamkari 2022
- `kamkari_70_n1_range`

## Status 2026-11-02 04:58 UTC

**Liquid fraction at 70 °C, ours vs experiment (Fig. 6)**

| Run | 30 min | 50 min | 80 min | t(f = 0.99) |
|---|---|---|---|---|
| experiment, plain wall | 0.18 | 0.32 | 0.55 | ~185 |
| isothermal 43.5 °C | 0.28 | 0.46 | 0.69 | 155 |
| isothermal 45.85 °C | 0.24 | 0.40 | 0.62 | 175 |
| range 43.5–48.2 | 0.23 | 0.39 | 0.59 | running |
| range + Cu 5e6 | 0.22 | 0.37 | 0.58 | running |
| experiment, 1 fin | 0.27 | 0.45 | 0.73 | ~155 |
| isothermal, 1 fin | 0.44 | 0.70 | 0.85 | 128 |
| range, 1 fin | 0.38 | 0.60 | running | running |

**What this shows**
- **Plain wall:** the melting-range model halves the gap; at 80 min the error drops from +0.14 to +0.04. A mushy constant of 5e6 helps a little more (+0.03).
- **1 fin:** the range model helps only partly (+0.15 at 50 min, against +0.25 isothermal). The remaining fin excess points to the isothermal-fin assumption (decision 3).
- **Fin ratio:** the isothermal model's ratio of 1-fin to plain melting times, 128/155 = 0.83, still matches Kamkari's 0.82.
- **Heater warm-up:** the ramp runs track the step runs within 0.01. Confirmed: not the cause.

**Other runs**
- **Tilts:** 45° runs +0.05 mean, and heated-from-below +0.08 mean (isothermal model).
- **Vogel:** V1–V3 all within ±0.01.

## Conducting fins (built 2026-11-02)

**Option.** `make_pcm_case.py --fin-model conduct --k-fin 130` (requires `--melt-range`).
- Fin cells stay in the mesh as cellZone `fin`, held solid with liquid fraction 0.
- An implicit extra diffusion term raises their conductivity. Face values are harmonic means, so the fin/PCM faces see the correct series resistance.
- The fin roots get their own patch `finroot`. The exporter scales its wallHeatFlux by k_fin/k_pcm and adds the fins' sensible heat to the energy balance.
- Liquid fraction and auto-stop average over cellZone `pcm`. That result is named `volAverage(pcm,melting:alpha1)`.
- Fin heat capacity uses the PCM's ρcp. Aluminium is about 15 % higher, but the fins are a small share of the volume.

**Verification.** Small case: 20 × 40 mm, 1 fin of 10 × 2 mm, 70 °C, range 43.5–48.2. Liquid fraction at 300 s:

| Mesh | Isothermal fin | Conducting, k = 1e5 | Gap | Al (130) | k = k_pcm |
|---|---|---|---|---|---|
| 1 mm | 0.2457 | 0.2567 | +4.5 % | 0.2481 | 0.1521 |
| 0.5 mm | 0.2472 | 0.2509 | +1.5 % | | |
| 0.25 mm | 0.2388 | 0.2429 | +1.7 % | | |

- **Large-k limit.** A very conductive fin reproduces the isothermal fin within 1.5–1.7 % on 0.5 mm and finer meshes, and identically at early times (0.0870 vs 0.0869 at 60 s).
- **Remaining gap.** It is smaller than the mesh effect on the isothermal model itself (3.4 % between 0.5 and 0.25 mm). The likely cause is that the no-slip surface sits at the fin cell centres instead of the fin faces.
- **Ordering.** Al is slightly below the large-k limit, and k = k_pcm is far below, as expected.

**Runs on pc3, started 06:57–07:01 UTC** (0.5 mm, range + Cu 5e6):
- `kamkari_70_n1_cond`
- `kamkari_70_n3_cond`
- `kamkari_70_n1_range_cu5e6`: isothermal fin, the same-settings reference

**Mesh test on the lab, started 06:48 UTC** (1 mm):
- `kamkari_70_n0_range_cu5e6_h1`
- `kamkari_70_n1_range_h1`

## Final comparison and frozen settings (2026-11-02, 17:50 UTC)

**Frozen settings** (`pcm_design.py`, used for the pilot and the full PCM batch):
- lauric acid melting range 43.5–48.2 °C;
- mushy constant Cu = 5e6 (as in Safari/Kamkari 2022);
- conducting aluminium fins, k = 130 W/m K;
- 0.5 mm mesh.

### Liquid fraction at 70 °C: final model vs experiment (Fig. 6, ±0.02)

| t (min) | 10 | 20 | 30 | 40 | 50 | 60 | 80 | 100 | 120 | 140 | 160 | full melt (0.995) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| experiment, plain wall | 0.06 | 0.12 | 0.18 | 0.25 | 0.32 | 0.40 | 0.55 | 0.68 | 0.80 | 0.89 | 0.95 | ~195 |
| **model, plain wall** | 0.09 | 0.15 | 0.22 | 0.30 | 0.37 | 0.44 | 0.58 | 0.69 | 0.79 | 0.87 | 0.93 | **195** |
| experiment, 1 fin | 0.09 | 0.18 | 0.27 | 0.35 | 0.45 | 0.56 | 0.73 | 0.83 | 0.89 | 0.95 | 1.0 | ~160 |
| **model, 1 fin (conducting)** | 0.14 | 0.25 | 0.36 | 0.47 | 0.57 | 0.67 | 0.77 | 0.85 | 0.91 | 0.96 | | running* |
| experiment, 3 fins | 0.17 | 0.35 | 0.49 | 0.61 | 0.71 | 0.79 | 0.91 | 0.97 | 1.0 | | | ~125 |
| **model, 3 fins (conducting)** | 0.24 | 0.43 | 0.60 | 0.71 | 0.81 | 0.86 | 0.93 | 0.97 | | | | **115** |

\* The 1-fin isothermal-fin run with the same settings (`kamkari_70_n1_range_cu5e6`) tracks the conducting run within 0.01 and fully melted at **161 min**.

**Deviation (model − experiment)**

| Case | Mean absolute | Largest | Full melting time | Ratio to plain wall (model / experiment) |
|---|---|---|---|---|
| Plain wall | 0.03 | +0.05 at 50 min | 195 vs ~195 min (0 %) | |
| 1 fin | 0.07 | +0.12 at 50 min | 161 vs ~160 min (+1 %) | 0.83 / 0.82 |
| 3 fins | 0.07 | +0.11 at 30 min | 115 vs ~125 min (−8 %) | 0.59 / 0.64 |

**What it shows**
- **Plain wall:** within ±0.05 at every time and the same full melting time. Validated.
- **Finned walls:** the model melts about 0.1 too fast during the first hour, then converges.
  - After 80 min the deviation is within ±0.04.
  - The 1-fin full melting time matches the experiment.
  - The fin benefit (ratio to the plain wall) matches for 1 fin and is 0.05 too strong for 3 fins.
- **For comparison:** Kamkari's own 2D model (Safari et al. 2022) reached 5.4 % maximum deviation for 3 fins. Ours is larger in the first hour (+0.11 absolute at 30 min).

**What it is NOT (ruled out by the runs)**
- **Fin model:** conducting (k = 130) and isothermal fins agree within 0.01 for one fin. Aluminium is conductive enough that the fin is close to wall temperature.
- **Heater warm-up:** the ramp runs track the step runs within 0.01.
- **Melting model:** the range model with Cu = 5e6 is what fixed the plain wall (from +0.14 to +0.03 at 80 min); it applies equally to finned cases.

**Likely causes of the early fin excess (open, not tuned)**
- **Mesh:** coarsening from 0.5 to 1 mm speeds melting by 7–11 % at mid-times and shortens the full melt by about 7 % (plain 182 vs 195 min, 1 fin 147 vs 156 min). The small-case check showed 3.4 % between 0.5 and 0.25 mm. Part of the early fin excess may therefore be discretisation, since the flow around fin tips is under-resolved.
- **No-slip position:** in the conducting-fin model the no-slip surface sits at the fin cell centres, not the fin faces (see the verification above), which slightly enlarges the effective fin.
- **3D effects:** the experiment has front and back walls 120 mm apart. They damp convection near the fins, which a 2D model cannot represent.

**Decision:** settings frozen as above. We report the fin deviation openly rather than tuning parameters to remove it. A 0.25 mm run of the 3-fin case would quantify how much is mesh. It is optional, at roughly 8 times the cost of a 0.5 mm run.

## Re-run with the final solver set-up (2026-11-05, interim at 05:30 UTC)

**Why.** All 500 PCM cases were rerun with the pressure fix (p_rghFinal relTol 0 + maxIter 200, option A, 2026-11-04). These re-runs check that the validation still holds.

**Runs.** On pc4 (`scripts/pcm_validate_fix.sh`): 0.5 mm, melting range 43.5 to 48.2 °C, conducting Al fins (k = 130), wall 70 °C. Compared with `scripts/valfix_compare.py`.

**One setting differs from the dataset: mushy constant 1e6, not the frozen 5e6.** The script's base arguments set `--Cu 1e6`. The 2026-11-02 runs showed this changes the plain wall by about 0.01 in melt fraction (Cu 1e6 melts slightly faster: 0.23 vs 0.22 at 30 min, 0.59 vs 0.58 at 80 min).

**Liquid fraction, re-run vs experiment (Fig. 6 and inclination Fig. 11)**

| Case | Mean abs. dev. | Mean dev. | Largest | Full melt | Before the fix (Cu 5e6) |
|---|---|---|---|---|---|
| plain wall | 0.036 | +0.033 | +0.067 at 50 min | running (0.954 at 165 min) | 0.03 mean abs., 195 min |
| 1 fin | 0.090 | +0.090 | +0.148 at 50 min | running (0.896 at 111 min) | 0.07, 161 min |
| 3 fins | 0.080 | +0.080 | +0.125 at 30 min | **112 vs ~125 min (−10 %)** | 0.07, 115 min |
| 45° | 0.040 | −0.040 | −0.082 at 120 min | running (0.963 at 134 min) | |
| heated from below | 0.036 | +0.024 | +0.064 at 20 min | running (0.938 at 91 min) | |

Plain wall, point by point (min: experiment / before the fix / re-run):
- 10: 0.06 / 0.09 / 0.087
- 30: 0.18 / 0.22 / 0.233
- 50: 0.32 / 0.37 / 0.387
- 80: 0.55 / 0.58 / 0.592
- 120: 0.80 / 0.79 / 0.806
- 160: 0.95 / 0.93 / 0.942

**What it shows**
- **The fix itself barely moves the curves.** The re-runs sit 0.01 to 0.03 above the pre-fix runs at every point. That is the size and direction expected from Cu 1e6 vs 5e6, and the fix test (pc4 `~/pcm_fixtest/V1_tight`) showed the fix alone moves the melt curve by less than 0.005.
- **Validation conclusions are unchanged.**
  - Plain wall: within about ±0.07.
  - Finned walls: still about 0.1 too fast in the first hour, then converging. 3 fins melts fully at 112 min against about 125.
  - The tilted cases are within ±0.08.
  - The early fin excess was already documented above and is not caused by the fix.
- **No temperature overshoot in any re-run:** max T − T_wall is −0.000 K (n0, n1, n3), −0.018 K (45°) and −0.55 K (from below), over all snapshots.

**Open (optional):** one plain-wall run with exactly the dataset's settings (Cu 5e6 plus the fix) would remove the Cu caveat. It costs about 5 h on one core.

**Final numbers:** fill in the full-melt times when n0, n1, 45° and from-below finish (all above 0.89 at 05:30 UTC). Rerun `python3 scripts/valfix_compare.py` after copying postProcessing from pc4 `~/of_runs/pcm_valfix`.

## Our model and expected deviations (original plan, 2026-11-01; superseded by the section above)

**Material set in `make_pcm_case.py`**
- Constant properties: mean density (912.5) and mean cp (2285).
- Liquid conductivity 0.14 and μ = ν·ρ_l = 5.93e-3 Pa s.
- Tmelt = 43.5 °C, L = 187.21 kJ/kg, β = 8.2e-4.

**Expected deviations**
- **Isothermal fins.** We expect a slight over-prediction of the fin benefit. The estimated fin efficiency is about 0.93 for a 4 mm Al fin at h ≈ 100 W/m² K, so the error should be a few per cent in heat input.
- **Point melting at 43.5 °C instead of a 4.7 K range.** The sharp-front model may melt slightly differently.
- **Large subcooling (18.5 K) with constant cp.** The sensible heat of the solid is represented by the mean cp.
