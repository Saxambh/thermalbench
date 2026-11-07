# Speed statement for the tank surrogate (review item 4.10, 8 November 2026)

**What is compared:** the wall-clock latency to produce one full run (all 121 snapshots) with the trained
model against the CFD solver's wall-clock time for that run. This is a latency ratio on different hardware,
not an equal-cost or energy comparison. Training cost is not amortised into it.
- **Recorded training times** (`train_min` in `results_merged`, on mixed GPUs):
  - FNO hybrid + canonical: 13.0 GPU-hours for its 12 jobs (4 splits × 3 seeds);
  - all 8 neural models: 146.6 GPU-hours for 96 jobs.
- **Data cost:** generating the 1,212 training-and-test CFD runs is the dominant cost (about 1,212 × 2.6 h
  ≈ 3,200 core-hours at the median).

## Surrogate timing (`spread.py`, stored in `~/tb_verify/ml_spread.json`)

- **Hardware:** laptop, Intel Core i9-13900HX, NVIDIA GeForce RTX 4060 Laptop GPU (8 GB), WSL2 Ubuntu
  24.04, PyTorch 2.14.1 + CUDA 12.6.
- **Model:** FNO hybrid + canonical frame, **3 seeds** (the 3-seed ensemble), all 121 snapshots of the run.
- **Timed:**
  - building the inputs from the run's design parameters, including the plug-flow base field;
  - transfer to the GPU;
  - the forward passes, in batches of 8;
  - the return to the CPU;
  - a `torch.cuda.synchronize()` before stopping the clock.
- **Not timed:**
  - Python and CUDA start-up;
  - loading the three checkpoints and building the input scaling, done once per split;
  - reading the CFD labels (used only for scoring);
  - scoring.
- **Result over 821 test runs** (all four splits): median **1.45 s** per run (10th to 90th percentile 1.41 to
  1.51 s, max 2.75 s).

## CFD timing (`cfdt_all.txt`)

- **Source:** `ClockTime` at the end of 293 dataset solver logs (`log.solver`).
- **Solver:** buoyantPimpleFoam, serial on **one CPU core** per run, on the project's workstations.
- **Result:** median **2.64 h** (10th to 90th percentile 0.65 to 8.38 h).

## Ratio

The ratio of medians is **2.64 h / 1.45 s ≈ 6,500**. The exact value is 6,541; an earlier draft gave
"about 6,455", computed from the rounded 2.6 h, and "about 6,000" in the dossier.

**For the paper:** "a median 1.45 s per run (three-model ensemble, 121 snapshots, RTX 4060 laptop GPU, model
already loaded) against a median 2.6 h of single-core CFD, a latency ratio of about 6,500; the hardware
differs and training cost is not included."
