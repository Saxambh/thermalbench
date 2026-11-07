"""Paired alternate-reference scoring (independent review of 2026-11-07, its section 5.2).

Every held-out tank run with an existing alternative CFD solution is predicted once by each frozen model
(FNO and U-Net, hybrid + canonical frame, each seed and the 3-seed ensemble). The SAME predictions are then
scored against the production label (the dataset run) and against each alternative, on identical snapshots,
masks, clipping and metric code (metrics.score). Alternatives:
  n4    nOuterCorrectors 4            co25  maxCo 0.25
  rep   inlet velocity x 1.0001       h25   2.5 mm mesh, block-averaged 2 x 2 onto the native 5 mm cells
Alternative fields are interpolated linearly in time onto the production snapshot times; only production
snapshots inside the alternative's time range (t > 0) are scored, for every reference alike.
Every eligible case is reported (no selection). Event-window outlet error: snapshots where the reference's
outlet theta has completed 10 to 90 % of its change over the run.
Writes ~/tb_verify/alt_ref.json and prints a summary.
"""
import os, sys, json, numpy as np, torch, h5py
sys.path.insert(0, "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml")
import predict as P, metrics as M, splits as SP
from data import index, port_maps

V = os.path.expanduser("~/tb_verify")
ALT = {   # run_id: {label: path}; T0211, T0243, T0393 from v2/ (corrected inputs); the older sets were superseded
    "T0211_sst": {"n4": "v2/T0211_sst_n4", "co25": "v2/T0211_sst_co25", "rep": "v2/T0211_sst_rep"},
    "T0243_sst": {"h25": "v2/T0243_sst_h25", "n4": "v2/T0243_sst_n4", "co25": "v2/T0243_sst_co25", "rep": "v2/T0243_sst_rep"},
    "T0393_lam": {"n4": "v2/T0393_lam_n4", "co25": "v2/T0393_lam_co25", "rep": "v2/T0393_lam_rep"},
    "T0551_lam": {"h25": "pc6/T0551_lam_h25", "n4": "lab/T0551_lam_n4", "co25": "lab/T0551_lam_co25", "rep": "lab/T0551_lam_rep"},
    "T0221_lam": {"h25": "pc7/T0221_lam_h25", "n4": "lab/T0221_lam_n4", "co25": "lab/T0221_lam_co25", "rep": "lab/T0221_lam_rep"},
    "T0408_lam": {"h25": "lab/T0408_lam_h25", "n4": "lab/T0408_lam_n4", "co25": "lab/T0408_lam_co25", "rep": "lab/T0408_lam_rep"},
    "T0408_sst": {"h25": "lab/T0408_sst_h25", "n4": "lab/T0408_sst_n4", "co25": "lab/T0408_sst_co25", "rep": "lab/T0408_sst_rep"},
}
for r in ("T0052_sst", "T0156_sst", "T0256_sst"):
    ALT[r] = {"n4": f"reg/{r}_n4", "rep": f"reg/{r}_rep"}
for r in ("T0492_sst", "T0828_sst", "T0636_sst", "T0851_sst", "T0108_sst", "T0004_sst", "T0227_sst", "T0696_sst"):
    ALT[r] = {"n4": f"reg2/{r}_n4", "rep": f"reg2/{r}_rep"}
FLAGGED = {"T0211_sst", "T0052_sst"}
dev = "cuda"
man = {r["run_id"] for r in json.load(open(os.path.join(P.HERE, "manifest_full_h5mm.json")))["runs"]}
runs = {r.run_id: r for r in index(P.DEFAULT_ROOTS, qc_ok=None) if r.run_id in man}


def alt_theta(path, run, t_ref):
    """Alternative field as theta on the native grid at the production times t_ref (NaN outside its range)."""
    with h5py.File(os.path.join(V, path, "thermbench.h5")) as f:
        T, ta = f["fields/T"][:], f["times_s"][:]
    ny, nx = run.meta["ny"], run.meta["nx"]
    k = T.shape[1] // ny
    if k > 1:
        assert T.shape[1] == k * ny and T.shape[2] == k * nx, (path, T.shape, ny, nx)
        T = T.reshape(len(T), ny, k, nx, k).mean((2, 4))
    th = (T - run.Tc) / (run.Th - run.Tc)
    out = np.full((len(t_ref), ny, nx), np.nan, np.float32)
    for i, t in enumerate(t_ref):
        if ta[0] <= t <= ta[-1]:
            j = min(max(int(np.searchsorted(ta, t)), 1), len(ta) - 1); w = (t - ta[j - 1]) / (ta[j] - ta[j - 1])
            out[i] = (1 - w) * th[j - 1] + w * th[j]
    return out


