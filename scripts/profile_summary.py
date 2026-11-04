#!/usr/bin/env python3
"""Thermocline position and thickness from the centreline T profiles of a tank case."""
import glob
import os
import sys

case = os.path.expanduser(sys.argv[1])
T0, TIN = 293.15, 333.15
mid, lo, hi = 0.5 * (T0 + TIN), T0 + 0.1 * (TIN - T0), T0 + 0.9 * (TIN - T0)


def crossing(ys, ts, level):
    # scan from the top down: first height where T drops below level
    for k in range(len(ys) - 1, 0, -1):
        if ts[k] >= level > ts[k - 1]:
            return ys[k - 1] + (level - ts[k - 1]) * (ys[k] - ys[k - 1]) / (ts[k] - ts[k - 1])
    return None


print("time_s  T_top_C  T_bottom_C  thermocline_y_m  thickness_10_90_m")
dirs = sorted(glob.glob(f"{case}/postProcessing/profile/*"), key=lambda d: float(os.path.basename(d)))
for d in dirs:
    f = glob.glob(f"{d}/centreline*")[0]
    ys, ts = [], []
    for line in open(f):
        p = line.split()
        if len(p) >= 2:
            ys.append(float(p[0])); ts.append(float(p[1]))
    ym, ylo, yhi = crossing(ys, ts, mid), crossing(ys, ts, lo), crossing(ys, ts, hi)
    th = (yhi - ylo) if (ylo is not None and yhi is not None) else None
    fmt = lambda v: f"{v:.3f}" if v is not None else "  n/a"
    print(f"{float(os.path.basename(d)):6.0f}  {ts[-1]-273.15:7.2f}  {ts[0]-273.15:9.2f}  {fmt(ym):>15}  {fmt(th):>17}")
