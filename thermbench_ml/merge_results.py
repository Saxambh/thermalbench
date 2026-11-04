"""Merge the results of the four GPU machines (run_final.sh) on the laptop.
  python merge_results.py results_workers/laptop results_workers/pc3 results_workers/lab results_workers/pc4
Each folder holds that machine's results/<split>.json. Writes results/<split>.json with every
model entry; refuses if two machines produced the same entry or the split sizes differ (which
would mean they did not use the same frozen manifest)."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
merged = {}
for d in sys.argv[1:]:
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        r = json.load(open(f))
        s = r["split"]
        if s not in merged:
            merged[s] = {k: v for k, v in r.items() if k != "results"} | {"results": {}, "sources": {}}
        elif r["sizes"] != merged[s]["sizes"] or r["n_runs"] != merged[s]["n_runs"]:
            sys.exit(f"{f}: split sizes {r['sizes']} differ from {merged[s]['sizes']}: different manifests?")
        for name, v in r["results"].items():
            if name in merged[s]["results"]:
                sys.exit(f"{s}/{name} produced by both {merged[s]['sources'][name]} and {d}")
            merged[s]["results"][name] = v
            merged[s]["sources"][name] = os.path.basename(os.path.normpath(d))
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
for s, r in merged.items():
    json.dump(r, open(os.path.join(HERE, "results", f"{s}.json"), "w"), indent=1)
    print(f"{s}: {len(r['results'])} entries from {sorted(set(r['sources'].values()))}")
