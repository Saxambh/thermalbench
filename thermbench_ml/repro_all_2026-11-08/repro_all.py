"""Reproduce the full tank table (all 8 neural variants x 3 seeds x 4 splits = 96 checkpoints) from the frozen
release alone (8 November 2026). Extends repro_2026-11-07 (hybrid + canonical rows only) to every variant.

For each checkpoint in results_merged/ckpt: rebuild the input encoder from the split's training runs
(hybrid/canon flags from the model name; the cached encoder json is not used), score with the unchanged
train.Predictor + evaluate.evaluate (stride 10), and compare every run with the per-run score stored in
results_merged/<split>.json by the training job. Writes repro_all.json (rows) as it goes.
"""
import hashlib, json, os, sys, time
import torch
HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
sys.path.insert(0, ML)
import evaluate, train
from data import index, DEFAULT_ROOTS
from splits import SPLITS, split_runs
from models import MODELS

MAN = os.path.join(ML, "manifest_full_h5mm.json")
dev = "cuda" if torch.cuda.is_available() else "cpu"
ONLY = sys.argv[1:]   # optional: split name (rescore one entry, merged into repro_all.json)
prev = json.load(open(os.path.join(HERE, "repro_all.json")))["rows"] if ONLY else []
out = {"manifest_md5": hashlib.md5(open(MAN, "rb").read()).hexdigest(), "device": dev, "rows": []}
print("manifest md5", out["manifest_md5"], "device", dev, flush=True)
allruns = index(DEFAULT_ROOTS, manifest=MAN)
for split in (ONLY[:1] or SPLITS):
    s = split_runs(allruns, split)
    stored = json.load(open(os.path.join(ML, "results_merged", f"{split}.json")))["results"]
    for arch in ("fno", "unet"):
        for var in ("", "_canon", "_hybrid", "_hybrid_canon"):
            enc = train.Encoder(s["train"], hybrid="hybrid" in var, canon="canon" in var)
            for tag in ("", "_s1", "_s2"):
                name = f"{arch}{var}{tag}"
                if ONLY[1:] and name != ONLY[1]:
                    continue
                ck = os.path.join(ML, "results_merged", "ckpt", f"ckpt_{name}_{split}.pt")
                if not os.path.exists(ck):
                    print("MISSING", ck, flush=True); out["rows"].append({"split": split, "name": name, "missing": True}); continue
                net = MODELS[arch](enc.channels, **({"width": 32} if arch == "fno" else {"base": 32}))
                net.load_state_dict(torch.load(ck, map_location=dev)); net.to(dev).eval()
                t0 = time.time()
                res, per = evaluate.evaluate(train.Predictor(net, enc, dev), s["test"], 10)
                row = {"split": split, "name": name, "n_test": len(s["test"]), "repro": res,
                       "ckpt_md5": hashlib.md5(open(ck, "rb").read()).hexdigest()}
                if name in stored:
                    pr = {p["run_id"]: p for p in stored[name].get("per_run", [])}
                    d = [abs(p["rmse_theta"] - pr[p["run_id"]]["rmse_theta"]) for p in per if p["run_id"] in pr]
                    row |= {"stored": {k: stored[name][k] for k in res if k in stored[name]},
                            "n_matched_runs": len(d), "max_abs_run_diff_pct": 100 * max(d) if d else None}
                out["rows"].append(row)
                st = row.get("stored", {}).get("rmse_theta")
                print(f"{split:8s} {name:22s} repro {100 * res['rmse_theta']:.3f}  stored {'none' if st is None else f'{100 * st:.3f}'}  "
                      f"runs {row.get('n_matched_runs')}/{len(per)}  max run diff {row.get('max_abs_run_diff_pct')}  {time.time() - t0:.0f}s", flush=True)
                rows = [r for r in prev if (r["split"], r["name"]) not in {(x["split"], x["name"]) for x in out["rows"]}] + out["rows"]
                json.dump(out | {"rows": rows}, open(os.path.join(HERE, "repro_all.json"), "w"), indent=1)
print("done", flush=True)
