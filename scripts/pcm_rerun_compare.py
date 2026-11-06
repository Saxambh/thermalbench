"""PCM: corrected rerun (PCG + DIC pressure) vs original dataset run of the same case (2026-11-07).
Same grid; rerun fields interpolated linearly in time onto the original snapshot times.
usage: pcm_cmp.py design.csv out.json case:rerun.h5:orig.h5 ..."""
import csv, json, sys
import numpy as np, h5py, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcm_front import front_metrics
D = {r["case_id"]: r for r in csv.DictReader(open(sys.argv[1]))}
def t99(lf, t):
    i = np.nonzero(lf >= 0.99)[0]; return float(t[i[0]]) if i.size else float("nan")
out = []
for spec in sys.argv[3:]:
    c, fr, fo = spec.split(":"); r = D[c]; dT = float(r["superheat_K"]) + float(r["subcooling_K"])
    with h5py.File(fr) as a, h5py.File(fo) as b:
        ta, tb = a["times_s"][:], b["times_s"][:]
        sel = [k for k in range(len(tb)) if ta[0] <= tb[k] <= ta[-1] and tb[k] > 0]
        def at(F):
            res = []
            for x in tb[sel]:
                j = min(max(int(np.searchsorted(ta, x)), 1), len(ta) - 1); w = min(max((x - ta[j-1]) / (ta[j] - ta[j-1]), 0), 1)
                res.append((1 - w) * F[j - 1] + w * F[j])
            return np.array(res)
        dTf = at(a["fields/T"]) - b["fields/T"][sel]; dA = at(a["fields/alpha"]) - b["fields/alpha"][sel]
        lfa, lfb, tma, tmb = a["metrics/liquid_fraction"][:], b["metrics/liquid_fraction"][:], a["metrics/t_s"][:], b["metrics/t_s"][:]
        row = dict(case=c, material=r["material"], nfins=int(r["nfins"]), fin_t_mm=float(r["fin_t_m"]) * 1000, tilt=float(r["tilt_deg"]),
                   snapshots=len(sel), field_rms_K=float(np.sqrt(np.mean(dTf ** 2))), field_rms_pct=float(100 * np.sqrt(np.mean(dTf ** 2)) / dT),
                   max_abs_K=float(np.max(np.abs(dTf))), alpha_rms=float(np.sqrt(np.mean(dA ** 2))),
                   melt_curve_maxdiff=float(np.max(np.abs(np.interp(tmb, tma, lfa) - lfb))),
                   t99_rerun=t99(lfa, tma), t99_orig=t99(lfb, tmb))
        row["t99_diff_pct"] = 100 * (row["t99_rerun"] - row["t99_orig"]) / row["t99_orig"]
        h = __import__("json").loads(b.attrs["case_json"])["mesh_h_m"]; mk = b["mask"][:] > 0 if "mask" in b else None
        row.update(front_metrics(at(a["fields/alpha"]), b["fields/alpha"][sel], at(a["fields/T"]), b["fields/T"][sel], h, mk))
    out.append(row); print(json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in row.items()}))
json.dump(out, open(sys.argv[2], "w"), indent=1)
