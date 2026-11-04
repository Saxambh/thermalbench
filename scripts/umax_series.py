#!/usr/bin/env python3
"""Max |U| / u_in over time with location, plus T range, for one run.  Usage: umax_series.py <run_dir>"""
import json
import sys

import h5py
import numpy as np

d = sys.argv[1]
meta = json.load(open(f"{d}/case.json"))
uin = meta["u_in_m_s"]
f = h5py.File(f"{d}/thermbench.h5", "r")
ux, uy, T = (f[f"fields/{k}"][:].astype(float) for k in ("ux", "uy", "T"))
t = f["series/t_s"][:] if "series/t_s" in f and len(f["series/t_s"]) == len(T) else np.arange(len(T))
nt = len(T)
print(f"u_in {uin}, fields shape {T.shape}, mode {meta.get('mode')}, inlet {meta.get('inlet_port')}, outlet {meta.get('outlet_port')}")
U = np.sqrt(ux ** 2 + uy ** 2)
for k in range(0, nt, max(1, nt // 24)):
    i = np.unravel_index(U[k].argmax(), U[k].shape)
    print(f"snap {k:3d} t {float(t[k]):8.1f}  Umax/u_in {U[k].max() / uin:5.2f} at (row,col) {i}  "
          f"T {T[k].min():6.2f}..{T[k].max():6.2f}  mean {T[k].mean():6.2f}")
