#!/usr/bin/env python3
"""Case-by-case PCM inventory: one authoritative accepted output per physical case (2026-11-07,
collaborator request). Input: inventory_raw.tsv from scripts/pcm_inventory_collect.sh (one row per case
folder found on any machine) and the solver-QC files in D:/ThermBench_data/qc. Rules:
  - usable = DONE, not a moved-away placeholder, pcm_qc.py status OK or WARN, final solver set-up
  - a corrected rerun (PCG + DIC for both pressure solves, or a fresh rerun) replaces the dataset run
  - a dataset run whose pressure solves failed (solver QC FAIL) is not accepted; it needs a corrected rerun
  - between identical copies of a dataset run, one is chosen by machine order; the others are provenance
Output: pcm_inventory_<date>.csv.   usage: pcm_inventory.py inventory_raw.tsv out.csv [running ids] [rerun ids]"""
import csv, collections, glob, sys
R = __file__.rsplit("/scripts/", 1)[0] if "/scripts/" in __file__ else "."
raw, out = sys.argv[1], sys.argv[2]
running = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else set()
reruns_running = set(sys.argv[4].split(",")) if len(sys.argv) > 4 and sys.argv[4] else set()
cases = [r["case_id"] for r in csv.DictReader(open(f"{R}/scripts/pcm_full.csv"))]
cols = "case host folder done moved qc eerr tmelt solver size mtime".split()
rows = [dict(zip(cols, l.rstrip("\n").split("\t"))) for l in open(raw) if l.strip()]
host = {"Saxam": "laptop", "SoRrYnAh": "pc3", "GHLAB-SERVER": "pc4", "DESKTOP-HK82PPA": "lab", "AnupUniConsult": "pc6", "DESKTOP-HDB87J7": "pc7"}
for r in rows:
    r["machine"] = "pc5-archive(laptop D:)" if "tb_data/pc5" in r["folder"] else host.get(r["host"], r["host"])
    r["kind"] = "halffix" if "halffix" in r["folder"] else "rerun" if r["solver"].startswith(("PCG", "fresh")) else "dataset"
sq = {}
for f in sorted(glob.glob("D:/ThermBench_data/qc/first_scan_1106/solver_*.txt")) + sorted(glob.glob("D:/ThermBench_data/qc/solver_*.txt")):
    for l in open(f):
        p = l.split()
        if len(p) == 5 and p[4] in ("ok", "WARN", "FAIL"): sq[p[0]] = p[4]
for extra in glob.glob("D:/ThermBench_data/qc/solver_extra_*.txt"):
    for l in open(extra):
        p = l.split()
        if len(p) == 5: sq[p[0]] = p[4]
by = collections.defaultdict(list)
for r in rows: by[r["case"]].append(r)
pref = {"pc4": 0, "pc6": 1, "lab": 2, "pc7": 3, "pc3": 4, "laptop": 5, "pc5-archive(laptop D:)": 6}
inv = []
for c in cases:
    att = [r for r in by.get(c, []) if r["kind"] != "halffix"]
    ok = [r for r in att if r["done"] == "1" and r["moved"] == "-" and r["qc"] in ("OK", "WARN") and r["solver"].endswith("/fix")]
    rr = [r for r in ok if r["kind"] == "rerun"]; ds = [r for r in ok if r["kind"] == "dataset"]
    s_qc = sq.get(c, "unknown"); pick = None
    if rr: pick, status, note = max(rr, key=lambda r: int(r["mtime"])), "ACCEPTED", "corrected rerun (replaces the dataset run)"
    elif c in reruns_running: status, note = "CORRECTED RERUN RUNNING", ""
    elif ds and s_qc != "FAIL": pick, status, note = min(ds, key=lambda r: (pref[r["machine"]], -int(r["mtime"]))), "ACCEPTED", "dataset run"
    elif ds: status, note = "NEEDS CORRECTED RERUN (solver QC FAIL)", ""
    elif c in running: status, note = "DATASET RUN STILL RUNNING", ""
    else: status, note = "NO USABLE OUTPUT", ""
    copies = [r for r in ds if pick is not None and r is not pick and pick["kind"] == "dataset"]
    inv.append(dict(case_id=c, status=status, accepted_machine=pick["machine"] if pick else "",
        accepted_path=(pick["folder"] + "/" + c) if pick else "", source=note, pcm_qc=pick["qc"] if pick else "",
        solver_qc=("fixed" if pick and pick["kind"] == "rerun" else s_qc),
        series_repaired=("yes" if pick and "series_repaired" in pick["solver"] else "no"),
        energy_err_pct=pick["eerr"] if pick else "", t_melt_s=pick["tmelt"] if pick else "", h5_bytes=pick["size"] if pick else "",
        identical_copies_elsewhere=sum(1 for r in copies if r["size"] == pick["size"]),
        differing_copies=sum(1 for r in copies if r["size"] != pick["size"]), n_attempt_folders=len(by.get(c, [])),
        superseded=";".join(f"{r['machine']}:{r['folder'].rsplit('/', 1)[-1]}[{r['kind']},{r['qc']}]" for r in by.get(c, []) if r is not pick)))
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(inv[0])); w.writeheader(); w.writerows(inv)
st = collections.Counter(i["status"] for i in inv); print(dict(st))
acc = [i for i in inv if i["status"] == "ACCEPTED"]
print("accepted:", len(acc), "pcm_qc", dict(collections.Counter(i["pcm_qc"] for i in acc)), "solver_qc", dict(collections.Counter(i["solver_qc"] for i in acc)),
      "corrected reruns", sum(i["source"].startswith("corrected") for i in acc), "series repaired", sum(i["series_repaired"] == "yes" for i in acc),
      "with differing copies", [i["case_id"] for i in acc if i["differing_copies"]])
for s in st:
    if s != "ACCEPTED": print(" ", s, [i["case_id"] for i in inv if i["status"] == s])
print("folders scanned", len(rows), "| attempt folders per case: max", max(i["n_attempt_folders"] for i in inv))
