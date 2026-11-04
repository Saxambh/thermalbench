#!/usr/bin/env python3
"""Quality checks on finished ThermalStorageBench PCM cases (directories with DONE and thermbench.h5).

Per case, writes <case>/qc.json once (skipped on later passes unless --redo), then writes
<root>/qc_report.csv over all checked cases and prints the WARN/FAIL ones.

Checks (FAIL = exclude or rerun, WARN = look at it):
  complete   fields readable, no NaN/inf, >= 30 snapshots                          FAIL / WARN < 30
  melted     final liquid fraction >= 0.99 (cases stop themselves at 0.995)          FAIL
  bounds     share of cell-snapshots with T outside [T0 - 0.5, Tw + 0.5] K           FAIL > 0.1 %, WARN any
  alpha      liquid fraction outside [-0.001, 1.001]                                 FAIL
  monotone   largest drop of the melted fraction between snapshots                   WARN > 0.5 %
  energy     drift of the energy balance after the first snapshot,
             max |err(t) - err(t1)| (fraction of a full charge)                      FAIL > 1 %, WARN > 0.3 %
             offset |err(t1)|: start-up artefact of the fin-root flux spike,
             2026-11-03 (5 fins: 1.5 %)                                              WARN > 3 %
  t_melt     t(0.99) / t_ref (pcm_data a priori scale; P0dt 1.13)                    WARN outside [0.5, 2]
  velocity   max |U| over the run                                                    WARN > 0.05 m/s
Usage: pcm_qc.py <root> [<root> ...] [--redo]
"""
import csv, glob, json, math, os, sys
import h5py
import numpy as np

C_NU = 0.236   # as pcm_data.t_ref


def t_ref(m):
    p = m["props"]
    sh, sub = m["T_wall_K"] - m["Tmelt_K"], m["Tmelt_K"] - m["T_init_K"]
    E = p["rho"] * m["W_m"] * (p["L"] + p["cp"] * (sub + sh / 2))
    q = C_NU * p["k"] * sh / m["H_m"] * m["Ra_H"] ** 0.25
    f_tilt = float(np.interp(float(m.get("tilt_deg", 0.0)), [0, 45, 90], [1.0, 0.62, 0.46]))
    return E / q * (1 + m.get("nfins", 0)) ** -0.5 * f_tilt


def check(case):
    m = json.load(open(f"{case}/case.json"))
    r = {"case": os.path.basename(case), "status": "OK", "notes": []}
    def flag(level, note):
        r["notes"].append(f"{level} {note}")
        if level == "FAIL" or r["status"] == "OK":
            r["status"] = "FAIL" if level == "FAIL" or r["status"] == "FAIL" else level
    try:
        f = h5py.File(f"{case}/thermbench.h5", "r")
        T, a = f["fields/T"][:], f["fields/alpha"][:]
        ux, uy = f["fields/ux"][:], f["fields/uy"][:]
        mask = f["mask"][:] > 0.5
        met = {k: f[f"metrics/{k}"][:] for k in f["metrics"]}
    except Exception as e:  # noqa: BLE001
        flag("FAIL", f"unreadable: {e}")
        return r
    n = T.shape[0]
    r["snapshots"] = n
    if not all(np.isfinite(x).all() for x in (T, a, ux, uy)):
        flag("FAIL", "NaN/inf in fields")
    if n < 30:
        flag("WARN", f"only {n} snapshots")
    lf = met["liquid_fraction"]
    r["lf_end"] = float(lf[-1])
    if lf[-1] < 0.99:
        flag("FAIL", f"not melted: liquid fraction {lf[-1]:.3f} at end")
    T0, Tw = m["T_init_K"], m["T_wall_K"]
    out = float(((T < T0 - 0.5) | (T > Tw + 0.5)).mean())
    r["bounds_frac"] = out
    if out > 1e-3:
        flag("FAIL", f"T out of bounds in {100 * out:.2f} % of cell-snapshots")
    elif out > 0:
        flag("WARN", f"T out of bounds in {100 * out:.4f} % of cell-snapshots")
    if a.min() < -1e-3 or a.max() > 1.001:
        flag("FAIL", f"alpha range {a.min():.4f}..{a.max():.4f}")
    drop = float(max(0.0, -np.diff(lf).min())) if n > 1 else 0.0
    r["max_melt_drop"] = drop
    if drop > 5e-3:
        flag("WARN", f"melted fraction drops by {100 * drop:.2f} % between snapshots")
    e = met["energy_balance_err"]
    if n > 2:
        drift = float(np.abs(e[1:] - e[1]).max())
        r["energy_drift"], r["energy_offset"] = drift, float(e[1])
        if drift > 0.01:
            flag("FAIL", f"energy balance drifts {100 * drift:.2f} %")
        elif drift > 0.003:
            flag("WARN", f"energy balance drifts {100 * drift:.2f} %")
        if abs(e[1]) > 0.03:
            flag("WARN", f"energy start-up offset {100 * e[1]:.2f} %")
    t = met["t_s"]
    i = np.nonzero(lf >= 0.99)[0]
    if i.size:
        r["t_melt_s"] = float(t[i[0]])
        r["t_melt_over_tref"] = r["t_melt_s"] / t_ref(m)
        if not 0.5 <= r["t_melt_over_tref"] <= 2.0:
            flag("WARN", f"t_melt / t_ref = {r['t_melt_over_tref']:.2f}")
    umax = float(np.sqrt(ux ** 2 + uy ** 2).max())
    r["u_max"] = umax
    if umax > 0.05:
        flag("WARN", f"max |U| {umax:.3f} m/s")
    for k in ("material", "nfins", "tilt_deg", "W_m"):
        r[k] = m.get(k)
    return r


def main():
    redo = "--redo" in sys.argv
    for root in [os.path.expanduser(x) for x in sys.argv[1:] if not x.startswith("--")]:
        rows = []
        for done in sorted(glob.glob(f"{root}/*/DONE")):
            case = os.path.dirname(done)
            if not os.path.exists(f"{case}/thermbench.h5"):
                continue
            q = f"{case}/qc.json"
            if os.path.exists(q) and not redo and os.path.getmtime(q) >= os.path.getmtime(f"{case}/thermbench.h5"):
                rows.append(json.load(open(q)))
                continue
            r = check(case)
            json.dump(r, open(q, "w"), indent=1)
            rows.append(r)
        if not rows:
            print(f"{root}: no finished cases yet")
            continue
        keys = ["case", "status", "material", "nfins", "tilt_deg", "W_m", "snapshots", "lf_end", "t_melt_s",
                "t_melt_over_tref", "energy_offset", "energy_drift", "bounds_frac", "max_melt_drop", "u_max", "notes"]
        with open(f"{root}/qc_report.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(r | {"notes": "; ".join(r["notes"])} for r in rows)
        st = {s: sum(r["status"] == s for r in rows) for s in ("OK", "WARN", "FAIL")}
        tr = [r["t_melt_over_tref"] for r in rows if "t_melt_over_tref" in r]
        print(f"{root}: {len(rows)} cases, OK {st['OK']}, WARN {st['WARN']}, FAIL {st['FAIL']}"
              + (f"; t_melt/t_ref median {np.median(tr):.2f} [{min(tr):.2f}, {max(tr):.2f}]" if tr else ""))
        for r in rows:
            if r["status"] != "OK":
                print(f"  {r['status']:4s} {r['case']}: {'; '.join(r['notes'])}")


if __name__ == "__main__":
    main()
