#!/bin/bash
# After distributed training: collect every worker's results to the laptop, merge, tables, figures.
#   bash results_all.sh tank      (run_final.sh workers: results/, results_pc5a/, results_pc5b/)
#   bash results_all.sh pcm       (run_final_pcm.sh workers: results_pcm*/)
# Writes results_workers[_pcm]/<worker>/ (copies), the merged <results>/<split>.json, tables.md,
# summary.csv and figures/. Safe to rerun while training is still going (partial tables).
set -e
F=${1:?tank or pcm}
cd "$(dirname "$(readlink -f "$0")")"
if [ $F = tank ]; then P=results; W=results_workers; else P=results_pcm; W=results_workers_pcm; fi
mkdir -p $W
for x in laptop: lab:labpc:thermbench_ml/$P pc3:saxam@pc3:thermbench_ml/$P pc4:saxam@pc4:thermbench_ml/$P \
         pc5a:pc5:thermalbench/thermbench_ml/${P}_pc5a pc5b:pc5:thermalbench/thermbench_ml/${P}_pc5b; do
  IFS=: read -r w h d <<< "$x"
  mkdir -p $W/$w
  if [ -z "$h" ]; then cp $P/*.json $W/$w/ 2>/dev/null || true
  else scp -q "$h:$d/*.json" $W/$w/ 2>/dev/null || echo "  $w: no results yet"; fi
  echo "  $w: $(ls $W/$w/*.json 2>/dev/null | wc -l) split files"
done
OUT=${P}_merged
python3 - $W $OUT <<'PY'
import glob, json, os, sys
W, OUT = sys.argv[1], sys.argv[2]
merged = {}
for d in sorted(glob.glob(f"{W}/*/")):
    for f in sorted(glob.glob(d + "*.json")):
        r = json.load(open(f))
        if "split" not in r: continue
        s = r["split"]
        m = merged.setdefault(s, {k: v for k, v in r.items() if k != "results"} | {"results": {}, "sources": {}})
        if r.get("sizes") != m.get("sizes"):
            sys.exit(f"{f}: split sizes {r.get('sizes')} differ from {m.get('sizes')}: different manifests?")
        for name, v in r["results"].items():
            if name in m["results"] and m["sources"][name] != os.path.basename(d[:-1]):
                sys.exit(f"{s}/{name} produced by both {m['sources'][name]} and {d}")
            m["results"][name] = v; m["sources"][name] = os.path.basename(d[:-1])
os.makedirs(OUT, exist_ok=True)
for s, r in merged.items():
    json.dump(r, open(f"{OUT}/{s}.json", "w"), indent=1)
    print(f"  {s}: {len(r['results'])} entries from {sorted(set(r['sources'].values()))}")
PY
PY=~/venvs/tbml-gpu/bin/python
$PY tables.py --results $OUT --family $F > /dev/null && echo "  tables: $OUT/tables.md, $OUT/summary.csv"
$PY figures.py --results $OUT --family $F
