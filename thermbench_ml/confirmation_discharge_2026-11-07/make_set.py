"""Discharge confirmation set (run ids only, no scores), revision 2 after the review of 7 November.

Rule: ood_mode test runs whose design (case_id) appears in no evaluation made before the model freeze, in
any split. Exposure is counted from
  (a) recorded per-run scores in the pre-freeze results folders listed in PRE_FREEZE, and
  (b) the reconstructable membership of the one aggregate-only pre-freeze evaluation (n1 pilot, 31 Oct).
Model freeze: commit d42ce92, 2026-11-04 13:29 (code, run_final.sh); later changes to the training and
scoring code are docstrings and added baselines only. Evaluations after the freeze (data efficiency,
6 Nov; paired reference, capacity analysis, 7 Nov) informed no model choice and do not count.

Also checks, from ids only (no score is read or printed), that every model entry the analysis needs has a
per-run score for every confirmation run and that all three seeds exist.
"""
import glob, hashlib, json, os, sys
H = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml"
OUT = H + "/confirmation_discharge_2026-11-07"
sys.path.insert(0, H)
from data import index, DEFAULT_ROOTS
from splits import split_runs

MAN = H + "/manifest_full_h5mm.json"
PRE_FREEZE = {   # folder: (date, what it informed)
    "results_testpass_2026-11-01": ("2026-11-01", "pipeline test pass"),
    "results_interim_2026-11-02": ("2026-11-02", "interim benchmark; ablation that led to the canonical frame"),
    "results_modediag_2026-11-02": ("2026-11-02", "discharge diagnostics; canonical frame adopted, main model chosen"),
    "results_epochcheck_ep60": ("2026-11-03", "epoch choice"),
    "results_epochcheck_ep150": ("2026-11-03", "epoch choice"),
    "results_rehearsal": ("2026-11-04 08:32", "full-pipeline rehearsal before the final runs"),
}
POST_FREEZE_NOT_COUNTED = {"results_dataeff": "2026-11-06, data efficiency, after the freeze"}

exposed, record = set(), {}
byid = {r.run_id: r for r in index(DEFAULT_ROOTS, qc_ok=None)}   # every run on disk, for reconstruction
for b, (date, why) in PRE_FREEZE.items():
    d = os.path.join(H, b)
    if not os.path.isdir(d):
        sys.exit(f"FAIL: expected pre-freeze folder {b} is missing")
    files = sorted(glob.glob(os.path.join(d, "**", "*.json"), recursive=True))
    mans = [f for f in files if os.path.basename(f).startswith("manifest")]
    ids, checks, n_files = set(), [], 0
    for f in files:
        if f in mans:
            continue
        r = json.load(open(f))
        if not (isinstance(r, dict) and "results" in r):
            continue
        n_files += 1
        n_test = r["sizes"]["test"]
        if not r["results"]:
            sys.exit(f"FAIL: {f} has no result entries")
        # A results file accumulates entries from successive sessions (evaluate.save merges), and "sizes"
        # records the test split of the LAST save. Entries from earlier sessions, when fewer runs had
        # finished, list fewer runs. Required: no duplicates; at least one entry lists exactly the recorded
        # test size; every other entry is a subset of such a full entry; the union equals that full set.
        sets = {}
        for name, v in r["results"].items():
            lst = [p["run_id"] for p in v.get("per_run", [])] if isinstance(v, dict) else []
            if not lst or len(set(lst)) != len(lst):
                sys.exit(f"FAIL: {f}:{name} has no per-run list or duplicate run ids")
            sets[name] = set(lst)
        full = [n for n, s in sets.items() if len(s) == n_test]
        if not full:
            sys.exit(f"FAIL: {f}: no entry lists the recorded {n_test} test runs")
        file_ids = set().union(*sets.values())
        if any(sets[n] != sets[full[0]] for n in full) or file_ids != sets[full[0]]:
            sys.exit(f"FAIL: {f}: entries list runs outside the recorded test set")
        partial = {n: len(s) for n, s in sets.items() if len(s) != n_test}
        # where the evaluation kept its run list, rebuild its test set from ids and compare
        recon = "not reconstructable (no run list kept); checked against the recorded test size only"
        for m in mans:
            ml = json.load(open(m))
            sub = [byid[x["run_id"]] for x in ml["runs"] if x["run_id"] in byid]
            if len(sub) != len(ml["runs"]):
                sys.exit(f"FAIL: {m}: {len(ml['runs']) - len(sub)} listed runs not found on disk")
            t = {x.run_id for x in split_runs(sub, r["split"])["test"]}
            if t != file_ids:
                sys.exit(f"FAIL: {f}: reconstructed test set differs from recorded ids "
                         f"(missing {sorted(t - file_ids)[:5]}, extra {sorted(file_ids - t)[:5]})")
            recon = f"reconstructed from {os.path.basename(m)}: identical ({len(t)} runs)"
        checks.append({"file": os.path.relpath(f, d), "split": r["split"], "test_recorded": n_test,
                       "ids_listed": len(file_ids), "entries": len(r["results"]),
                       "earlier_session_entries_subset_of_full": partial, "membership": recon})
        ids |= file_ids
    if n_files == 0 or not ids:
        sys.exit(f"FAIL: pre-freeze folder {b} yields no results")
    designs = {i.split("_")[0] for i in ids}
    record[b] = {"date": date, "informed": why, "runs": len(ids), "designs": len(designs), "files": checks}
    exposed |= designs

