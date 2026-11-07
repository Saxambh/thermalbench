# PCM mesh study: time-step controls, t99 sampling and the corrected GCI (review item 3.3, 8 November 2026)

Script `pcm_t99_dense.py`, data `pcm_t99_dense.json`.

## Time-step controls (identical at every level)

`make_pcm_case.py`: adjustTimeStep yes, **maxCo 1.0**, **maxDeltaT 0.5 s**; fields are written every 42 s
(G131), 40 s (G301) or 15 s (P0021, G021); stop at liquid fraction 0.995.

The solver time step is the spacing of the function-object series (written every 10 steps) divided by 10:

| Run | Mesh | Median solver Δt |
|---|---|---|
| G131 | 1.0 / 0.5 / 0.25 mm | 0.233 / 0.133 / 0.073 s |
| G301 | 1.0 / 0.5 / 0.25 mm | 0.126 / 0.069 / 0.040 s |
| P0021 | 0.5 / 0.25 mm | 0.047 / 0.024 s |

The time step stays far below the 0.5 s cap and is **Courant-limited**: it roughly halves with each mesh
halving. So the mesh study is a combined space-and-time refinement. The apparent order and the GCI include
the temporal error and must be described that way, not as spatial discretisation error alone.

## t99 sampling: snapshots vs dense series

The reported t99 was the first snapshot with liquid fraction ≥ 0.99, quantised by the write interval of up
to 42 s. The h5 files also hold the liquid fraction every 10 solver steps (`series/liquid_fraction`); t99
from its interpolated crossing is:

| Run | Snapshot t99 (s) | Dense t99 (s) |
|---|---|---|
| G131 1.0 / 0.5 / 0.25 mm | 4200 / 4536 / 4746 | 4198.6 / 4515.0 / 4704.3 |
| G301 1.0 / 0.5 / 0.25 mm | 3600 / 3920 / 4200 | 3596.0 / 3910.8 / 4194.3 |
| P0021 0.5 / 0.25 mm | 1530 / 1545 | 1523.6 / 1534.3 |

## Corrected GCI (r = 2, Fs = 1.25)

| | Order p | Extrapolated t99 | GCI, fine | GCI, medium (= production 0.5 mm) |
|---|---|---|---|---|
| G131, snapshots (as reported) | 0.678 | 5096 s | 9.22 % | 15.43 % |
| **G131, dense** | **0.741** | **4987 s** | **7.50 %** | **13.06 %** |
| G301, dense | 0.152 | (6750 s) | not meaningful | not meaningful |

**Reading**
- **G131:** sampling at the write interval inflated the reported uncertainty. The corrected value for t99
  on the production mesh is 13.06 %, for one scalar in the width-adjusted G131 case, from a combined
  space-time refinement. The 0.5 mm result is 9.5 % early relative to the extrapolation, and 4.0 % early
  relative to the observed 0.25 mm result. 13.06 % replaces 15.43 % wherever the current estimate is cited.
- **G301:** its observed order of about 0.15 means the three levels are not shown to be in the asymptotic
  range, so no GCI is quoted (pre-registered order criterion). The low order makes the extrapolation
  unreliable; it does not by itself explain why the order is low.
  - Two-grid difference on the same basis as the old 6.67 % (divided by the fine result): the 0.5 mm run
    melts **6.76 %** earlier than the 0.25 mm run (dense).
  - Equivalently, the fine run is 7.25 % later, divided by the medium result.
  - The old 6.67 % used snapshot t99.
- **P0021:** the fine mesh melts 0.70 % later (dense), not 0.98 %.
- **Three different "melt" times** must be kept apart in the paper:
  - **t99:** liquid fraction 0.99, used in the mesh study;
  - **the stop criterion:** 0.995, the end of every run, used as "full melt" in the validation tables;
  - **the experiment's "full melt":** visual.
