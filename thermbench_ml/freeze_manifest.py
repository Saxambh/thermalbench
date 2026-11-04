"""Freeze the list of runs used for training and evaluation.

  python freeze_manifest.py [--out manifest_full_h5mm.json] [--roots ...]
Writes one entry per usable run (DONE, thermbench.h5, QC verdict OK or WARN, no MOVED_TO_*
placeholder): run_id, case_id, machine root, QC verdict, h5 size and md5. Every split
then draws from this list only (data.index(..., manifest=path)), so all models see exactly
the same runs, and the paper can cite the manifest's md5.
"""
import argparse
import csv
import hashlib
import json
import os
import time

from data import DEFAULT_ROOTS, index

HERE = os.path.dirname(os.path.abspath(__file__))


def md5(path, block=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", default=DEFAULT_ROOTS)
    ap.add_argument("--out", default=os.path.join(HERE, "manifest_full_h5mm.json"))
    a = ap.parse_args()
    runs = index(a.roots)
    # Design rule (Saxam, 2026-11-04, decided before any final training): drop discharge runs that
    # start partly charged with the hot layer entirely above the outlet (initial thermocline yi
    # above the outlet's top edge H - off). Cold water then flows straight from inlet to outlet,
    # under 1 % of the stored energy leaves, and the QC energy check (error / exchanged energy)
    # cannot judge them (T0765: 0.034 % of stored energy, shown as 4.1-4.7 %). Both turbulence
    # variants of such a design point go. Affects 4 of 1,217 runs: T0765_lam, T0765_sst, T0882_lam, T0191_sst.
    design = list(csv.DictReader(open(os.path.join(HERE, "..", "design_v2_full.csv"))))
    trapped = {d["case_id"] for d in design if d["mode"] == "discharge" and d["yi"]
               and float(d["yi"]) > float(d["H"]) - float(d["off"])}
    excluded = sorted(r.run_id for r in runs if r.case_id in trapped)
    runs = [r for r in runs if r.case_id not in trapped]
    entries = []
    for r in runs:
        h5 = os.path.join(r.path, "thermbench.h5")
        entries.append({"run_id": r.run_id, "case_id": r.case_id, "root": os.path.dirname(r.path),
                        "qc": r.qc.get("verdict", "none"), "h5_MB": round(os.path.getsize(h5) / 1e6, 2),
                        "h5_md5": md5(h5)})
    body = {"created_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()), "n_runs": len(entries),
            "n_cases": len({e["case_id"] for e in entries}), "roots": a.roots,
            "excluded_by_design_rule": {"rule": "discharge, initial hot layer above the outlet (yi > H - off)",
                                        "cases": sorted(trapped), "runs_present": excluded},
            "runs": entries}
    text = json.dumps(body, indent=1)
    open(a.out, "w").write(text)
    print(f"{len(entries)} runs ({body['n_cases']} design points) -> {a.out} "
          f"(manifest md5 {hashlib.md5(text.encode()).hexdigest()})")
    no_qc = [e["run_id"] for e in entries if e["qc"] == "none"]
    if no_qc:
        print(f"warning: {len(no_qc)} runs have no QC verdict yet: {no_qc[:10]}")


if __name__ == "__main__":
    main()
