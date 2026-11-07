"""Minimal example: read one ThermalStorageBench tank run without the benchmark code (h5py and numpy only).

  python load_example.py <path to a run folder containing thermbench.h5>

Each run folder holds thermbench.h5 (fields, times, metrics, series; attribute case_json = all inputs) plus
case.json, metrics.json and qc.json. The frozen manifest (thermbench_ml/manifest_full_h5mm.json) lists every
run with its h5 md5.
"""
import json, sys
import h5py
import numpy as np

path = sys.argv[1].rstrip("/") + "/thermbench.h5"
with h5py.File(path) as f:
    case = json.loads(f.attrs["case_json"])
    t = f["times_s"][:]                     # [121] s
    T = f["fields/T"][:]                    # [121, ny, nx] K, row 0 = bottom, uniform cells of mesh_h_m
    E = f["metrics/E_J"][:]                 # stored energy per metre depth, real properties, relative to Tc
    y_mid = f["metrics/y_mid_m"][:]         # thermocline midpoint (NaN when undefined)
    T_out = f["metrics/T_out_K"][:]         # area-averaged outlet temperature
    mdot, Hdot = f["series/outlet_mdot"][:], f["series/outlet_Hdot"][:]   # outlet mass and enthalpy flow, every step

Th, Tc = max(case["T_in_K"], case["T_init_K"]), min(case["T_in_K"], case["T_init_K"])
theta = (T - Tc) / (Th - Tc)               # the benchmark's target
print(f"{case['case']}: {case['mode']}, {case['turbulence']}, W {case['W_m']} m, grid {T.shape[1]} x {T.shape[2]}, "
      f"{len(t)} snapshots to {t[-1]:.0f} s")
print(f"theta range {theta.min():.3f} to {theta.max():.3f}; mean theta at the end {theta[-1].mean():.3f}; "
      f"stored energy {E[0]:.3g} -> {E[-1]:.3g} J/m; outlet {T_out[1]:.2f} -> {T_out[-1]:.2f} K; "
      f"midpoint undefined in {np.isnan(y_mid).mean():.0%} of snapshots")
