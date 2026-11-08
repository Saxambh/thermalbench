"""Merge the six per-worker rescores (repro_pcm_<worker>.json) into repro_pcm.json and print the summary."""
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
rows, meta = [], {}
for f in sorted(glob.glob(os.path.join(HERE, "repro_pcm_*.json"))):
    d = json.load(open(f)); meta[d["worker"]] = {"manifest_md5": d["manifest_md5"], "device": d["device"]}
    rows += [r | {"worker": d["worker"]} for r in d["rows"]]
bad = [r for r in rows if r.get("missing") or r.get("md5_mismatch")]
ok = [r for r in rows if "max_abs_run_diff" in r]
keys = ok[0]["max_abs_run_diff"].keys()
mx = {k: max(r["max_abs_run_diff"][k] for r in ok) for k in keys}
exact = sum(all(v == 0 for v in r["max_abs_run_diff"].values()) for r in ok)
runs = sum(r["n_matched"] for r in ok)
assert len({(r["split"], r["name"]) for r in ok}) == len(ok)
json.dump({"workers": meta, "rows": rows}, open(os.path.join(HERE, "repro_pcm.json"), "w"), indent=1)
print(f"checkpoints rescored {len(ok)}, problems {len(bad)}, all metrics exact {exact}, run scores compared {runs}")
print("max abs per-run difference by metric:", mx)
print("manifests:", {w: m["manifest_md5"][:8] for w, m in meta.items()})
