"""Freeze the list of PCM runs used for training and evaluation (PCM counterpart of freeze_manifest.py).

  python pcm_freeze_manifest.py [--out manifest_pcm.json] [--roots ...] [--expect 500]
One entry per usable run: DONE + thermbench.h5, no MOVED_TO_* placeholder, pcm_qc.py verdict
(qc.json "status") OK or WARN, and made with the final solver set-up (case dir system/fvSolution with
p_rghFinal relTol 0, option A 2026-11-04; first-round runs are kept apart in runs_v1_relTol1e-3 and
never listed). Entry: run_id, root, QC status, h5 size and md5. "family": "pcm" tells
check_data.py which roots to search. Every PCM split then draws from this list only
(pcm_data.index(..., manifest=path)), so all models see exactly the same runs.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import time

from pcm_data import DEFAULT_ROOTS, index

HERE = os.path.dirname(os.path.abspath(__file__))


def md5(path, block=1 << 22):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()


def fixed(path):
    """True if the case was solved with p_rghFinal relTol 0. The synced copies on the laptop hold
    only light files (no system/), so their origin batch (runs, not runs_v1_*) is the evidence there."""
    f = os.path.join(path, "system", "fvSolution")
    if os.path.exists(f):
        m = re.search(r"p_rghFinal\s*\{[^}]*?relTol\s+([0-9.eE+-]+)\s*;", open(f).read(), re.S)
        return bool(m) and float(m.group(1)) == 0.0
    return "v1_relTol" not in path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", default=DEFAULT_ROOTS)
    ap.add_argument("--out", default=os.path.join(HERE, "manifest_pcm.json"))
    ap.add_argument("--expect", type=int, default=500, help="design size, for the summary only")
    a = ap.parse_args()
    runs = index(a.roots)
    entries, skipped = [], {"no_qc": [], "fail": [], "old_solver": []}
    for r in runs:
        q = os.path.join(r.path, "qc.json")
        st = json.load(open(q)).get("status", "none") if os.path.exists(q) else "none"
        if not fixed(r.path):
            skipped["old_solver"].append(r.run_id); continue
        if st == "none":
            skipped["no_qc"].append(r.run_id)
        if st == "FAIL":
            skipped["fail"].append(r.run_id); continue
        h5 = os.path.join(r.path, "thermbench.h5")
        entries.append({"run_id": r.run_id, "case_id": r.case_id, "root": os.path.dirname(r.path), "qc": st,
                        "h5_MB": round(os.path.getsize(h5) / 1e6, 2), "h5_md5": md5(h5)})
    body = {"family": "pcm", "created_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
            "n_runs": len(entries), "n_cases": len({e["case_id"] for e in entries}), "roots": a.roots,
            "solver": "make_pcm_case.py with p_rghFinal relTol 0, maxIter 200 (option A, 2026-11-04)",
            "excluded": {"qc_fail": sorted(skipped["fail"]), "old_solver": sorted(skipped["old_solver"])},
            "runs": entries}
    text = json.dumps(body, indent=1)
    open(a.out, "w").write(text)
    print(f"{len(entries)} PCM runs of {a.expect} -> {a.out} (manifest md5 {hashlib.md5(text.encode()).hexdigest()}); "
          f"QC FAIL left out: {len(skipped['fail'])}, old solver left out: {len(skipped['old_solver'])}")
    if skipped["no_qc"]:
        print(f"warning: {len(skipped['no_qc'])} runs have no QC verdict yet: {skipped['no_qc'][:10]}")


if __name__ == "__main__":
    main()