def mets(pred, ref, run, outlet):
    s = M.score(pred, ref, run.Th - run.Tc, run.meta["mesh_h_m"], outlet)
    w = outlet / outlet.sum(); o_ref, o_p = (ref * w).sum((1, 2)), (pred * w).sum((1, 2))
    lo, hi = o_ref[0], o_ref[-1]; c = (o_ref - lo) / (hi - lo) if abs(hi - lo) > 0.02 else np.full(len(o_ref), np.nan)
    ev = (c >= 0.1) & (c <= 0.9)
    return {"field_pct": 100 * s["rmse_theta"], "profile_pct": 100 * s["profile_rmse"], "energy_proxy_pct": 100 * s["energy_err"],
            "outlet_pct": 100 * float(np.abs(o_p - o_ref).mean()), "outlet_event_pct": 100 * float(np.abs(o_p - o_ref)[ev].mean()) if ev.any() else float("nan"),
            "ymid_mm": 1000 * s["y_mid_err_m"], "ymid_missing": s["y_mid_missing"], "n_event": int(ev.sum())}


res = []
nets = {}
for rid, alts in ALT.items():
    run = runs[rid]
    for split in SP.SPLITS:
        if SP.side(run, split) != "test":
            continue
        t = run.times()[0]; idx = np.arange(len(t))
        prod = run.field("T", theta=True)
        refs = {"production": prod} | {lab: alt_theta(p, run, t) for lab, p in alts.items()}
        keep = np.ones(len(t), bool); keep[0] = False
        for a in refs.values():
            keep &= np.isfinite(a.reshape(len(t), -1)).all(1)
        m = run.meta; outlet = port_maps(m, m["ny"], m["nx"])[1]
        preds = {}
        for arch in ("fno", "unet"):
            key = (arch, split)
            if key not in nets:
                ck = P.checkpoints("results_merged", f"{arch}_hybrid_canon", split)
                enc = P.encoder(next(iter(ck.values())), split, os.path.join(P.HERE, "manifest_full_h5mm.json"), True, True)[0]
                lst = []
                for tag, f in sorted(ck.items()):
                    net = P.MODELS[arch](enc.channels, **({"width": 32} if arch == "fno" else {"base": 32})); net.load_state_dict(torch.load(f, map_location=dev)); lst.append((tag, P.Predictor(net.to(dev), enc, dev)))
                nets[key] = lst
            seeds = {f"{arch}{tag}": np.clip(p.predict(run, idx), 0, 1) for tag, p in nets[key]}
            preds |= seeds
            preds[f"{arch}_ens"] = np.clip(np.mean(list(seeds.values()), 0), 0, 1)
        row = {"run_id": rid, "split": split, "flagged": rid in FLAGGED, "Ri": m["Ri_H"], "Re": m["Re_in"], "turb": m["turbulence"],
               "n_scored": int(keep.sum()), "n_snap": len(t), "seeds": {a: len(nets[(a, split)]) for a in ("fno", "unet")},
               "ref_vs_production": {lab: mets(a[keep], prod[keep], run, outlet) for lab, a in refs.items() if lab != "production"},
               "scores": {pn: {lab: mets(pv[keep], a[keep], run, outlet) for lab, a in refs.items()} for pn, pv in preds.items()}}
        res.append(row)
        e = row["scores"]
        print(f"{rid} {split:8s} n {row['n_scored']:3d} | " + " | ".join(
            f"{lab}: ref {row['ref_vs_production'][lab]['field_pct']:.2f}  fno {e['fno_ens'][lab]['field_pct']:.2f} unet {e['unet_ens'][lab]['field_pct']:.2f}"
            for lab in alts) + f" | prod: fno {e['fno_ens']['production']['field_pct']:.2f} unet {e['unet_ens']['production']['field_pct']:.2f}", flush=True)
        json.dump(res, open(os.path.join(V, "alt_ref.json"), "w"))
print("done", len(res), "run-split rows")
