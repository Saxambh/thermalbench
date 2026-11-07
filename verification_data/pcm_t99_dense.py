"""PCM mesh study (review item 3.3, 8 November 2026): t99 from the dense liquid-fraction series instead of the
snapshots, and the solver time step per level.

The mesh-study t99 values were taken as the first SNAPSHOT with liquid fraction >= 0.99
(scripts/pcm_mesh_compare.py), so they are quantised by the write interval (42 s for G131, 40 s for G301,
15 s for P0021/G021). Each h5 also holds series/liquid_fraction, logged every 10 solver steps; here t99 is
its first crossing of 0.99, linearly interpolated. The solver time step is the series spacing / 10
(the function objects write every 10 steps; adjustTimeStep yes, maxCo 1.0, maxDeltaT 0.5 s at every level).
GCI as in the dossier: r = 2, p = ln((f_coarse - f_med)/(f_med - f_fine))/ln 2, Fs = 1.25,
GCI_fine = Fs |f_fine - f_med| / (2^p - 1) / f_fine (and the medium-grid value), when the three are monotone.
Writes pcm_t99_dense.json and prints a table.
"""
import glob, json, os
import numpy as np
import h5py

HERE = os.path.dirname(os.path.abspath(__file__))
rows = {}
for p in sorted(glob.glob(os.path.expanduser("~/tb_verify/pcm3/*/thermbench.h5"))):
    name = os.path.basename(os.path.dirname(p))
    with h5py.File(p) as f:
        ts, lf = f["series/t_s"][:], f["series/liquid_fraction"][:]
        tsn, lfn = f["metrics/t_s"][:], f["metrics/liquid_fraction"][:]
        h = json.loads(f.attrs["case_json"])["mesh_h_m"]
    i = np.nonzero(lf >= 0.99)[0]
    t_dense = float(ts[i[0] - 1] + (0.99 - lf[i[0] - 1]) * (ts[i[0]] - ts[i[0] - 1]) / (lf[i[0]] - lf[i[0] - 1])) if i.size and i[0] > 0 else None
    j = np.nonzero(lfn >= 0.99)[0]
    t_snap = float(tsn[j[0]]) if j.size else None
    rows[name] = {"h_mm": 1000 * h, "t99_snapshot_s": t_snap, "t99_dense_s": t_dense,
                  "write_interval_s": float(np.median(np.diff(tsn))),
                  "solver_dt_median_s": float(np.median(np.diff(ts))) / 10, "solver_dt_p10_s": float(np.percentile(np.diff(ts), 10)) / 10}


def gci(c, m, f):
    out = {"coarse": c, "medium": m, "fine": f}
    if not ((c - m) * (m - f) > 0):
        return out | {"monotone": False}
    p = np.log((c - m) / (m - f)) / np.log(2)
    ext = f + (f - m) / (2 ** p - 1)
    return out | {"monotone": True, "p": float(p), "extrapolated_s": float(ext),
                  "GCI_fine_pct": float(100 * 1.25 * abs(f - m) / (2 ** p - 1) / f),
                  "GCI_medium_pct": float(100 * 1.25 * abs(m - c) / (2 ** p - 1) / m)}


res = {"runs": rows, "gci": {}}
for g in ("G131", "G301"):
    for key in ("t99_snapshot_s", "t99_dense_s"):
        v = [rows.get(f"{g}_h{x}", {}).get(key) for x in ("100", "050", "025")]
        if all(x is not None for x in v):
            res["gci"][f"{g} {key}"] = gci(*v)
json.dump(res, open(os.path.join(HERE, "pcm_t99_dense.json"), "w"), indent=1)
for k, r in rows.items():
    print(f"{k:11s} h {r['h_mm']:.2f} mm  write {r['write_interval_s']:5.1f} s  solver dt {r['solver_dt_median_s']:.3f} s  "
          f"t99 snapshot {r['t99_snapshot_s']}  dense {r['t99_dense_s'] and round(r['t99_dense_s'], 1)}")
for k, g in res["gci"].items():
    print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in g.items()})
