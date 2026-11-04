#!/usr/bin/env python3
"""Quality checks on finished ThermalStorageBench runs (directories with DONE and thermbench.h5).

Per run, writes <case>/qc.json once (skipped on later passes), then prints a summary
and writes <batch>/qc_report.csv over all checked runs.

Checks (FAIL = exclude or rerun, WARN = look at it):
  complete     snapshot count = nsnap + 1, last snapshot at end time, no NaN/inf    FAIL
  energy       stored-energy change vs net enthalpy flow through the ports:
               |dE - (E_in - E_out)| / max(E_in, |dE|)                             FAIL > 3 %, WARN > 1 %
               E_out from the exact outlet flux sum(phi*h) when recorded (runs generated
               from 1 Nov 2026); otherwise from the area-averaged outlet T, which is biased
               when the outlet has backflow or a non-uniform velocity profile
  bounds       share of cell-snapshots outside [Tc - 0.5, Th + 0.5] K               FAIL > 0.1 %, WARN any
  direction    hot inflow adds energy, cold inflow removes it                       FAIL
  outlet_T     outlet temperature within [Tc - 0.5, Th + 0.5] K                     FAIL
  velocity     max |U| over the run / u_in                                          WARN > 40
  growth       final-10 % max |U| / early-half max |U|                              FAIL > 3, WARN > 2
               (a late-half peak alone is not used: in discharge the outgoing thermocline
               gives a physical transient of up to ~4 u_in at the outlet that then decays)
  backflow     largest fraction of outlet cells with inflow, any snapshot           info
Usage: qc_runs.py <batch_dir> [--redo]
"""
import csv
import glob
import json
import os
import sys

import numpy as np
import h5py

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_tank_case as gen  # noqa: E402
from export_case import h_int  # noqa: E402

DEPTH = 0.01     # mesh depth (m) in make_tank_case.block_mesh
T_STD = 298.15   # OpenFOAM sensible-enthalpy reference temperature


def rho_h(T, real):
    """Density and specific enthalpy relative to 0 K (real) or a constant-property stand-in."""
    if real:
        return gen.poly(gen.RHO_C, T), h_int(T)
    return np.full_like(np.asarray(T, float), 992.0), 4180.0 * np.asarray(T, float)


