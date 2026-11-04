"""Checks before the tank freeze (freeze_all.sh): list coverage, loader view, duplicates, QC, splits.
  python freeze_check.py <manifest.json> <lists_laptop.json> <lists_lab.json> <lists_pc3.json>
Exit 1 if a run is assigned twice or nowhere, or a finished run is invisible or duplicated."""
import collections, csv, glob, json, os, sys
sys.path.insert(0, ".")
from data import DEFAULT_ROOTS, index
from splits import SPLITS, split_runs
R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
design = [r["run_id"] for r in csv.DictReader(open(f"{R}/design_v2_full.csv"))]
assign = []
MAN = sys.argv[1]
for f in sys.argv[2:]:
    assign += json.load(open(f))
c = collections.Counter(a["run_id"] for a in assign)
print(f"1. coverage: design {len(design)} runs; assigned {len(assign)} entries, {len(c)} distinct")
print(f"   assigned twice: {[k for k, v in c.items() if v > 1][:10]} ({sum(v > 1 for v in c.values())})")
print(f"   in design but nowhere: {sorted(set(design) - set(c))[:10]} ({len(set(design) - set(c))})")
print(f"   assigned but not in design: {sorted(set(c) - set(design))[:10]}")
print(f"   DONE without thermbench.h5: {[a['m'] + ':' + a['run_id'] for a in assign if a['done'] and not a['h5']][:10]}")
done = {a["run_id"] for a in assign if a["done"] and a["h5"]}
print(f"   finished now: {len(done)} of {len(design)}")
# 2. what the loader sees across all roots
allruns = index(DEFAULT_ROOTS, qc_ok=None)
seen = collections.defaultdict(list)
for root in DEFAULT_ROOTS:
    for p in glob.glob(os.path.join(os.path.expanduser(root), "*", "DONE")):
        d = os.path.dirname(p)
        if not glob.glob(f"{d}/MOVED*") and os.path.exists(f"{d}/thermbench.h5"):
            seen[os.path.basename(d)].append((root, os.path.getsize(f"{d}/thermbench.h5")))
dups = {k: v for k, v in seen.items() if len(v) > 1}
diff = {k: v for k, v in dups.items() if len({s for _, s in v}) > 1}
print(f"2. loader: {len(allruns)} runs found; run_ids in more than one root: {len(dups)}"
      f" (different file sizes: {len(diff)}) e.g. {list(diff.items())[:2]}")
missing = done - {r.run_id for r in allruns}
print(f"   finished on a machine but not visible to the loader: {len(missing)} e.g. {sorted(missing)[:8]}")
extra = {r.run_id for r in allruns} - set(design)
print(f"   loader runs not in the design: {len(extra)} e.g. {sorted(extra)[:5]}")
qc = collections.Counter(r.qc.get("verdict", "none") for r in allruns)
print(f"3. QC verdicts: {dict(qc)}")
for r in allruns:
    if r.qc.get("verdict") == "FAIL":
        print(f"   FAIL {r.run_id}: {r.qc.get('fails') or r.qc.get('notes') or r.qc}"[:200])
m = json.load(open(MAN))
print(f"4. manifest: {m['n_runs']} runs, {m['n_cases']} design points; by root: "
      f"{dict(collections.Counter(e['root'].split('/')[-2] + '/' + e['root'].split('/')[-1] for e in m['runs']))}")
runs = index(DEFAULT_ROOTS, manifest=MAN)
for s in SPLITS:
    sp = split_runs(runs, s)
    print(f"   split {s:9s}: " + ", ".join(f"{k} {len(v)}" for k, v in sp.items()))

bad = [k for k, v in c.items() if v > 1] or sorted(set(design) - set(c)) or missing or diff
sys.exit(1 if bad else 0)
