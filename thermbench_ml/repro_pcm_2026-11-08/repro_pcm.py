"""Rescore every released PCM checkpoint (FNO, U-Net, Transolver; plain and hybrid; 3 seeds; 6 splits = 108)
from the frozen release alone (8 November 2026), as repro_all_2026-11-08 did for the tank.

Checkpoints: results_pcm_release/ckpt (collect_ckpt.sh, each from the worker that produced the stored score).
For each: rebuild the input encoder from the split's training runs (hybrid flag from the name), score with
the unchanged pcm_train.Predictor + pcm_evaluate.evaluate (stride 5, as in training), and compare every test
run with the per-run score stored by the training job (results_pcm_merged / results_pcm_ts_merged).
Writes repro_pcm.json as it goes.

Distributed mode (8 November, after the single-laptop run was stopped for memory): `repro_pcm.py <worker>`
rescores only the checkpoints that <worker> produced (ckpt_sources.tsv), reading the worker's own copy
(results_pcm/ckpt or results_pcm_ts/ckpt) after checking that its md5 equals the md5 of the release copy.
Writes repro_pcm_<worker>.json; merge.py combines the six.
"""
import hashlib, json, os, sys, time
import torch
HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
sys.path.insert(0, ML)
import pcm_evaluate, pcm_train
from pcm_data import DEFAULT_ROOTS, index
from pcm_splits import SPLITS, split_runs
from models import MODELS

MAN = os.path.join(ML, "manifest_pcm.json")
dev = "cuda" if torch.cuda.is_available() else "cpu"
WORKER = sys.argv[1] if len(sys.argv) > 1 else None
JOBS = {}
for line in open(os.path.join(HERE, "ckpt_sources.tsv")):
    sp, nm, wk, md = line.split()
    JOBS[(sp, nm)] = (wk, md)
torch.set_num_threads(4)
KEYS = ("rmse_K", "alpha_rmse", "liquid_iou", "energy_err", "t90_reached", "t90_err")
out = {"worker": None, "manifest_md5": hashlib.md5(open(MAN, "rb").read()).hexdigest(), "device": dev, "rows": []}
out["worker"] = WORKER
print("worker", WORKER, "manifest md5", out["manifest_md5"], "device", dev, flush=True)
allruns = index(DEFAULT_ROOTS, manifest=MAN)
for split in SPLITS:
    s = split_runs(allruns, split)
    stored = json.load(open(os.path.join(ML, "results_pcm_merged", f"{split}.json")))["results"]
    stored |= json.load(open(os.path.join(ML, "results_pcm_ts_merged", f"{split}.json")))["results"]
    for arch in ("fno", "unet", "transolver"):
        for hyb in (False, True):
            enc = pcm_train.Encoder(s["train"], hybrid=hyb)
            for tag in ("", "_s1", "_s2"):
                name = f"{arch}{'_hybrid' if hyb else ''}{tag}"
                if WORKER and JOBS[(split, name)][0] != WORKER:
                    continue
                ck = (os.path.join(ML, "results_pcm_ts" if arch == "transolver" else "results_pcm", "ckpt", f"ckpt_pcm_{name}_{split}.pt")
                      if WORKER else os.path.join(ML, "results_pcm_release", "ckpt", f"ckpt_pcm_{name}_{split}.pt"))
                if not os.path.exists(ck):
                    print("MISSING", ck, flush=True); out["rows"].append({"split": split, "name": name, "missing": True}); continue
                if hashlib.md5(open(ck, "rb").read()).hexdigest() != JOBS[(split, name)][1]:
                    print("MD5 MISMATCH with release copy", ck, flush=True)
                    out["rows"].append({"split": split, "name": name, "md5_mismatch": True}); continue
                net = MODELS[arch](enc.channels, cout=2, **({"width": 32} if arch == "fno" else {"base": 32}))
                net.load_state_dict(torch.load(ck, map_location=dev)); net.to(dev).eval()
                t0 = time.time()
                res, per = pcm_evaluate.evaluate(pcm_train.Predictor(net, enc, dev), s["test"], 5)
                pr = {p["run_id"]: p for p in stored[name]["per_run"]}
                diff = {}
                for k in KEYS:
                    d = [abs(p[k] - pr[p["run_id"]][k]) for p in per if p["run_id"] in pr]
                    d = [x for x in d if x == x]   # skip NaN (t90 where a run does not cross)
                    diff[k] = max(d, default=0.0)
                row = {"split": split, "name": name, "n_test": len(s["test"]), "n_matched": sum(p["run_id"] in pr for p in per),
                       "repro_rmse_K": res["rmse_K"], "stored_rmse_K": stored[name]["rmse_K"] if "rmse_K" in stored[name] else None,
                       "max_abs_run_diff": diff, "ckpt_md5": hashlib.md5(open(ck, "rb").read()).hexdigest()}
                out["rows"].append(row)
                print(f"{split:15s} {name:22s} repro {res['rmse_K']:.4f}  stored {row['stored_rmse_K']}  runs {row['n_matched']}/{len(per)}  "
                      f"max run diff rmse_K {diff['rmse_K']:.2e}  {time.time() - t0:.0f}s", flush=True)
                json.dump(out, open(os.path.join(HERE, f"repro_pcm{'_' + WORKER if WORKER else ''}.json"), "w"), indent=1)
print("done", flush=True)
