import sys, json, os, numpy as np, h5py
sys.path.insert(0, "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml")
import predict as P, metrics as M
from data import index
V = os.path.expanduser("~/tb_verify")
man = {r["run_id"] for r in json.load(open(os.path.join(P.HERE, "manifest_full_h5mm.json")))["runs"]}
runs = {r.run_id: r for r in index(P.DEFAULT_ROOTS, qc_ok=None) if r.run_id in man}
ALTS = {"T0211_sst": ["v2/T0211_sst_n4", "v2/T0211_sst_co25", "v2/T0211_sst_rep"],
        "T0052_sst": ["reg/T0052_sst_n4", "reg/T0052_sst_rep"], "T0156_sst": ["reg/T0156_sst_n4", "reg/T0156_sst_rep"]}
def interp(path, run, t):
    with h5py.File(f"{V}/{path}/thermbench.h5") as f: T, ta = f["fields/T"][:], f["times_s"][:]
    th = (T - run.Tc) / (run.Th - run.Tc); out = np.full((len(t),) + th.shape[1:], np.nan, np.float32)
    for i, ti in enumerate(t):
        if ta[0] <= ti <= ta[-1]:
            j = min(max(int(np.searchsorted(ta, ti)), 1), len(ta) - 1); w = (ti - ta[j-1]) / (ta[j] - ta[j-1]); out[i] = (1-w)*th[j-1] + w*th[j]
    return out, ta[-1]
for rid, alts in ALTS.items():
    run = runs[rid]; t = run.times()[0]; prod = run.field("T", theta=True)
    A = [interp(p, run, t) for p in alts]
    keep = t > 0
    for a, _ in A: keep &= np.isfinite(a.reshape(len(t), -1)).all(1)
    d = A[0][0][keep] - prod[keep]
    s = M.score(A[0][0][keep], prod[keep], run.Th - run.Tc, run.meta["mesh_h_m"], np.ones(prod.shape[1:], bool))
    print(rid, "t_end prod", t[-1], "alts", [round(float(e), 1) for _, e in A], f"n {keep.sum()} pooled {100*np.sqrt((d**2).mean()):.2f} per-snap {100*np.sqrt((d**2).mean((1,2))).mean():.2f} metrics.score {100*s['rmse_theta']:.2f}")
