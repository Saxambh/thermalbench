"""Fig. 6: example predictions on test runs (run in WSL with the training environment).
Tank: discharge split (ood_mode, never trained on discharge), U-Net hybrid + canonical, mean of the 3 seeds.
PCM: held-out fin counts (ood_fins), U-Net (plain), mean of the 3 seeds.
Each family: the test run with the median per-run field error of that model (seed mean, stored scores),
at three snapshots (25, 50 and 75 % of the run). Columns per time: CFD, prediction, |error|.
Checkpoints: results_merged/ckpt (tank), results_pcm_release/ckpt (PCM); the encoders are rebuilt from the
split's training runs exactly as in repro_all.py / repro_pcm.py. The per-snapshot RMSE of the arrays shown is
recomputed and written to out/fig6_examples.json for checking.
"""
import json, os, sys
import numpy as np
import torch
from style import plt, INK, INK2, MM, ML, OUT, save
sys.path.insert(0, ML)
import train, pcm_train
from data import index as tindex, DEFAULT_ROOTS as TROOTS
from splits import split_runs as tsplit
from pcm_data import index as pindex, DEFAULT_ROOTS as PROOTS
from pcm_splits import split_runs as psplit
from models import MODELS

dev = "cuda" if torch.cuda.is_available() else "cpu"
torch.set_num_threads(4)


def median_run(path, model, key):
    res = json.load(open(path))["results"]
    per = [{p["run_id"]: p[key] for p in res[model + s]["per_run"]} for s in ("", "_s1", "_s2")]
    m = {r: np.mean([d[r] for d in per]) for r in per[0]}
    rid = sorted(m, key=m.get)[len(m) // 2]
    return rid, m[rid]


def ensemble(make_net, ckpts, predictor, run, idx):
    outs = []
    for ck in ckpts:
        net = make_net(); net.load_state_dict(torch.load(ck, map_location=dev)); net.to(dev).eval()
        outs.append(predictor(net)(run, idx))
    return outs


info = {}
# ---- tank
rid_t, err_t = median_run(os.path.join(ML, "results_merged", "ood_mode.json"), "unet_hybrid_canon", "rmse_theta")
s = tsplit(tindex(TROOTS, manifest=os.path.join(ML, "manifest_full_h5mm.json")), "ood_mode")
run_t = [r for r in s["test"] if r.run_id == rid_t][0]
enc = train.Encoder(s["train"], hybrid=True, canon=True)
n = len(run_t.times()[0]); idx_t = np.array([round(0.25 * (n - 1)), round(0.5 * (n - 1)), round(0.75 * (n - 1))])
ck = [os.path.join(ML, "results_merged", "ckpt", f"ckpt_unet_hybrid_canon{s_}_ood_mode.pt") for s_ in ("", "_s1", "_s2")]
outs = ensemble(lambda: MODELS["unet"](enc.channels, base=32), ck, lambda net: train.Predictor(net, enc, dev).predict, run_t, idx_t)
pred_t = np.mean(outs, 0); true_t = run_t.field("T", idx=idx_t, theta=True)
tstar = run_t.times()[1][idx_t] if isinstance(run_t.times(), tuple) and len(run_t.times()) > 1 else idx_t
info["tank"] = {"run": rid_t, "stored_seed_mean_rmse_theta": err_t, "idx": idx_t.tolist(),
                "rmse_theta_shown": [float(np.sqrt(np.nanmean((pred_t[k] - true_t[k]) ** 2))) for k in range(3)]}

# ---- PCM
rid_p, err_p = median_run(os.path.join(ML, "results_pcm_merged", "ood_fins.json"), "unet", "rmse_K")
sp = psplit(pindex(PROOTS, manifest=os.path.join(ML, "manifest_pcm.json")), "ood_fins")
run_p = [r for r in sp["test"] if r.run_id == rid_p][0]
encp = pcm_train.Encoder(sp["train"], hybrid=False)
n = len(run_p.times()[0]); idx_p = np.array([round(0.25 * (n - 1)), round(0.5 * (n - 1)), round(0.75 * (n - 1))])
ckp = [os.path.join(ML, "results_pcm_release", "ckpt", f"ckpt_pcm_unet{s_}_ood_fins.pt") for s_ in ("", "_s1", "_s2")]
outs = ensemble(lambda: MODELS["unet"](encp.channels, cout=2, base=32), ckp,
                lambda net: (lambda r, i: pcm_train.Predictor(net, encp, dev).predict(r, i)[0]), run_p, idx_p)
pred_p = np.mean(outs, 0); true_p = run_p.field("T", idx=idx_p, theta=True); mask = run_p.mask() > 0
dT = run_p.Tw - run_p.T0
info["pcm"] = {"run": rid_p, "stored_seed_mean_rmse_K": err_p, "idx": idx_p.tolist(), "dT_K": float(dT),
               "rmse_K_shown": [float(dT * np.sqrt(np.mean((pred_p[k][mask] - true_p[k][mask]) ** 2))) for k in range(3)],
               "t_s": [float(run_p.times()[0][k]) for k in idx_p]}
info["tank"]["t_s"] = [float(run_t.times()[0][k]) for k in idx_t]
json.dump(info, open(os.path.join(OUT, "fig6_examples.json"), "w"), indent=1)
print(json.dumps(info, indent=1))

# ---- plot: 2 rows (tank, PCM) x 9 columns (3 times x CFD / prediction / |error|)
fig, ax = plt.subplots(2, 9, figsize=(190 * MM, 95 * MM), gridspec_kw={"hspace": 0.35, "wspace": 0.08})
for row, (true, pred, msk, lab, tt) in enumerate(((true_t, pred_t, None, f"Tank {rid_t}, discharge", info["tank"]["t_s"]),
                                                  (true_p, pred_p, mask, f"PCM {rid_p}, held-out fins", info["pcm"]["t_s"]))):
    for k in range(3):
        for c, (arr, cmap, vmax, ttl) in enumerate(((true[k], "RdBu_r", 1, "CFD"), (pred[k], "RdBu_r", 1, "prediction"),
                                                    (np.abs(pred[k] - true[k]), "Greys", 0.3, "|error|"))):
            a = ax[row, 3 * k + c]
            A = np.array(arr, float)
            if msk is not None:
                A = np.where(msk, A, np.nan)
            im = a.imshow(A, origin="lower", cmap=cmap, vmin=0, vmax=vmax, interpolation="nearest")
            a.set_xticks([]); a.set_yticks([])
            for sp_ in a.spines.values():
                sp_.set_visible(False)
            a.set_title((f"t = {tt[k] / 60:.0f} min" if c == 1 else "") + "\n" + ttl, fontsize=6.5)
            if c == 1:
                im_th = im
            if c == 2:
                im_er = im
    ax[row, 0].set_ylabel(lab.replace(", ", ",\n"), fontsize=6.5)
cb1 = fig.colorbar(im_th, ax=ax[:, :], location="bottom", fraction=0.04, pad=0.04, shrink=0.45, anchor=(0.1, 1))
cb1.set_label("Normalised temperature θ")
cb2 = fig.colorbar(im_er, ax=ax[:, :], location="bottom", fraction=0.04, pad=0.04, shrink=0.25, anchor=(0.95, 1))
cb2.set_label("|error| in θ")
save(fig, "fig6_examples")
