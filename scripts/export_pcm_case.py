#!/usr/bin/env python3
"""Export a finished ThermalStorageBench PCM melting case to one compact file plus metrics.

Reads case.json (written by make_pcm_case.py), every time directory and the function-object
logs, and writes into the case directory:
  thermbench.h5
      fields/T, fields/alpha (liquid fraction), fields/ux, fields/uy:
          float32 [time, ny, nx] on the uniform grid (row 0 = bottom, column 0 = heated wall).
          Fin cells hold T = wall temperature (isothermal fins) or the solved fin
          temperature (conducting fins), alpha = 0, U = 0; see mask.
      mask [ny, nx]: 1 = PCM cell, 0 = fin
      times_s, tstar (= t / t_melt, NaN if the case never reached full melt)
      metrics/* (per snapshot), series/* (every 10 solver steps), attrs = case.json
  metrics.json   (snapshot metrics, case summary)

Per metre of depth (2D), constant-property (B-2D) energy relative to the initial state:
  E_J = sum over PCM cells of rho (cp (T - T0) + L alpha) dA
Energy balance: E_J against the time integral of the wall + fin heat rate; the error is
reported as a fraction of the full charge rho A (cp (Tw - T0) + L).
Nusselt number as in Kamkari & Shokouhmand (2014): Nu = Q H / (A_w (Tw - Tm) k), with
A_w = H + 2 N L_f per metre of depth (fin tips excluded).
Usage: export_pcm_case.py <case_dir>
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_case import read_internal, time_dirs  # noqa: E402  (same OpenFOAM readers)

EPS = 1e-9


def cell_index(meta):
    """(iy, ix) of every cell in blockMesh order: blocks j-outer/i-inner with the fin blocks
    left out (as make_pcm_case.block_mesh; kept for conducting fins), cells x-fastest within a
    block. Also the mask (0 on fins)."""
    h, xs, ys = meta["mesh_h_m"], meta["x_breaks"], meta["y_breaks"]
    fins = [tuple(f) for f in meta.get("fins_y_m") or []]
    solid = {(0, j) for j in range(len(ys) - 1)
             if any(abs(ys[j] - lo) < EPS and abs(ys[j + 1] - hi) < EPS for lo, hi in fins)}
    in_mesh = meta.get("fin_cells_in_mesh", False)
    iy, ix = [], []
    mask = np.zeros((meta["ny"], meta["nx"]), np.float32)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            if (i, j) in solid and not in_mesh:
                continue
            x0, y0 = round(xs[i] / h), round(ys[j] / h)
            nx, ny = round((xs[i + 1] - xs[i]) / h), round((ys[j + 1] - ys[j]) / h)
            for b in range(ny):
                for a in range(nx):
                    iy.append(y0 + b)
                    ix.append(x0 + a)
            mask[y0:y0 + ny, x0:x0 + nx] = 0 if (i, j) in solid else 1
    return np.array(iy), np.array(ix), mask


def read_table(path, ncol):
    """Numeric rows of a function-object .dat file (first ncol columns)."""
    rows = []
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        try:
            rows.append([float(v) for v in p[:ncol]])
        except ValueError:
            pass
    return np.array(rows, float).reshape(-1, ncol)


def wall_heat(case):
    """Heat rate into the PCM over time (W, through the one-cell-deep mesh), per heated patch.
    Reads heat_<patch> surfaceFieldValue logs, or the older wallHeat log (validation runs)."""
    pp = f"{case}/postProcessing"
    new = sorted(d[len("heat_"):] for d in os.listdir(pp) if d.startswith("heat_"))
    if new:
        per = {}
        for pn in new:
            f = [os.path.join(r, x) for r, _, fs in os.walk(f"{pp}/heat_{pn}") for x in fs
                 if x.endswith(".dat")][0]
            a = read_table(f, 2)
            per[pn] = dict(zip(a[:, 0], a[:, 1]))
        times = np.array(sorted(set.intersection(*(set(v) for v in per.values()))))
        return times, {p: np.array([v[t] for t in times]) for p, v in per.items()}
    path = [os.path.join(r, f) for r, _, fs in os.walk(f"{pp}/wallHeat")
            for f in fs if f.endswith(".dat")][0]
    per = {}
    for line in open(path):
        if line.startswith("#") or not line.strip():
            continue
        t, patch, _, _, q = line.split()[:5]
        per.setdefault(patch, {})[float(t)] = float(q)
    times = np.array(sorted(set.intersection(*(set(v) for v in per.values()))))
    return times, {p: np.array([v[t] for t in times]) for p, v in per.items()}


def main():
    case = os.path.abspath(sys.argv[1])
    meta = json.load(open(f"{case}/case.json"))
    p = meta["props"]
    h, ny, nx = meta["mesh_h_m"], meta["ny"], meta["nx"]
    depth = h                                            # 2D mesh is one cell (h) thick
    iy, ix, mask = cell_index(meta)
    ncell = len(iy)
    if int((mask > 0).sum()) != meta["cells"]:
        raise ValueError(f"PCM cell count {int((mask > 0).sum())} != case.json {meta['cells']}")
    tw, t0, tm = meta["T_wall_K"], meta["T_init_K"], meta["Tmelt_K"]
    rho, cp, L, k = p["rho"], p["cp"], p["L"], p["k"]

    # field snapshots only (older runs also have directories holding just wallHeatFlux)
    times = [(t, d) for t, d in time_dirs(case) if os.path.exists(f"{case}/{d}/T")]
    T = np.full((len(times), ny, nx), tw, np.float32)    # fin cells keep the wall temperature
    alpha = np.zeros((len(times), ny, nx), np.float32)
    ux = np.zeros((len(times), ny, nx), np.float32)
    uy = np.zeros((len(times), ny, nx), np.float32)
    for n, (t, d) in enumerate(times):
        T[n, iy, ix] = read_internal(f"{case}/{d}/T", ncell)
        a_path = f"{case}/{d}/melting:alpha1"
        alpha[n, iy, ix] = read_internal(a_path, ncell) if os.path.exists(a_path) else 0.0
        U = read_internal(f"{case}/{d}/U", ncell, vector=True)
        ux[n, iy, ix], uy[n, iy, ix] = U[:, 0], U[:, 1]

    # series: liquid fraction and mean T (volAverage over PCM cells), wall + fin heat rate
    lf_path = [os.path.join(r, f) for r, _, fs in os.walk(f"{case}/postProcessing/liquidFraction")
               for f in fs if f.endswith(".dat")][0]
    lf = read_table(lf_path, 3)
    tq, qp = wall_heat(case)
    if "finroot" in qp:   # wallHeatFlux used the PCM conductivity on the fin roots
        qp["finroot"] = qp["finroot"] * meta["k_fin"] / k
        qp["fins"] = qp.pop("finroot")
    q_wall = sum(qp.values()) / depth                     # W per m depth (all heated patches)
    q_fins = qp.get("fins", np.zeros_like(tq)) / depth
    E_in = np.concatenate([[0.0], np.cumsum(0.5 * (q_wall[1:] + q_wall[:-1]) * np.diff(tq))])
    A_pcm = float((mask > 0).sum()) * h * h
    E_full = rho * A_pcm * (cp * (tw - t0) + L)
    n_f = meta.get("nfins", 0)
    A_w = meta["H_m"] + 2 * n_f * meta.get("fin_len_m", 0.0)
    nu = q_wall * meta["H_m"] / (A_w * (tw - tm) * k)
    full = np.nonzero(lf[:, 1] >= 0.99)[0]
    t_melt = float(lf[full[0], 0]) if full.size else float("nan")

    rows = []
    pcm = mask > 0
    for n, (t, _) in enumerate(times):
        e = float(rho * h * h * (cp * (T[n][pcm] - t0) + L * alpha[n][pcm]).sum())
        if meta.get("fin_cells_in_mesh"):   # sensible heat stored in the fins (PCM rho cp)
            e += float(rho * h * h * cp * (T[n][~pcm] - t0).sum())
        e_in = float(np.interp(t, tq, E_in)) if t > 0 else 0.0
        rows.append({
            "t_s": t, "liquid_fraction": float(alpha[n][pcm].mean()),
            "T_mean_K": float(T[n][pcm].mean()), "E_J_per_m": e,
            "Q_W_per_m": float(np.interp(t, tq, q_wall)) if t > 0 else float("nan"),
            "Nu": float(np.interp(t, tq, nu)) if t > 0 else float("nan"),
            "energy_balance_err": (e - e_in) / E_full,
        })
    tstar = np.array([r["t_s"] for r in rows]) / t_melt

    import h5py
    path = f"{case}/thermbench.h5"
    with h5py.File(path, "w") as f:
        for name, v in (("T", T), ("alpha", alpha), ("ux", ux), ("uy", uy)):
            f.create_dataset(f"fields/{name}", data=v, compression="gzip", compression_opts=4,
                             chunks=(1, ny, nx))
        f.create_dataset("mask", data=mask)
        f.create_dataset("times_s", data=np.array([r["t_s"] for r in rows]))
        f.create_dataset("tstar", data=tstar)
        for key in rows[0]:
            f.create_dataset(f"metrics/{key}", data=np.array([r[key] for r in rows]))
        f.create_dataset("series/t_s", data=lf[:, 0])
        f.create_dataset("series/liquid_fraction", data=lf[:, 1])
        f.create_dataset("series/T_mean_K", data=lf[:, 2])
        f.create_dataset("series/Q_t_s", data=tq)
        f.create_dataset("series/Q_W_per_m", data=q_wall)
        f.create_dataset("series/Q_fins_W_per_m", data=q_fins)
        f.create_dataset("series/Nu", data=nu)
        f.attrs["case_json"] = json.dumps(meta)
    worst = max(abs(r["energy_balance_err"]) for r in rows)
    summary = {"case": meta, "snapshots": rows, "t_melt_s": t_melt,
               "energy_balance_max_abs_err": worst, "file": os.path.basename(path),
               "file_MB": os.path.getsize(path) / 1e6}
    json.dump(summary, open(f"{case}/metrics.json", "w"), indent=1)
    print(f"{meta['case']}: {len(times)} snapshots, t_melt {t_melt:.0f} s, "
          f"energy balance max error {100 * worst:.2f} % of full charge -> "
          f"{os.path.basename(path)} ({summary['file_MB']:.1f} MB)")


if __name__ == "__main__":
    main()
