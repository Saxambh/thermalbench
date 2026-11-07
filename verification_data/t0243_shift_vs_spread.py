"""T0243_sst, 2.5 mm vs production 5 mm (review item 2.2): is the profile difference a displacement of the
thermocline or a change in its shape (broadening)?

For every snapshot, the row-averaged theta profiles are compared (2.5 mm field block-averaged 2 x 2 onto the
5 mm cells, linear time interpolation onto the production times, as in the paired-reference study). The best
vertical shift d minimises RMS(p_fine(y) - p_prod(y - d)) over d in [-20, 20] mm (0.1 mm steps, linear
interpolation). The share of the profile difference removed by the shift is displacement; what remains is
shape (broadening or sharpening). Also reports the 10-90 % thickness of both profiles.
Writes t0243_shift_vs_spread.json.
"""
import json, os
import numpy as np
import h5py

HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "thermbench_ml"))
from data import index, DEFAULT_ROOTS
PROD = os.path.join([r for r in index(DEFAULT_ROOTS, qc_ok=None) if r.run_id == "T0243_sst"][0].path, "thermbench.h5")
FINE = os.path.expanduser("~/tb_verify/v2/T0243_sst_h25/thermbench.h5")


def load(p):
    with h5py.File(p) as f:
        return f["fields/T"][:].astype(float), f["times_s"][:], json.loads(f.attrs["case_json"])


Tp, tp, cj = load(PROD)
Tf, tf, _ = load(FINE)
Th, Tc = max(cj["T_in_K"], cj["T_init_K"]), min(cj["T_in_K"], cj["T_init_K"])
ny, nx = Tp.shape[1:]
k = Tf.shape[1] // ny
Tf = Tf.reshape(len(Tf), ny, k, nx, k).mean((2, 4))
h = cj["mesh_h_m"] * 1000          # mm
y = (np.arange(ny) + 0.5) * h
th = lambda T: (T - Tc) / (Th - Tc)


def thick(p):
    """10-90 % thickness (mm) of a monotone-ish profile, scanning down from the top as export_case.py."""
    def cross(level):
        d = p - level
        for j in range(len(p) - 1, 0, -1):
            if d[j - 1] * d[j] < 0 or d[j - 1] == 0:
                return y[j - 1] + (y[j] - y[j - 1]) * d[j - 1] / (d[j - 1] - d[j]) if d[j - 1] != d[j] else y[j - 1]
        return np.nan
    return cross(0.9) - cross(0.1)


rows = []
shifts = np.arange(-20, 20.01, 0.1)
for i, t in enumerate(tp):
    if t <= 0 or t < tf[0] or t > tf[-1]:
        continue
    j = min(max(int(np.searchsorted(tf, t)), 1), len(tf) - 1)
    w = (t - tf[j - 1]) / (tf[j] - tf[j - 1])
    pf = th((1 - w) * Tf[j - 1] + w * Tf[j]).mean(1)
    pp = th(Tp[i]).mean(1)
    rms0 = np.sqrt(((pf - pp) ** 2).mean())
    errs = [np.sqrt(((pf - np.interp(y - d, y, pp)) ** 2).mean()) for d in shifts]
    b = int(np.argmin(errs))
    rows.append({"t_s": float(t), "profile_rms_pct": 100 * float(rms0), "best_shift_mm": float(shifts[b]),
                 "after_shift_rms_pct": 100 * float(errs[b]),
                 "thick_prod_mm": float(thick(pp)), "thick_fine_mm": float(thick(pf))})

r = {k2: np.array([x[k2] for x in rows]) for k2 in rows[0]}
n = len(rows)
q = lambda a: [float(np.nanmin(a)), float(np.nanmedian(a)), float(np.nanmax(a))]
summary = {"n_snapshots": n,
           "profile_rms_pct_min_med_max": q(r["profile_rms_pct"]),
           "best_shift_mm_min_med_max": q(r["best_shift_mm"]),
           "after_shift_rms_pct_min_med_max": q(r["after_shift_rms_pct"]),
           "share_of_profile_ms_removed_by_shift": float(1 - (r["after_shift_rms_pct"] ** 2).sum() / (r["profile_rms_pct"] ** 2).sum()),
           "thickness_change_mm_min_med_max (fine minus prod)": q(r["thick_fine_mm"] - r["thick_prod_mm"]),
           "thickness_prod_mm_min_med_max": q(r["thick_prod_mm"])}
for name, sl in (("first half", slice(0, n // 2)), ("second half", slice(n // 2, n))):
    a, b2 = r["profile_rms_pct"][sl], r["after_shift_rms_pct"][sl]
    summary[f"{name}: share removed by shift"] = float(1 - (b2 ** 2).sum() / (a ** 2).sum())
    summary[f"{name}: median thickness change mm"] = float(np.nanmedian(r["thick_fine_mm"][sl] - r["thick_prod_mm"][sl]))
    summary[f"{name}: median shift mm"] = float(np.median(r["best_shift_mm"][sl]))
json.dump({"summary": summary, "rows": rows}, open(os.path.join(HERE, "t0243_shift_vs_spread.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
