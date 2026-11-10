"""Referee fix 2 (PLAN.md): score the tank models on the flow-weighted (mixing-cup) outlet temperature.

The paper's outlet metric is the area average of the cells next to the outlet ("near-outlet"). Here every model's
predicted theta field is weighted by the CFD's own outflow velocity in those cells (the label's ux / uy at the same
snapshot, outward normal component, negative values set to 0), for prediction and label alike:
    theta_fw = sum(max(u_n, 0) * theta) / sum(max(u_n, 0))     (volume-flux weighted; rho varies < 1 %)
So a model is scored on the outlet temperature a system model would receive, with the true flow split. Snapshots with
no outflow in the outlet cells are skipped (counted). Stride 10, the snapshots of every other tank score.

Models: multinode (refit on train + val, mn_eval protocol), ideal_stratified, rbf, fno_hybrid_canon and
unet_hybrid_canon (3 seeds each, released checkpoints results_merged/ckpt; seed mean per run).
Per run: near-outlet error (recomputed, must equal the stored T_out_err_K) and flow-weighted error (K), over all
scored snapshots and in the breakthrough window (snapshots where the label's flow-weighted theta has moved 10 to 90 %
of its largest change from the first scored snapshot).
Comparison: as multinode_2026-11-08/compare.py, other minus multinode per run, averaged per design, design-level
bootstrap (10,000, seed 20261110), marginal 95 % interval. Writes outlet_flow.json and outlet_flow.md.
Needs the full tank h5 files (with velocities): run on the laptop.
"""
import json, os, sys, time
import numpy as np
import torch
HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
sys.path.insert(0, ML)
import baselines, train
from data import DEFAULT_ROOTS, index, port_maps
from multinode import MultiNode
from models import MODELS
from splits import split_runs

MAN = os.path.join(ML, "manifest_full_h5mm.json")
SPLITS = ("random", "ood_geom", "ood_mode", "ood_flow")
STRIDE, B, SEED = 10, 10_000, 20261110
dev = "cuda" if torch.cuda.is_available() else "cpu"


def outflow_weights(run, idx):
    """[n, ny, nx] outward normal velocity (>= 0) in the outlet cells, 0 elsewhere."""
    m = run.meta
    out = port_maps(m, m["ny"], m["nx"])[1]
    side = m["outlet_port"][0]
    comp, sign = {"left": ("ux", -1), "right": ("ux", 1), "top": ("uy", 1), "bottom": ("uy", -1)}[side]
    u = run.field(comp, idx=idx) * sign
    return np.clip(u, 0, None) * out[None]


def score_run(pred, run, idx, cache):
    if run.run_id not in cache:
        true = run.field("T", idx=idx, theta=True).astype(float)
        w = outflow_weights(run, idx).astype(float)
        ws = w.sum((1, 2))
        ok = ws > 0
        m = run.meta
        o = port_maps(m, m["ny"], m["nx"])[1]
        tfw = np.where(ok, (w * true).sum((1, 2)) / np.where(ok, ws, 1), np.nan)
        d = np.abs(tfw - tfw[ok][0]) if ok.any() else np.zeros(len(tfw))
        mx = np.nanmax(d) if ok.any() else 0.0
        win = ok & (d >= 0.1 * mx) & (d <= 0.9 * mx) if mx > 0 else np.zeros(len(tfw), bool)
        cache[run.run_id] = (true, w, ws, ok, tfw, win, o / o.sum())
    true, w, ws, ok, tfw, win, o = cache[run.run_id]
    dT = run.Th - run.Tc
    pred = np.asarray(pred, float)
    near = np.abs(((pred - true) * o).sum((1, 2))) * dT
    pfw = np.where(ok, (w * pred).sum((1, 2)) / np.where(ok, ws, 1), np.nan)
    fw = np.abs(pfw - tfw) * dT
    f = lambda a, s: float(np.nanmean(a[s])) if s.any() else float("nan")
    return {"near_K": f(near, np.ones(len(near), bool)), "fw_K": f(fw, ok), "near_win_K": f(near, win), "fw_win_K": f(fw, win),
            "n_snap": int(len(ok)), "n_no_outflow": int((~ok).sum()), "n_win": int(win.sum())}


