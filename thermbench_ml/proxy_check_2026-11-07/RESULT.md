# Proxy metrics against the CFD's real-property quantities (7 November 2026)

**Question** (independent review): the tank benchmark scores energy as mean θ (constant ρcp) and the
outlet temperature as the mean of the cells next to the outlet. How well do these track the real
quantities?

**Method:** CFD labels only, every run of the frozen tank manifest (1,212 runs), every snapshot with t > 0.
- `proxy_check.py` compares the proxies with the values stored in each h5 by `export_case.py`: the real-property
  stored energy `E_J` (ρ(T) and ∫cp dT, water polynomials), the area-averaged outlet-face temperature
  `T_out_K` and `y_mid_m`.
- `outlet_mixcup.py` compares the outlet proxy with the flow-weighted (mixing-cup) outlet temperature,
  h_mix = Σφh / Σφ from the logged outlet mass and enthalpy flows, inverted with the cp polynomial.
  - **Inversion check:** on the 853 runs with a uniform start, the first outflow returns T_init within
    0.075 K (median 0.0006 K).
  - **Snapshots used:** only those with a well-defined net outflow (at least half the run's median), which
    is every snapshot.

## Results

| Quantity | Proxy vs real, run means: median / 90th percentile / max | Reading |
|---|---|---|
| **Energy** (fraction of a full charge) | 0.00023 / 0.00089 / 0.0021 | The label offset is at most 0.2 % of a full charge |
| **ρcp weight** over [Tc, Th], relative to its mean | 0.990 to 1.009 | A model's real-property energy error equals its proxy error within ±1 % |
| **Outlet proxy vs area-averaged outlet face** | 1e-5 / 3e-5 / 1e-4 % of ΔT | Identical: the outlet is zero-gradient, so the face value is the adjacent cell |
| **Outlet proxy vs mixing-cup outlet**, all snapshots | **0.62 / 1.65 / 13.7 % of ΔT** | Small for most runs |
| the same, breakthrough window (10 to 90 % of the outlet change) | **2.3 / 7.2 / 29.7 % of ΔT** | Larger while the thermocline passes the outlet |
| the same, by closure | laminar 0.46 (max 13.7), SST 0.80 (max 4.3) % of ΔT | |
| **y_mid proxy vs `y_mid_m`** | max 4e-14 m | Same definition |
| **Snapshots where the label has no θ = 0.5 crossing** | 2.5 % / 15 % / 51 % (924 of 1,212 runs have at least one) | These are left out of `y_mid_err_m` and counted in `y_mid_missing` |

**Where the outlet difference is large.** Of the runs, 49 have a snapshot above 20 % of ΔT and 14 have a
run mean above 3 %. All of the largest are laminar runs with very high Ri (600 to 5,800). In these, a sharp
thermocline crosses the outlet slot and the outflow leaves through only part of it, sometimes with local
backflow. There the area average and the flow-weighted temperature really differ.

## What this means for the benchmark

1. **The energy metric** measures the real-property stored-energy error within about 1 %. It can be called
   "stored-energy error" with the constant-ρcp definition stated.
2. **The outlet metric** is exactly the **area-averaged outlet temperature**, and should be named that. It
   is not the mixing-cup temperature a system simulation receives. The two differ by a median 0.6 % of ΔT,
   2.3 % around breakthrough, and up to about 30 % in very-high-Ri laminar runs.
   - The benchmark predicts temperature only; a mixing-cup score would need the outlet velocity.
   - The dataset card and paper must state this limit. The h5 files keep the mixing-cup inputs (outlet
     mass and enthalpy flow series) for anyone who wants it.
3. **y_mid** is as defined, and missing crossings are reported, not hidden.
