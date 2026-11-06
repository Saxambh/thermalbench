"""Recompute the series-based PCM metrics of a resumed case (2026-11-07). Restarted runs left their
postProcessing series in several start-time folders (0/, <t_restart>/ ...), the 0/ file partly corrupted
(NUL bytes from the interrupted write); export_pcm_case.py read only the first folder, so t_melt, Q, Nu
and the energy balance in thermbench.h5 cover only the time before the first restart. The fields and the
snapshot liquid fraction/energy in the h5 are complete and unaffected.
This script merges each series (rows sorted by time, a later folder wins from its start time on, unreadable
lines dropped), recomputes q_wall, E_in, t_melt, Nu and the energy balance exactly as export_pcm_case.py,
and reports them. With --write it backs the h5 up (thermbench.h5.series_bug) and rewrites only the affected
metrics datasets and attributes.   repair_series.py <case_dir> [--write]"""
import json, os, re, sys, shutil
import numpy as np, h5py
case = os.path.abspath(sys.argv[1]); write = "--write" in sys.argv
num = re.compile(r"^[0-9][0-9.e+-]*$")
def series(fo, ncol):
    d = f"{case}/postProcessing/{fo}"; subs = sorted((s for s in os.listdir(d) if num.match(s)), key=float)
    rows = {}
    for k, s in enumerate(subs):
        f = [os.path.join(d, s, x) for x in os.listdir(os.path.join(d, s)) if x.endswith(".dat")][0]
        start = float(s); nxt = float(subs[k + 1]) if k + 1 < len(subs) else np.inf
        for line in open(f, "rb").read().replace(b"\0", b"").decode("ascii", "ignore").splitlines():
            if not line.strip() or line.startswith("#"): continue
            p = line.split()
            try: v = [float(x) for x in p[:ncol]]
            except ValueError: continue
            if len(v) < ncol or not (start - 1e-9 <= v[0] < nxt): continue
            rows[v[0]] = v
    a = np.array([rows[t] for t in sorted(rows)]); return a, subs
meta = json.load(open(f"{case}/case.json")); p = meta["props"]; h = meta["mesh_h_m"]; depth = h
rho, cp, L, k = p["rho"], p["cp"], p["L"], p["k"]; tw, t0, tm = meta["T_wall_K"], meta["T_init_K"], meta["Tmelt_K"]
pp = f"{case}/postProcessing"; pat = sorted(d[5:] for d in os.listdir(pp) if d.startswith("heat_"))
per = {}; nsub = {}
for pn in pat:
    a, subs = series(f"heat_{pn}", 2); per[pn] = dict(zip(a[:, 0], a[:, 1])); nsub[pn] = len(subs)
tq = np.array(sorted(set.intersection(*(set(v) for v in per.values()))))
qp = {pn: np.array([v[t] for t in tq]) for pn, v in per.items()}
if "finroot" in qp: qp["fins"] = qp.pop("finroot") * meta["k_fin"] / k
q_wall = sum(qp.values()) / depth
E_in = np.concatenate([[0.0], np.cumsum(0.5 * (q_wall[1:] + q_wall[:-1]) * np.diff(tq))])
lf, lsubs = series("liquidFraction", 3)
full = np.nonzero(lf[:, 1] >= 0.99)[0]; t_melt = float(lf[full[0], 0]) if full.size else float("nan")
n_f = meta.get("nfins", 0); A_w = meta["H_m"] + 2 * n_f * meta.get("fin_len_m", 0.0)
nu = q_wall * meta["H_m"] / (A_w * (tw - tm) * k)
with h5py.File(f"{case}/thermbench.h5", "r") as f:
    t = f["metrics/t_s"][:]; E = f["metrics/E_J_per_m"][:] if "metrics/E_J_per_m" in f else None
    old = {kk: f[f"metrics/{kk}"][:] for kk in f["metrics"]}
    E_full = None
A_pcm = None
# E_full from the old balance: err = (E - E_in_old)/E_full -> need E_full; recompute as in the exporter
with h5py.File(f"{case}/thermbench.h5", "r") as f:
    mask_cells = meta["cells"]
E_full = rho * mask_cells * h * h * (cp * (tw - t0) + L)
e_in = np.array([float(np.interp(x, tq, E_in)) if x > 0 else 0.0 for x in t])
err = (E - e_in) / E_full if E is not None else None
print(json.dumps(dict(case=os.path.basename(case), folders=len(lsubs), q_rows=len(tq), q_t_end=float(tq[-1]), lf_t_end=float(lf[-1, 0]),
      t_melt_s=t_melt, energy_balance_max_abs_err_pct=round(100 * float(np.max(np.abs(err))), 3) if err is not None else None,
      old_err_pct=round(100 * float(np.max(np.abs(old["energy_balance_err"]))), 2) if "energy_balance_err" in old else None, keys=sorted(old))))
if write:
    import time
    if not os.path.exists(f"{case}/thermbench.h5.series_bug"):
        shutil.copy2(f"{case}/thermbench.h5", f"{case}/thermbench.h5.series_bug")
        shutil.copy2(f"{case}/metrics.json", f"{case}/metrics.json.series_bug")
    q_fins = qp.get("fins", np.zeros_like(tq)) / depth
    with h5py.File(f"{case}/thermbench.h5", "r+") as f:
        tt = f["times_s"][:]
        new = {"tstar": tt / t_melt,
               "metrics/Q_W_per_m": np.array([float(np.interp(x, tq, q_wall)) if x > 0 else np.nan for x in tt]),
               "metrics/Nu": np.array([float(np.interp(x, tq, nu)) if x > 0 else np.nan for x in tt]),
               "metrics/energy_balance_err": err,
               "series/t_s": lf[:, 0], "series/liquid_fraction": lf[:, 1], "series/T_mean_K": lf[:, 2],
               "series/Q_t_s": tq, "series/Q_W_per_m": q_wall, "series/Q_fins_W_per_m": q_fins, "series/Nu": nu}
        for kk, v in new.items():
            if kk in f: del f[kk]
            f.create_dataset(kk, data=v)
        f.attrs["series_repair"] = (f"2026-11-07: series merged from {len(lsubs)} restart folders, t_melt, Q, Nu, "
                                    f"energy balance recomputed (repair_series.py); fields unchanged")
    m = json.load(open(f"{case}/metrics.json"))
    for n_, r in enumerate(m["snapshots"]):
        r["Q_W_per_m"] = float(new["metrics/Q_W_per_m"][n_]); r["Nu"] = float(new["metrics/Nu"][n_])
        r["energy_balance_err"] = float(err[n_])
    m["t_melt_s"] = t_melt; m["energy_balance_max_abs_err"] = float(np.max(np.abs(err)))
    m["file_MB"] = os.path.getsize(f"{case}/thermbench.h5") / 1e6; m["series_repair"] = "2026-11-07, see thermbench.h5 attrs"
    json.dump(m, open(f"{case}/metrics.json", "w"), indent=1)
    with open(f"{case}/export.log", "a") as fl:
        fl.write(f"{meta['case']}: series repaired {time.strftime('%Y-%m-%d %H:%M', time.gmtime())} UTC: t_melt {t_melt:.0f} s, "
                 f"energy balance max error {100 * float(np.max(np.abs(err))):.2f} % of full charge (was "
                 f"{100 * float(np.max(np.abs(old['energy_balance_err']))):.2f} %)\n")
    print("written", os.path.basename(case))
