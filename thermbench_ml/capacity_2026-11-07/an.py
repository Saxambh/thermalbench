import json, os, numpy as np
from scipy.stats import spearmanr
d = json.load(open(os.path.expanduser("~/tb_verify/ml_spread.json")))
for sp, res in d.items():
    rm = np.array([r["rmse_pct"] for r in res]); sd = np.array([r["sd_pct"] for r in res]); ri = np.array([r["Ri"] for r in res])
    c = np.array([r["corr_sd_err"] for r in res]); sh = np.array([r["err_in_top10sd"] for r in res]); t = np.array([r["pred_s"] for r in res])
    e = np.array([r["energy_pct"] for r in res]); to = np.array([r["Tout_K"] for r in res])
    print(f"\n== {sp}: n {len(res)}  ensemble field RMSE mean {rm.mean():.2f} median {np.median(rm):.2f} | energy median {np.median(e):.2f} | outlet median {np.median(to):.2f} K")
    print(f" run level: Spearman(spread, error) {spearmanr(sd, rm)[0]:+.2f}   Spearman(Ri, error) {spearmanr(ri, rm)[0]:+.2f}   spread/error median {np.median(sd/rm):.2f}")
    # flagging: top 10 % by spread, how many of the top-10 % error runs?
    k = max(1, len(rm) // 10); fs = set(np.argsort(sd)[-k:]); fe = set(np.argsort(rm)[-k:]); print(f" top-10 % by spread catches {len(fs & fe)}/{k} of the top-10 % by error")
    for thr in [5, 10]:
        bad = rm > thr
        if bad.any():
            for q in [0.5, 0.8]:
                cut = np.quantile(sd, q); fl = sd > cut
                print(f"  error>{thr}% ({bad.sum()} runs): flag spread>{q:.0%} quantile ({cut:.2f}%) -> recall {np.mean(fl[bad]):.0%}, precision {np.mean(bad[fl]):.0%}")
    # if we keep only the less uncertain half
    keep = sd <= np.median(sd); print(f"  keep lower-spread half: median error {np.median(rm[keep]):.2f}, max {rm[keep].max():.2f}; other half median {np.median(rm[~keep]):.2f}")
    print(f" within run: corr(spread, |err|) over cells median {np.median(c):.2f}; error share in top-10 % spread cells median {np.median(sh):.0%}")
    print(f" prediction time per run (3 seeds, GPU, laptop): median {np.median(t):.2f} s, max {t.max():.2f} s")