def check(case):
    meta = json.load(open(f"{case}/case.json"))
    real = meta["props"] == "real"
    f = h5py.File(f"{case}/thermbench.h5", "r")
    T = f["fields/T"][:].astype(float)
    ux, uy = f["fields/ux"][:], f["fields/uy"][:]
    t = f["times_s"][:]
    nt, ny, nx = T.shape
    h = meta["mesh_h_m"]
    Th = max(meta["T_in_K"], meta["T_init_K"])
    Tc = min(meta["T_in_K"], meta["T_init_K"])
    r = {"run_id": os.path.basename(case), "mode": meta["mode"], "type": meta["inlet_type"],
         "turb": meta["turbulence"], "u_in": meta["u_in_m_s"]}
    flags = []

    # complete
    nsnap = round(meta["end_time_s"] / meta["write_interval_s"])
    finite = all(np.isfinite(f[k][:]).all() for k in ("fields/T", "fields/ux", "fields/uy"))
    end_ok = abs(t[-1] - meta["end_time_s"]) < 1e-3 * meta["end_time_s"]
    r["snaps"] = nt
    if not (finite and end_ok and nt >= nsnap + 1):
        flags.append("FAIL:complete")

    # energy balance, per metre depth, relative to Tc
    dA = h * h
    rho, hh = rho_h(T, real)
    hc = rho_h(np.array(Tc), real)[1]
    E = (rho * (hh - hc)).sum(axis=(1, 2)) * dA
    M = rho.sum(axis=(1, 2)) * dA
    Q = meta["u_in_m_s"] * meta["slot_m"]
    rin, hin = rho_h(np.array(meta["T_in_K"]), real)
    mdot_in = float(rin) * Q
    tq, Tq = f["series/T_out_t_s"][:], f["series/T_out_K"][:]
    _, hq = rho_h(Tq, real)
    # outflow mass rate = inflow - rate of change of tank mass (from snapshots)
    dMdt = np.interp(tq, 0.5 * (t[1:] + t[:-1]), np.diff(M) / np.diff(t))
    mdot_out = mdot_in - dMdt
    E_in = mdot_in * float(hin - hc) * (t[-1] - t[0])
    E_out = np.trapz(mdot_out * (hq - hc), tq)
    r["energy_src"] = "outlet_T"
    dE = E[-1] - E[0]
    r["energy_err_Tavg"] = abs(dE - (E_in - E_out)) / max(abs(E_in), abs(dE), 1e-12)
    if "series/outlet_Hdot" in f:  # exact: sum(phi*h) and sum(phi) on the outlet, 0.01 m depth
        tm, md = f["series/outlet_mdot_t_s"][:], f["series/outlet_mdot"][:] / DEPTH
        tH, Hd = f["series/outlet_Hdot_t_s"][:], f["series/outlet_Hdot"][:] / DEPTH
        hs_c = float(hc) - float(rho_h(np.array(T_STD), real)[1])  # solver h is relative to T_STD
        E_out = np.trapz(Hd, tH) - hs_c * np.trapz(md, tm)
        r["energy_src"] = "outlet_flux"
    dE = E[-1] - E[0]
    scale = max(abs(E_in), abs(dE), 1e-12)
    r["energy_err"] = abs(dE - (E_in - E_out)) / scale
    if r["energy_err"] > 0.03:
        flags.append("FAIL:energy")
    elif r["energy_err"] > 0.01:
        flags.append("WARN:energy")

    # bounds and direction
    r["Tmin_off"] = T.min() - Tc
    r["Tmax_off"] = T.max() - Th
    # isolated start-up overshoots of a few cells are a known nOuterCorrectors=1 artefact
    # (P10: +3.6 K in 6 cells at t = 8 s); fail only if excursions are widespread
    r["bounds_frac"] = float(((T > Th + 0.5) | (T < Tc - 0.5)).mean())
    if r["bounds_frac"] > 1e-3:
        flags.append("FAIL:bounds")
    elif r["Tmin_off"] < -0.5 or r["Tmax_off"] > 0.5:
        flags.append("WARN:bounds")
    if (meta["T_in_K"] > meta["T_init_K"]) != (dE > 0):  # hot inflow must add energy
        flags.append("FAIL:direction")
    if Tq.min() < Tc - 0.5 or Tq.max() > Th + 0.5:
        flags.append("FAIL:outlet_T")

    # velocity
    U = np.sqrt(ux.astype(float) ** 2 + uy.astype(float) ** 2).reshape(nt, -1).max(axis=1)
    r["Umax_rel"] = U.max() / meta["u_in_m_s"]
    r["growth"] = U[-max(2, nt // 10):].max() / max(U[1:nt // 2].max(), 1e-12)
    if r["Umax_rel"] > 40:
        flags.append("WARN:velocity")
    if r["growth"] > 3:
        flags.append("FAIL:growth")
    elif r["growth"] > 2:
        flags.append("WARN:growth")

    # outlet backflow
    side, a, b = meta["outlet_port"]
    if side in ("left", "right"):
        un = ux[:, int(round(a / h)):int(round(b / h)), 0 if side == "left" else nx - 1]
        un = un * (-1 if side == "left" else 1)
    else:
        un = uy[:, ny - 1 if side == "top" else 0, int(round(a / h)):int(round(b / h))]
        un = un * (1 if side == "top" else -1)
    r["backflow"] = float((un < 0).mean(axis=1).max())
    # without the exact outlet flux, a backflowing outlet makes the balance unreliable
    if r["energy_src"] == "outlet_T" and r["backflow"] > 0.1 and "FAIL:energy" in flags:
        flags[flags.index("FAIL:energy")] = "WARN:energy_unmeasured"

    r["flags"] = " ".join(flags)
    r["verdict"] = "FAIL" if any(x.startswith("FAIL") for x in flags) else \
        ("WARN" if flags else "OK")
    for k, v in r.items():
        if isinstance(v, (np.floating, np.integer)):
            r[k] = v.item()
    return r


def main():
    batch = os.path.abspath(sys.argv[1])
    redo = "--redo" in sys.argv
    rows = []
    for done in sorted(glob.glob(f"{batch}/*/DONE")):
        case = os.path.dirname(done)
        if os.path.exists(f"{case}/MOVED_TO_LAPTOP") or not os.path.exists(f"{case}/thermbench.h5"):
            continue
        qf = f"{case}/qc.json"
        if os.path.exists(qf) and not redo:
            rows.append(json.load(open(qf)))
            continue
        try:
            r = check(case)
        except Exception as e:  # report, do not stop the pass
            r = {"run_id": os.path.basename(case), "verdict": "FAIL", "flags": f"FAIL:qc_error {e}"}
        json.dump(r, open(qf, "w"), indent=1)
        rows.append(r)
    if not rows:
        print("no finished runs")
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(f"{batch}/qc_report.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    n = {v: sum(r["verdict"] == v for r in rows) for v in ("OK", "WARN", "FAIL")}
    err = [r["energy_err"] for r in rows if "energy_err" in r]
    print(f"QC {os.path.basename(batch)}: {len(rows)} runs  OK {n['OK']}  WARN {n['WARN']}  FAIL {n['FAIL']}"
          + (f"  energy error median {np.median(err):.2%} max {max(err):.2%}" if err else ""))
    for r in rows:
        if r["verdict"] != "OK":
            print(f"  {r['run_id']:12} {r['verdict']:4}  {r['flags']}")


if __name__ == "__main__":
    main()
