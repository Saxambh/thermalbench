#!/usr/bin/env python3
"""Export a finished ThermalStorageBench tank case to one compact file plus metrics.

Reads case.json (written by make_tank_case.py), every time directory and the
function-object logs, and writes into the case directory:
  thermbench.h5  (or thermbench.npz if h5py is not installed)
      fields/T, fields/U (ux, uy), fields/p_rgh, and k, omega, nut if turbulent:
          float32 arrays [time, ny, nx] on the uniform grid (row 0 = bottom)
      times_s, tstar, metrics/*, series/* (every solver step), attrs = case.json
  metrics.json   (snapshot metrics, case summary)

Snapshot metrics (per metre of tank depth, 2D):
  E_J        stored energy relative to the cold temperature Tc
  Ex_J       exergy relative to the dead state Tc
  MIX        MIX number (Davidson et al. 1994): 0 = perfectly stratified, 1 = fully mixed;
             NaN when the tank is (almost) uniform
  Str        stratification number: mean vertical gradient of the row-averaged
             temperature, divided by (Th - Tc)/H
  y_mid_m    height where the row-averaged temperature crosses (Th + Tc)/2
  thick_m    10-90 % thickness of the row-averaged profile
  T_out_K    outlet temperature (area average), at the snapshot time

Raw OpenFOAM output is left in place.
Usage: export_case.py <case_dir>
"""
import json
import math
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_tank_case as gen  # noqa: E402  (same property polynomials and mesh layout)

FLOAT = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"


def read_internal(path, ncell, vector=False):
    s = open(path).read()
    m = re.search(r"internalField\s+uniform\s+(\([^)]*\)|" + FLOAT + r")\s*;", s)
    if m:
        v = [float(x) for x in re.findall(FLOAT, m.group(1))]
        return np.tile(v[:2] if vector else v[0], (ncell, 1) if vector else ncell).astype(float)
    m = re.search(r"internalField\s+nonuniform\s+List<\w+>\s*\d+\s*\((.*?)\n\)\s*;", s, re.S)
    if not m:
        raise ValueError(f"cannot parse internalField in {path}")
    vals = np.array(re.findall(FLOAT, m.group(1)), float)
    if vector:
        return vals.reshape(-1, 3)[:, :2]
    return vals


def time_dirs(case):
    out = []
    for d in os.listdir(case):
        try:
            out.append((float(d), d))
        except ValueError:
            pass
    return sorted(out)


def read_series(path):
    """Two-column function-object log -> (t, value)."""
    t, v = [], []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        t.append(float(p[0]))
        v.append(float(p[1]))
    return np.array(t), np.array(v)


# --- water property integrals (real properties) -------------------------------
def h_int(T):  # integral of cp dT from 0 (J/kg), cp polynomial in T [K]
    return sum(c * T ** (n + 1) / (n + 1) for n, c in enumerate(gen.CP_C))


def s_int(T):  # integral of cp/T dT (J/kg/K)
    c = gen.CP_C
    return c[0] * np.log(T) + sum(c[n] * T ** n / n for n in range(1, len(c)))


def metrics(T, meta, dA):
    """T: [ny, nx] in K. Returns a dict of scalar metrics."""
    real = meta["props"] == "real"
    Th = max(meta["T_in_K"], meta["T_init_K"])
    Tc = min(meta["T_in_K"], meta["T_init_K"])
    H, ny = meta["H_m"], T.shape[0]
    y = (np.arange(ny) + 0.5) * meta["mesh_h_m"]
    if real:
        rho = gen.poly(gen.RHO_C, T)
        dh = h_int(T) - h_int(Tc)
        ds = s_int(T) - s_int(Tc)
    else:  # Boussinesq: constant rho*cp, rho = 992 kg/m3, cp = 4180 J/kg/K
        rho = np.full_like(T, 992.0)
        dh = 4180.0 * (T - Tc)
        ds = 4180.0 * np.log(T / Tc)
    e = rho * dh * dA                       # energy per cell (J per m depth)
    E = float(e.sum())
    Ex = float((rho * (dh - Tc * ds) * dA).sum())
    # MIX number from the energy moment about the bottom
    e_row = e.sum(axis=1)
    M = float((e_row * y).sum())
    W = meta["W_m"]
    if real:
        e_h = float(gen.poly(gen.RHO_C, Th) * (h_int(Th) - h_int(Tc)))  # J/m3 of hot water
    else:
        e_h = 992.0 * 4180.0 * (Th - Tc)
    frac = min(max(E / (e_h * W * H), 0.0), 1.0)    # hot fraction in the ideal tank
    hs = frac * H                                    # hot layer on top, thickness hs
    M_strat = e_h * W * hs * (H - hs / 2)
    M_mixed = E * H / 2
    # undefined for an (almost) uniform tank: no stored or no missing energy
    MIX = ((M_strat - M) / (M_strat - M_mixed)
           if 1e-4 < frac < 1 - 1e-4 else float("nan"))
    # row-averaged profile
    Tbar = T.mean(axis=1)
    Str = float(np.mean(np.diff(Tbar) / meta["mesh_h_m"]) / ((Th - Tc) / H))

    def crossing(level):
        # highest crossing for charging (thermocline below hot layer) is ambiguous only
        # with inversions; use the first crossing scanning downward from the top
        th = Tc + level * (Th - Tc)
        for j in range(ny - 1, 0, -1):
            a, b = Tbar[j - 1] - th, Tbar[j] - th
            if a == 0:
                return float(y[j - 1])
            if a * b < 0:
                return float(y[j - 1] + (y[j] - y[j - 1]) * a / (a - b))
        return float("nan")

    y_mid = crossing(0.5)
    thick = crossing(0.9) - crossing(0.1)   # 90 % level lies above the 10 % level
    return {"E_J": E, "Ex_J": Ex, "MIX": MIX, "Str": Str, "y_mid_m": y_mid,
            "thick_m": thick, "T_mean_K": float(Tbar.mean())}


