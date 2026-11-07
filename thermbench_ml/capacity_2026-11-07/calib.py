"""Spread calibration (2026-11-07): fit on validation runs only, check on test runs.
Per run and per snapshot: field RMSE of the 3-seed mean and RMS seed spread (both % dT).
k_q = q-quantile of error/spread on validation -> predicted bound k_q * spread; coverage checked on test."""
import os, sys, json, numpy as np, torch
sys.path.insert(0, "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml")
import predict as P, splits as SP
from data import index
dev = "cuda"
man = {r["run_id"] for r in json.load(open(os.path.join(P.HERE, "manifest_full_h5mm.json")))["runs"]}
runs = {r.run_id: r for r in index(P.DEFAULT_ROOTS, qc_ok=None) if r.run_id in man}
out = {}
for split in sys.argv[1:]:
    ck = P.checkpoints("results_merged", "fno_hybrid_canon", split)
    enc, lo, hi = P.encoder(next(iter(ck.values())), split, os.path.join(P.HERE, "manifest_full_h5mm.json"), True, True)
    nets = []
    for f in ck.values():
        net = P.MODELS["fno"](enc.channels, width=32); net.load_state_dict(torch.load(f, map_location=dev)); nets.append(P.Predictor(net.to(dev), enc, dev))
    out[split] = {}
    for part in ("val", "test"):
        rr = []
        for run in sorted([r for r in runs.values() if SP.side(r, split) == part], key=lambda r: r.run_id):
            idx = np.arange(1, len(run.times()[1]))
            pr = np.array([p.predict(run, idx) for p in nets]); th = np.clip(pr.mean(0), 0, 1); sd = pr.std(0)
            tr = run.field("T", theta=True)[1:]
            e_s = np.sqrt(((th - tr) ** 2).mean((1, 2))) * 100; s_s = np.sqrt((sd ** 2).mean((1, 2))) * 100
            rr.append({"run_id": run.run_id, "err": float(np.sqrt((e_s ** 2).mean())), "sd": float(np.sqrt((s_s ** 2).mean())),
                       "err_snap": e_s.round(4).tolist(), "sd_snap": s_s.round(4).tolist()})
        out[split][part] = rr
        print(split, part, len(rr), flush=True)
    json.dump(out, open(os.path.expanduser("~/tb_verify/ml_calib.json"), "w"))