# (b) n1 pilot, 31 Oct: aggregate scores only (random split, 5 test runs of 53). Its run folder now holds
# 34 of the 53 runs; the random split is fixed by case_id, so the test designs among them are recoverable.
n1 = split_runs(index([os.path.expanduser("~/of_runs/full_h5mm_n1")], qc_ok=None), "random")["test"]
n1_designs = {str(r.case_id) for r in n1}
record["results_n1_random_2026-10-31.json"] = {
    "date": "2026-10-31", "informed": "first pilot (aggregate only)", "test_runs_recorded": 5,
    "test_designs_reconstructed": sorted(n1_designs),
    "note": "2 of the 5 test runs cannot be identified (their folders are no longer on disk)"}
exposed |= n1_designs

test = split_runs(index(DEFAULT_ROOTS, manifest=MAN), "ood_mode")["test"]
conf = sorted(r.run_id for r in test if r.run_id.split("_")[0] not in exposed)
meta = {r.run_id: r.meta for r in test}

# availability check: ids only
need = [f"{a}_{v}{s}" for a in ("fno", "unet") for v in ("hybrid", "hybrid_canon") for s in ("", "_s1", "_s2")]
have = {}
for f in glob.glob(os.path.expanduser("~/tb_verify/mljson/*_ood_mode.json")):
    for name, v in json.load(open(f))["results"].items():
        have[name] = {p["run_id"] for p in v["per_run"]}
base = json.load(open(H + "/results/ood_mode.json"))["results"]["ideal_stratified"]
have["ideal_stratified"] = {p["run_id"] for p in base["per_run"]}
avail = {n: (n in have and set(conf) <= have[n]) for n in need + ["ideal_stratified"]}

json.dump({"rule": "ood_mode test runs whose design appears in no evaluation made before the model freeze "
                   "(commit d42ce92, 2026-11-04 13:29), any split: recorded per-run scores, plus the "
                   "reconstructable membership of the one aggregate-only pre-freeze evaluation",
           "manifest": os.path.basename(MAN), "manifest_md5": hashlib.md5(open(MAN, "rb").read()).hexdigest(),
           "pre_freeze_evaluations": record, "post_freeze_not_counted": POST_FREEZE_NOT_COUNTED,
           "n_exposed_designs": len(exposed), "n_ood_mode_test": len(test),
           "n_runs": len(conf), "n_designs": len({c.split('_')[0] for c in conf}),
           "n_sst": sum(meta[c]["turbulence"] == "kOmegaSST" for c in conf),
           "n_Ri_below_5": sum(meta[c]["Ri_H"] < 5 for c in conf),
           "flagged_in_set": [c for c in conf if c in ("T0211_sst", "T0052_sst")],
           "score_availability_ids_only": avail,
           "run_ids": conf}, open(OUT + "/confirmation_set.json", "w"), indent=1)
print(len(conf), "runs,", len({c.split('_')[0] for c in conf}), "designs; exposed designs", len(exposed))
print(json.dumps(record, indent=1)); print("availability", avail)
