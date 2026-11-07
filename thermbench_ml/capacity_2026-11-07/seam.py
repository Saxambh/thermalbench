"""Stitching lines = plug-flow step in the hybrid base (2026-11-07). Per test run: error in the 2 rows at the
plug-front step vs elsewhere, a jump index (row-to-row change of the prediction at the step minus the CFD's),
and the RMSE after bridging those 2 rows by linear interpolation from their neighbours (post-hoc, no retraining)."""
import os, sys, json, numpy as np, torch
sys.path.insert(0, "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml")
import predict as P, splits as SP
from baselines import IdealStratified
from data import index
dev = "cuda"; out = {}
man = {r["run_id"] for r in json.load(open(os.path.join(P.HERE, "manifest_full_h5mm.json")))["runs"]}
runs = {r.run_id: r for r in index(P.DEFAULT_ROOTS, qc_ok=None) if r.run_id in man}
for split in sys.argv[1:]:
    ck = P.checkpoints("results_merged", "fno_hybrid_canon", split)
    enc, lo, hi = P.encoder(next(iter(ck.values())), split, os.path.join(P.HERE, "manifest_full_h5mm.json"), True, True)
    nets = []
    for f in ck.values():
        net = P.MODELS["fno"](enc.channels, width=32); net.load_state_dict(torch.load(f, map_location=dev)); nets.append(P.Predictor(net.to(dev), enc, dev))
    res = []
    for run in sorted([r for r in runs.values() if SP.side(r, split) == "test"], key=lambda r: r.run_id):
        idx = np.arange(1, len(run.times()[1]))
        th = np.clip(np.mean([p.predict(run, idx) for p in nets], 0), 0, 1)
        tr = run.field("T", theta=True)[1:]; base = IdealStratified().predict(run, idx)
        n, ny, nx = th.shape; fixed = th.copy(); band = np.zeros_like(th, bool); jp, jt = [], []
        for k in range(n):
            d = np.nonzero(np.diff(base[k, :, 0]) != 0)[0]
            if not d.size: continue
            j = d[0]                       # step between rows j and j+1
            if j < 1 or j + 2 >= ny: continue
            band[k, j:j + 2] = True
            jp.append(np.abs(th[k, j + 1] - th[k, j]).mean() - 0.5 * (np.abs(th[k, j] - th[k, j - 1]).mean() + np.abs(th[k, j + 2] - th[k, j + 1]).mean()))
            jt.append(np.abs(tr[k, j + 1] - tr[k, j]).mean() - 0.5 * (np.abs(tr[k, j] - tr[k, j - 1]).mean() + np.abs(tr[k, j + 2] - tr[k, j + 1]).mean()))
            a, b = th[k, j - 1], th[k, j + 2]
            fixed[k, j] = a + (b - a) / 3; fixed[k, j + 1] = a + 2 * (b - a) / 3
        e2 = (th - tr) ** 2; rm = np.sqrt(e2.mean()); rf = np.sqrt(((fixed - tr) ** 2).mean())
        res.append({"run_id": run.run_id, "rmse": 100 * rm, "rmse_bridged": 100 * rf, "band_err_share": float(e2[band].sum() / e2.sum()) if band.any() else 0,
                    "band_area_share": float(band.mean()), "jump_pred": float(np.mean(jp)) if jp else 0, "jump_cfd": float(np.mean(jt)) if jt else 0, "Ri": run.meta["Ri_H"], "turb": run.meta["turbulence"]})
    r = res; rm = np.array([x["rmse"] for x in r]); rf = np.array([x["rmse_bridged"] for x in r]); sh = np.array([x["band_err_share"] for x in r]); ar = np.array([x["band_area_share"] for x in r])
    jp = np.array([x["jump_pred"] for x in r]); jt = np.array([x["jump_cfd"] for x in r]); hard = rm > np.percentile(rm, 90)
    print(f"{split}: n {len(r)} | error share in the 2 step rows: median {np.median(sh):.1%} (area {np.median(ar):.1%}); hardest 10 %: {np.median(sh[hard]):.1%}")
    print(f"   extra jump at the step (theta, pred minus CFD): median {np.median(jp - jt):.3f}, hardest 10 % {np.median((jp - jt)[hard]):.3f}")
    print(f"   field RMSE mean {rm.mean():.2f} -> bridged {rf.mean():.2f} %; median {np.median(rm):.2f} -> {np.median(rf):.2f}; hardest 10 % median {np.median(rm[hard]):.2f} -> {np.median(rf[hard]):.2f}")
    out[split] = res
json.dump(out, open(os.path.expanduser("~/tb_verify/ml_seam.json"), "w"))
