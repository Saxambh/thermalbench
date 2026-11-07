# Tank mesh verification: result

**Claim.** On four designs spanning laminar and SST flow, the 5 mm production mesh reproduces the 2.5 mm
solution within the pre-registered agreement limits for the integral quantities. These are stored energy (one
borderline case), the horizontally averaged temperature profile, outlet temperature and thermocline height.
The full temperature field differs by 0.3 to 2.8 % of ΔT between the two meshes. Two designs are borderline
on this quantity and none exceeds the clear-disagreement limit over the whole run. We report this as the
field-level mesh uncertainty of the tank labels. We do not claim mesh convergence, and no GCI is given
because the three grid levels do not converge monotonically.

## Method

- **Designs.** Four dataset designs:
  - T0408, laminar (Re 2014, Ri 31);
  - T0221, laminar (Re 678, Ri 386);
  - T0551, laminar (Re 1259, Ri 55);
  - T0243, k-omega SST (Re 18,626, Ri 5.8).
- **Runs.** Each design was rerun at production settings on the 5 mm mesh (identical to the dataset run in
  all four cases, difference 0.00) and on a 2.5 mm mesh. For three designs a 10 mm mesh was also run, as a
  diagnostic only.
- **Comparison.** The 2.5 mm run was compared with the 5 mm rerun at matched physical times over all
  snapshots of the run.
- **Limits.** The agreement and disagreement limits were committed before any mesh result was compared
  (verification_criteria_2026-11-06.md, commit 1a63b11):

  | Quantity | Agreement | Clear disagreement |
  |---|---|---|
  | Field RMSE, % of ΔT | ≤ 1.5 % | > 3 % |
  | Horizontal-profile RMSE, % of ΔT | ≤ 1.5 % | > 3 % |
  | Time-averaged field difference, % of ΔT | ≤ 1.0 % | > 2 % |
  | Stored energy | ≤ 0.5 % | > 2 % |
  | Outlet temperature, % of ΔT | ≤ 2 % | > 5 % |
  | Thermocline midpoint | ≤ 10 mm | > 25 mm |

  Results between the two columns are borderline. A quantity that agrees over the whole run but exceeds its
  limit in any time window (before, around or after the outlet event) is classed as borderline (event
  window).
- **Perturbation runs.** To separate mesh effects from the sensitivity of the unsteady flow, each design was
  also rerun on 5 mm with the inlet velocity × 1.0001. That difference is reported as physical sensitivity,
  not as a noise floor.

## Results, 2.5 mm vs 5 mm

| Design | Field | Profile | Time-averaged field | Energy | Outlet | Midpoint | Inlet × 1.0001 (field) |
|---|---|---|---|---|---|---|---|
| T0408 lam | 0.34 % | pass | pass | 0.17 % | 1.43 % (2.03 % in event window) | 0.5 mm | ~0 % |
| T0221 lam | 0.60 % | pass | 0.28 % | 0.42 % | 0.77 % | 0.8 mm | 0.39 % |
| T0243 SST | **1.70 %** | 0.92 % | 0.67 % | **0.96 %** | 1.30 % | pass | ≤ 0.11 % |
| T0551 lam | **2.76 %** | 0.81 % | 0.29 % | 0.23 % | 1.32 % | 1.1 mm | 1.85 % |

Verdicts:
- T0408: agreement, with the outlet borderline (event window).
- T0221: agreement on all quantities.
- T0243: field and energy borderline, all else agreement.
- T0551: field borderline (3.03 % in the early window), all else agreement.

## Interpretation

- **T0243.** The perturbation difference is small (≤ 0.11 %), so the 1.70 % is a genuine mesh effect:
  - it lies on the thermocline interface and grows with time (by quarter of the run 0.41, 1.14, 1.99 and
    2.49 %; 2.72 % at the worst snapshot);
  - the finer mesh stores slightly less energy (−0.64 % at the end of the run).
- **T0551.** The perturbation alone moves the field by 1.85 %. Most of the 2.76 % mesh difference is
  therefore the flow's own sensitivity, and only a small part is attributable to the mesh.
- **10 mm grid.** It is clearly coarser than 5 mm, for example a 2.76 % outlet difference in the event window
  for T0221 and 3.07 % field RMSE for T0551. The three levels do not converge monotonically, so under the
  pre-registered rule no observed order or GCI is reported.
- **Scale.** The largest mesh difference in the field (2.8 % of ΔT) is below the best machine-learning field
  error on the random split (3.4 %), and the integral quantities differ by much less than the corresponding
  ML errors.

## Consequence

- The tank dataset is kept at 5 mm.
- The paper will report the field-level mesh uncertainty (up to about 2.8 % of ΔT, concentrated at the
  thermocline interface) with the per-design table above.
- The paper will not describe the mesh as converged.
- Time-step and outer-iteration sensitivity were tested separately and are reported on their own.
