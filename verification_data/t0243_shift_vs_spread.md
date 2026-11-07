# T0243_sst mesh difference: displacement or broadening? (7 November 2026, review item 2.2)

**Method** (`t0243_shift_vs_spread.py`, data `t0243_shift_vs_spread.json`):
- Compare the row-averaged θ profiles of the 2.5 mm run (block-averaged onto the 5 mm cells, interpolated
  in time) and the production run, at all 120 snapshots.
- For each snapshot, find the vertical shift that best aligns them. The part of the difference a shift
  removes is displacement; the rest is shape.

**Result**

| | Whole run | First half | Second half |
|---|---|---|---|
| Share of the profile difference (mean square) removed by a pure shift | **79 %** | 27 % | **83 %** |
| Median best shift (fine minus production) | 0.15 mm | −0.45 mm | **+2.85 mm** |
| Median 10–90 % thickness change (fine minus production) | −0.7 mm | +0.05 mm | −2.3 mm |

- **Overall profile difference:** median 0.55 %, max 1.57 % of ΔT. After the best shift: median 0.37 %,
  max 0.79 %.
- **Production thermocline thickness:** 46 to 80 mm (median 59 mm). So the thickness change in the second
  half is about 4 %.

**Reading.** The T0243 mesh difference is mainly a displacement: the fine-mesh thermocline sits about 3 mm
higher (lags) in the second half. The thermocline is also slightly sharper on the fine mesh, about 4 %
thinner, which is the expected sign of less numerical diffusion, but this is the smaller part. In the first
half the differences are small and mostly shape. This is one design; it does not establish the split for
other cases.