def main():
    allruns = index(DEFAULT_ROOTS, manifest=MAN)
    res = {}
    for split in SPLITS:
        s = split_runs(allruns, split)
        test = s["test"]
        cache, per = {}, {}
        t0 = time.time()
        models = {"multinode": MultiNode().fit(s["train"] + s["val"]),
                  "ideal_stratified": baselines.IdealStratified().fit(s["train"] + s["val"]),
                  "rbf": baselines.RBF().fit(s["train"] + s["val"])}
        for arch in ("fno", "unet"):
            enc = train.Encoder(s["train"], hybrid=True, canon=True)
            for tag in ("", "_s1", "_s2"):
                name = f"{arch}_hybrid_canon{tag}"
                net = MODELS[arch](enc.channels, **({"width": 32} if arch == "fno" else {"base": 32}))
                net.load_state_dict(torch.load(os.path.join(ML, "results_merged", "ckpt", f"ckpt_{name}_{split}.pt"), map_location=dev))
                models[name] = train.Predictor(net.to(dev).eval(), enc, dev)
        for name, m in models.items():
            per[name] = {}
            for r in test:
                idx = np.arange(STRIDE, len(r.times()[0]), STRIDE)
                per[name][r.run_id] = score_run(m.predict(r, idx), r, idx, cache)
            print(f"{split:8s} {name:22s} near {np.nanmean([v['near_K'] for v in per[name].values()]):.3f}  "
                  f"fw {np.nanmean([v['fw_K'] for v in per[name].values()]):.3f}  ({time.time() - t0:.0f} s)", flush=True)
        # seed means per run
        for arch in ("fno", "unet"):
            names = [f"{arch}_hybrid_canon{t}" for t in ("", "_s1", "_s2")]
            per[f"{arch}_hybrid_canon_mean"] = {rid: {k: float(np.nanmean([per[n][rid][k] for n in names])) for k in per[names[0]][rid]}
                                                for rid in per[names[0]]}
        res[split] = {"n_test": len(test), "per_run": per}
        json.dump(res, open(os.path.join(HERE, "outlet_flow.json"), "w"))
    compare(res)


def compare(res):
    md = ["# Flow-weighted vs near-outlet temperature error (K), tank test runs", "",
          "Mean over runs; in brackets the design-level paired difference other minus multinode (positive: multinode better) "
          "with its 95 % bootstrap interval.", ""]
    summ = {}
    for split, S in res.items():
        per = S["per_run"]
        runs = sorted(per["multinode"])
        md += [f"## {split} ({len(runs)} runs)", "", "| model | near-outlet | flow-weighted | near, breakthrough | flow-weighted, breakthrough |", "|---|---|---|---|---|"]
        summ[split] = {}
        for name in ("multinode", "ideal_stratified", "rbf", "fno_hybrid_canon_mean", "unet_hybrid_canon_mean"):
            cells, o = [], {}
            for k in ("near_K", "fw_K", "near_win_K", "fw_win_K"):
                mean = float(np.nanmean([per[name][r][k] for r in runs]))
                o[k] = {"mean": mean}
                if name == "multinode":
                    cells.append(f"{mean:.3f}"); continue
                g = {}
                for r in runs:
                    v = per[name][r][k] - per["multinode"][r][k]
                    if np.isfinite(v):
                        g.setdefault(r.split("_")[0], []).append(v)
                d = np.array([np.mean(v) for v in g.values()])
                bt = d[np.random.default_rng(SEED).integers(0, len(d), (B, len(d)))].mean(1)
                lo, hi = np.percentile(bt, [2.5, 97.5])
                o[k] |= {"diff": float(d.mean()), "ci95": [float(lo), float(hi)], "n_designs": len(d)}
                cells.append(f"{mean:.3f} ({d.mean():+.3f} [{lo:+.3f}, {hi:+.3f}])")
            summ[split][name] = o
            md.append(f"| {name} | " + " | ".join(cells) + " |")
        nn = [per["multinode"][r] for r in runs]
        md += ["", f"Snapshots with no outflow in the outlet cells: {sum(v['n_no_outflow'] for v in nn)} of {sum(v['n_snap'] for v in nn)}; "
               f"breakthrough snapshots: {sum(v['n_win'] for v in nn)}.", ""]
    json.dump(summ, open(os.path.join(HERE, "outlet_flow_summary.json"), "w"), indent=1)
    open(os.path.join(HERE, "outlet_flow.md"), "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    if sys.argv[1:] == ["compare"]:
        compare(json.load(open(os.path.join(HERE, "outlet_flow.json"))))
    else:
        main()
