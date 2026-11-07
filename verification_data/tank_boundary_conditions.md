# Tank boundary conditions and turbulence inputs (review item 2.8, 7 November 2026)

Taken from the case generator `scripts/make_tank_case.py` and checked against the `case.json` of every run in
the frozen manifest (1,212 runs).

## Patches

| Field | Inlet slot | Outlet slot | Walls |
|---|---|---|---|
| U | fixedValue, uniform normal velocity u_in | pressureInletOutletVelocity | noSlip |
| T | fixedValue T_in | **zeroGradient**: any local backflow carries the adjacent tank temperature, not T_in or T0 | zeroGradient (**adiabatic**) |
| p_rgh | fixedFluxPressure | **fixedMean** (mean p_rgh fixed; the profile follows the stratification across the slot) | fixedFluxPressure |
| k (SST) | fixedValue k_in = 1.5 (I u_in)² | inletOutlet (k_in on backflow) | kqRWallFunction |
| omega (SST) | fixedValue ω_in = √k_in / (0.09^¼ L), L = 0.07 × slot width | inletOutlet (ω_in on backflow) | omegaWallFunction |
| nut (SST) | calculated | calculated | nutkWallFunction |
| alphat (SST) | calculated | calculated | compressible::alphatJayatillekeWallFunction, Prt 0.85 |

- **Why fixedMean on the outlet:** a uniform fixedValue p_rgh drove an exchange flow through the outlet once the
  thermocline reached it. That is the P14 failure found during development.
- **Backflow:** with fixedMean p_rgh and pressureInletOutletVelocity, local inflow through part of the outlet
  slot is possible. It enters at the adjacent cell temperature (zeroGradient T), with k_in and ω_in for SST.
  The outlet mass and enthalpy flow series in each h5 (`series/outlet_mdot`, `series/outlet_Hdot`) record the
  net flow.

## Turbulence and buoyancy inputs, across the frozen dataset

| Closure | Runs | Inlet turbulence intensity I | Buoyancy production of k and ω |
|---|---|---|---|
| kOmegaSST | 588 (411 inlet type A, 177 type B) | 0.05 | OpenFOAM `buoyancyTurbSource` (fvOptions) |
| laminar | 624 (433 type A, 191 type B) | not applicable | not applicable |

**SST wall treatment:** standard wall functions (kqR, omega, nutk, Jayatilleke). The y+ distribution of all
588 SST runs is in the dataset card: 60 % of wall cell-snapshots below 5, 38.5 % in the buffer layer, and
1.6 % above 30.

## Thermal conditions

- **Walls:** adiabatic (no heat loss); the tank wall is not modelled as a solid.
- **Properties:** real water properties, polynomial in T (`RHO_C`, `CP_C`, `MU_C`, `KAPPA_C` in
  `make_tank_case.py`).
- **Initial state:** uniform (853 runs) or a tanh thermocline (359 runs, interface height y_i, thickness
  δ = 0.02 m).