def main():
    case = os.path.abspath(sys.argv[1])
    meta = json.load(open(f"{case}/case.json"))
    h, nx, ny = meta["mesh_h_m"], meta["nx"], meta["ny"]
    centres = gen.cell_centres(h, meta["x_breaks"], meta["y_breaks"])
    ix = np.array([int(math.floor(x / h)) for x, _ in centres])
    iy = np.array([int(math.floor(y / h)) for _, y in centres])
    ncell = len(centres)
    turb = meta["turbulence"] != "laminar"
    names = ["T", "p_rgh"] + (["k", "omega", "nut"] if turb else [])

    times = time_dirs(case)
    fields = {n: np.zeros((len(times), ny, nx), np.float32) for n in names}
    fields["ux"] = np.zeros((len(times), ny, nx), np.float32)
    fields["uy"] = np.zeros((len(times), ny, nx), np.float32)
    rows = []
    Q = meta["u_in_m_s"] * meta["slot_m"]
    V = meta["W_m"] * meta["H_m"]
    tq, Tout = read_series(f"{case}/postProcessing/outletT/0/surfaceFieldValue.dat")
    for n, (t, d) in enumerate(times):
        for name in names:
            fields[name][n, iy, ix] = read_internal(f"{case}/{d}/{name}", ncell)
        U = read_internal(f"{case}/{d}/U", ncell, vector=True)
        fields["ux"][n, iy, ix] = U[:, 0]
        fields["uy"][n, iy, ix] = U[:, 1]
        m = metrics(fields["T"][n].astype(float), meta, h * h)
        m["t_s"] = t
        m["tstar"] = t * Q / V
        m["T_out_K"] = float(np.interp(t, tq, Tout)) if t > 0 else meta["T_init_K"]
        rows.append(m)

    ts, Tmean = read_series(f"{case}/postProcessing/meanT/0/volFieldValue.dat")
    # outlet mass flow (kg/s) and enthalpy flow (W), per 0.01 m mesh depth, if recorded
    flux = {}
    for fo, key in (("outletFlux", "outlet_mdot"), ("outletHflux", "outlet_Hdot")):
        p = f"{case}/postProcessing/{fo}/0/surfaceFieldValue.dat"
        if os.path.exists(p):
            flux[f"{key}_t_s"], flux[key] = read_series(p)
    keys = list(rows[0].keys())
    out = {"times_s": np.array([r["t_s"] for r in rows]),
           "tstar": np.array([r["tstar"] for r in rows])}
    try:
        import h5py
        path = f"{case}/thermbench.h5"
        with h5py.File(path, "w") as f:
            for k, v in fields.items():
                f.create_dataset(f"fields/{k}", data=v, compression="gzip", compression_opts=4,
                                 chunks=(1, ny, nx))
            for k, v in out.items():
                f.create_dataset(k, data=v)
            for k in keys:
                f.create_dataset(f"metrics/{k}", data=np.array([r[k] for r in rows]))
            f.create_dataset("series/t_s", data=ts)
            f.create_dataset("series/T_mean_K", data=Tmean)
            f.create_dataset("series/T_out_t_s", data=tq)
            f.create_dataset("series/T_out_K", data=Tout)
            for k, v in flux.items():
                f.create_dataset(f"series/{k}", data=v)
            f.attrs["case_json"] = json.dumps(meta)
    except ImportError:
        path = f"{case}/thermbench.npz"
        np.savez_compressed(path, **{f"fields_{k}": v for k, v in fields.items()}, **out,
                            **{f"metrics_{k}": np.array([r[k] for r in rows]) for k in keys},
                            series_t_s=ts, series_T_mean_K=Tmean, series_T_out_t_s=tq,
                            series_T_out_K=Tout, case_json=json.dumps(meta),
                            **{f"series_{k}": v for k, v in flux.items()})
    summary = {"case": meta, "snapshots": rows, "file": os.path.basename(path),
               "file_MB": os.path.getsize(path) / 1e6}
    json.dump(summary, open(f"{case}/metrics.json", "w"), indent=1)
    print(f"{meta['case']}: {len(times)} snapshots -> {os.path.basename(path)} "
          f"({summary['file_MB']:.1f} MB)")


if __name__ == "__main__":
    main()
