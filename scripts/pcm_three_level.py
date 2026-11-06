"""PCM three-level mesh study (1.0 / 0.5 / 0.25 mm, ratio 2). Per case: t99 at each level, observed order
p = ln(|f3-f2|/|f2-f1|)/ln 2 (f1 finest), monotonic check, Richardson extrapolation and GCI (Celik 2008,
Fs 1.25) only if monotonic and 0.5 <= p <= 3 (pre-registered); field and melt-curve differences between
neighbouring levels (finer block-averaged onto coarser, matched times).  usage: three.py name f100 f050 f025"""
import sys, json, math, numpy as np, h5py
name, f3, f2, f1 = sys.argv[1:5]
def t99(f):
    with h5py.File(f) as a:
        lf, t = a["metrics/liquid_fraction"][:], a["metrics/t_s"][:]
    i = np.nonzero(lf >= 0.99)[0]; return float(t[i[0]]) if i.size else float("nan")
def block(x): t, ny, nx = x.shape; return x[:, :ny // 2 * 2, :nx // 2 * 2].reshape(t, ny // 2, 2, nx // 2, 2).mean((2, 4))
def pair(fine, coarse):
    with h5py.File(fine) as a, h5py.File(coarse) as b:
        ta, tb = a["times_s"][:], b["times_s"][:]; sel = [k for k in range(len(tb)) if ta[0] <= tb[k] <= ta[-1] and tb[k] > 0]
        def at(F):
            out = []
            for x in tb[sel]:
                j = min(max(int(np.searchsorted(ta, x)), 1), len(ta) - 1); w = min(max((x - ta[j-1]) / (ta[j] - ta[j-1]), 0), 1)
                out.append((1 - w) * F[j - 1] + w * F[j])
            return block(np.array(out))
        Tf, Tc = at(a["fields/T"]), b["fields/T"][sel]; ny, nx = min(Tf.shape[1], Tc.shape[1]), min(Tf.shape[2], Tc.shape[2])
        cj = json.loads(b.attrs["case_json"]); dT = cj["T_wall_K"] - cj["T_init_K"]
        d = Tf[:, :ny, :nx] - Tc[:, :ny, :nx]
        lfa, lfb = a["metrics/liquid_fraction"][:], b["metrics/liquid_fraction"][:]
        return dict(field_pct=float(100 * np.sqrt(np.mean(d ** 2)) / dT), melt_curve_maxdiff=float(np.max(np.abs(np.interp(tb, ta, lfa) - lfb))))
v3, v2, v1 = t99(f3), t99(f2), t99(f1)
e32, e21 = v3 - v2, v2 - v1
mono = e32 * e21 > 0
p = math.log(abs(e32 / e21)) / math.log(2) if e21 != 0 and e32 != 0 else float("nan")
res = dict(case=name, t99_1mm=v3, t99_05mm=v2, t99_025mm=v1, change_1_to_05_pct=100 * (v2 - v3) / v3, change_05_to_025_pct=100 * (v1 - v2) / v2,
           monotonic=bool(mono), observed_order=p, pair_05_vs_1=pair(f2, f3), pair_025_vs_05=pair(f1, f2))
if mono and 0.5 <= p <= 3:
    r21 = 2 ** p; ext = v1 + (v1 - v2) / (r21 - 1)
    res.update(extrapolated_t99=ext, err_05mm_vs_extrap_pct=100 * (v2 - ext) / ext, err_025mm_vs_extrap_pct=100 * (v1 - ext) / ext,
               GCI_fine_025mm_pct=100 * 1.25 * abs((v1 - v2) / v1) / (r21 - 1), GCI_medium_05mm_pct=100 * 1.25 * abs((v2 - v3) / v2) / (r21 - 1))
else: res["note"] = "no GCI: not monotonic or order outside [0.5, 3]"
print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in res.items()}))
