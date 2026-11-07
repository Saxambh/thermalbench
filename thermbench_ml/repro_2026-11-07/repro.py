"""Reproduce the headline tank table (dossier 8.4, hybrid + canonical rows) from the frozen release alone:
frozen manifest, the frozen h5 data, and the released checkpoints (results_merged/ckpt). The input scaling is
REBUILT from the manifest's training runs (the cached encoder json is not used), each checkpoint is scored with
the unchanged train.Predictor + evaluate.evaluate (stride 10), and every run's score is compared with the
score the training job stored on its worker (~/tb_verify/mljson)."""
import os, sys, json, glob, hashlib, time, numpy as np, torch
HERE = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml"
sys.path.insert(0, HERE)
import evaluate, train
from data import index, DEFAULT_ROOTS
from splits import SPLITS, split_runs
from models import MODELS
MAN = os.path.join(HERE, "manifest_full_h5mm.json")
md5 = hashlib.md5(open(MAN, "rb").read()).hexdigest()
dev = "cuda" if torch.cuda.is_available() else "cpu"
print("manifest md5", md5, "device", dev, flush=True)
stored = {}
for f in glob.glob(os.path.expanduser("~/tb_verify/mljson/*.json")):
    d = json.load(open(f)); w = os.path.basename(f).rsplit("_", 1)[0]
    for name, r in d["results"].items():
        if "hybrid_canon" in name and "_f" not in name:
            stored[(d["split"], name)] = (w, r)
allruns = index(DEFAULT_ROOTS, manifest=MAN)
out = {"manifest_md5": md5, "device": dev, "rows": []}
for split in SPLITS:
    s = split_runs(allruns, split)
    for arch in ("fno", "unet"):
        enc = train.Encoder(s["train"], hybrid=True, canon=True)
        for tag in ("", "_s1", "_s2"):
            name = f"{arch}_hybrid_canon{tag}"
            ck = os.path.join(HERE, "results_merged", "ckpt", f"ckpt_{name}_{split}.pt")
            if not os.path.exists(ck):
                print("missing", ck); continue
            net = MODELS[arch](enc.channels, **({"width": 32} if arch == "fno" else {"base": 32}))
            net.load_state_dict(torch.load(ck, map_location=dev)); net.to(dev)
            t0 = time.time()
            res, per = evaluate.evaluate(train.Predictor(net, enc, dev), s["test"], 10)
            row = {"split": split, "name": name, "n_test": len(s["test"]), "sizes": {k: len(v) for k, v in s.items()},
                   "repro": res, "ckpt_md5": hashlib.md5(open(ck, "rb").read()).hexdigest()}
            if (split, name) in stored:
                w, r = stored[(split, name)]
                pr = {p["run_id"]: p for p in r.get("per_run", [])}
                diffs = [abs(p["rmse_theta"] - pr[p["run_id"]]["rmse_theta"]) for p in per if p["run_id"] in pr]
                row |= {"worker": w, "stored": {k: r[k] for k in res if k in r},
                        "n_matched_runs": len(diffs), "max_abs_run_diff_pct": 100 * max(diffs) if diffs else None}
            out["rows"].append(row)
            st = row.get("stored", {}).get("rmse_theta")
            print(f"{split:8s} {name:22s} repro {100*res['rmse_theta']:.3f}  stored {'' if st is None else f'{100*st:.3f}'}  "
                  f"runs {row.get('n_matched_runs')}/{len(per)}  max run diff {row.get('max_abs_run_diff_pct')}  {time.time()-t0:.0f}s", flush=True)
            json.dump(out, open(os.path.expanduser("~/tb_verify/repro_headline.json"), "w"), indent=1)
print("done")
