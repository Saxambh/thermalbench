"""Seed-spread vs error for the main model on every test run of each split (2026-11-07)."""
import os, sys, json, time, numpy as np, torch
sys.path.insert(0, "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml")
import predict as P, metrics as M, splits as SP
from data import index, port_maps
dev = "cuda"; out = {}
runs = [r for r in index(P.DEFAULT_ROOTS, qc_ok=None)]
man = {r["run_id"] for r in json.load(open(os.path.join(P.HERE, "manifest_full_h5mm.json")))["runs"]}
runs = {r.run_id: r for r in runs if r.run_id in man}
print("runs", len(runs), flush=True)
for split in sys.argv[1:]:
    ck = P.checkpoints("results_merged", "fno_hybrid_canon", split)
    enc, lo, hi = P.encoder(next(iter(ck.values())), split, os.path.join(P.HERE, "manifest_full_h5mm.json"), True, True)
    nets = []
    for f in ck.values():
        net = P.MODELS["fno"](enc.channels, width=32); net.load_state_dict(torch.load(f, map_location=dev)); nets.append(P.Predictor(net.to(dev), enc, dev))
    test = [r for r in runs.values() if SP.side(r, split) == "test"]
    res = []
    for n, run in enumerate(sorted(test, key=lambda r: r.run_id)):
        idx = np.arange(len(run.times()[1])); t0 = time.time()
        preds = [p.predict(run, idx) for p in nets]
        if dev == "cuda": torch.cuda.synchronize()
        dt = time.time() - t0
        init = run.field("T", idx=[0], theta=True)[0]
        for pr in preds: pr[0] = init
        th = np.clip(np.mean(preds, 0), 0, 1); sd = np.std(preds, 0)
        true = run.field("T", theta=True); m = run.meta; dT = run.Th - run.Tc
        s = M.score(th[1:], true[1:], dT, m["mesh_h_m"], port_maps(m, m["ny"], m["nx"])[1])
        err = np.abs(th[1:] - true[1:]); sdd = sd[1:]
        sd_rms = float(np.sqrt((sdd ** 2).mean()))
        # does the spread sit where the error is? correlation over cells and snapshots
        c = float(np.corrcoef(sdd.ravel(), err.ravel())[0, 1])
        # share of the squared error inside the 10 % of cells with the largest spread
        top = sdd >= np.quantile(sdd, 0.9); share = float((err[top] ** 2).sum() / (err ** 2).sum())
        res.append({"run_id": run.run_id, "rmse_pct": 100 * s["rmse_theta"], "energy_pct": 100 * s["energy_err"], "Tout_K": s["T_out_err_K"],
                    "ymid_mm": 1000 * s["y_mid_err_m"], "profile_pct": 100 * s["profile_rmse"], "r2": s["r2_field"],
                    "sd_pct": 100 * sd_rms, "corr_sd_err": c, "err_in_top10sd": share, "pred_s": dt, "n_snap": len(idx),
                    "Re": m["Re_in"], "Ri": m["Ri_H"], "turb": m["turbulence"], "mode": m["mode"]})
        if n % 25 == 0: print(split, n, len(test), run.run_id, f"{res[-1]['rmse_pct']:.2f} sd {res[-1]['sd_pct']:.2f} {dt:.1f}s", flush=True)
    out[split] = res
    json.dump(out, open(os.path.expanduser("~/tb_verify/ml_spread.json"), "w"))
print("done")
