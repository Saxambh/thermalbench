"""Stage 0 (2026-11-06): PCM mesh spot check, 0.25 mm (fine) vs 0.5 mm dataset run. As spotcheck.py compare pcm,
plus: snapshot times checked to match, field rmse also as % of dT (T_hot - T_init), melt-time difference."""
import csv, glob, json, os, sys
import numpy as np, h5py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcm_front import front_metrics
fine_dir, roots, design = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
D = {r["case_id"]: r for r in csv.DictReader(open(design))}
def block(a):
    t, ny, nx = a.shape
    return a[:, :ny // 2 * 2, :nx // 2 * 2].reshape(t, ny // 2, 2, nx // 2, 2).mean((2, 4))
def t99(lf, t):
    i = np.nonzero(lf >= 0.99)[0]; return float(t[i[0]]) if i.size else np.nan
out = []
for f in sorted(glob.glob(f"{fine_dir}/*/thermbench.h5")):
    c = os.path.basename(os.path.dirname(f))
    g = next((f"{r}/{c}/thermbench.h5" for r in roots if os.path.exists(f"{r}/{c}/thermbench.h5")), None)
    if not g: print(c, "no dataset run"); continue
    with h5py.File(f) as a, h5py.File(g) as b:
        ta, tb = a["times_s"][:], b["times_s"][:]
        n = min(len(ta), len(tb)); tdiff = float(np.max(np.abs(ta[:n] - tb[:n])))
        Ff, Fc = a["fields/T"], b["fields/T"]
        if Ff.shape[1] != 2 * Fc.shape[1] and Ff.shape[1] != 2 * Fc.shape[1] + 1:
            print(c, "shapes", Ff.shape, Fc.shape)
        # interpolate the fine run linearly in time onto the dataset snapshot times (inside the fine range)
        sel = [k for k in range(len(tb)) if ta[0] <= tb[k] <= ta[-1]]
        def interp(F, tt):
            out = []
            for k in sel:
                j = min(max(int(np.searchsorted(ta, tt[k])), 1), len(ta) - 1); w = (tt[k] - ta[j - 1]) / (ta[j] - ta[j - 1])
                out.append((1 - w) * F[j - 1] + w * F[j])
            return block(np.array(out))
        Tf, Tc = interp(Ff, tb), Fc[sel]; n = len(sel)
        ny, nx = min(Tf.shape[1], Tc.shape[1]), min(Tf.shape[2], Tc.shape[2])
        d = Tf[:, :ny, :nx] - Tc[:, :ny, :nx]
        r = D[c]; dT = float(r["superheat_K"]) + float(r["subcooling_K"])
        Af, Ac = interp(a["fields/alpha"], tb), b["fields/alpha"][sel]
        lff, lfc = a["metrics/liquid_fraction"][:], b["metrics/liquid_fraction"][:]
        tf_, tc_ = a["metrics/t_s"][:], b["metrics/t_s"][:]
        row = dict(case=c, material=r["material"], nfins=int(r["nfins"]), fin_t_mm=float(r["fin_t_m"]) * 1000,
                   tilt=float(r["tilt_deg"]), snapshots=n, idx_time_mismatch_s=tdiff, shape_fine=list(Ff.shape[1:]), shape_ds=list(Fc.shape[1:]),
                   rmse_K=float(np.sqrt(np.mean(d ** 2))), rmse_pct_dT=float(100 * np.sqrt(np.mean(d ** 2)) / dT),
                   max_abs_K=float(np.max(np.abs(d))), alpha_rmse=float(np.sqrt(np.mean((Af[:, :ny, :nx] - Ac[:, :ny, :nx]) ** 2))),
                   melt_curve_maxdiff=float(np.max(np.abs(np.interp(tc_, tf_, lff) - lfc))))
        a99, b99 = t99(lff, a["metrics/t_s"][:]), t99(lfc, b["metrics/t_s"][:])
        row.update(t99_fine_s=a99, t99_ds_s=b99, t99_rel_diff_pct=100 * (a99 - b99) / b99)
        hc = json.loads(b.attrs["case_json"])["mesh_h_m"] if "case_json" in b.attrs else 2 * float(r["h_m"]) if "h_m" in r else 0.0005
        row.update(front_metrics(Af[:, :ny, :nx], Ac[:, :ny, :nx], Tf[:, :ny, :nx], Tc[:, :ny, :nx], hc))
    out.append(row); print(json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in row.items()}))
json.dump(out, open("/tmp/spotcheck_pcm_stage0.json", "w"), indent=1)
