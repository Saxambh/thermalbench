#!/usr/bin/env python3
"""Run a ThermalStorageBench design CSV: generate, mesh, solve, export, then delete the raw
time directories once the export is verified. Restartable: finished runs are skipped.

Usage: run_batch.py <design.csv> <out_dir> [--jobs 16] [--only P00_lam,P03_sst]
                    [--dry-run] [--keep-raw]
Status: <out_dir>/batch_status.csv (one line per finished or failed run).
"""
import argparse
import csv
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_design  # noqa: E402

FOAM_ENV = "unset LD_LIBRARY_PATH; source /usr/lib/openfoam/openfoam2606/etc/bashrc; "


def sh(cmd, cwd, log):
    with open(log, "w") as f:
        return subprocess.run(["bash", "-c", FOAM_ENV + cmd], cwd=cwd, stdout=f,
                              stderr=subprocess.STDOUT).returncode


def run_one(row, out, dry, keep_raw):
    rid = row["run_id"]
    case = os.path.join(out, rid)
    if os.path.exists(os.path.join(case, "DONE")):
        return rid, "skipped", 0.0, ""
    if os.path.exists(case):
        shutil.rmtree(case)  # unfinished earlier attempt
    t0 = time.time()
    args = " ".join(shlex.quote(x) for x in make_design.args_for(row))
    gen = shlex.quote(os.path.join(HERE, "make_tank_case.py"))
    if sh(f"python3 {gen} {shlex.quote(case)} {args}", out, f"{case}.gen.log") != 0:
        return rid, "generator_failed", 0.0, ""
    if sh("blockMesh", case, f"{case}/log.blockMesh") != 0:
        return rid, "blockMesh_failed", 0.0, ""
    if dry:
        return rid, "dry_ok", time.time() - t0, ""
    if sh("buoyantPimpleFoam", case, f"{case}/log.solver") != 0:
        return rid, "solver_failed", time.time() - t0, ""
    exp = shlex.quote(os.path.join(HERE, "export_case.py"))
    if sh(f"python3 {exp} {shlex.quote(case)}", case, f"{case}/log.export") != 0:
        return rid, "export_failed", time.time() - t0, ""
    m = json.load(open(f"{case}/metrics.json"))
    snaps = len(m["snapshots"])
    end_ok = abs(m["snapshots"][-1]["t_s"] - m["case"]["end_time_s"]) < 1e-3 * m["case"]["end_time_s"]
    if not end_ok or snaps < 2:
        return rid, "incomplete", time.time() - t0, f"snaps={snaps}"
    if not keep_raw:  # export verified: drop raw time directories (keep 0/, logs, metadata)
        for d in os.listdir(case):
            try:
                if float(d) > 0:
                    shutil.rmtree(os.path.join(case, d))
            except ValueError:
                pass
    open(os.path.join(case, "DONE"), "w").close()
    return rid, "ok", time.time() - t0, f"snaps={snaps} MB={m['file_MB']:.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("design")
    ap.add_argument("out")
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--only", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-raw", action="store_true")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.design)))
    if a.only:
        keep = set(a.only.split(","))
        rows = [r for r in rows if r["run_id"] in keep]
    # longest runs first, so the batch does not end waiting on one slow case
    rows.sort(key=lambda r: -float(r["end_s"]) * float(r["W"]) / float(r["s"]))
    os.makedirs(a.out, exist_ok=True)
    status = os.path.join(a.out, "batch_status.csv")
    new = not os.path.exists(status)
    print(f"{len(rows)} runs, {a.jobs} at a time -> {a.out}", flush=True)
    with open(status, "a") as st, ThreadPoolExecutor(a.jobs) as pool:
        if new:
            st.write("run_id,status,wall_s,note,finished\n")
        futs = [pool.submit(run_one, r, a.out, a.dry_run, a.keep_raw) for r in rows]
        for fut in as_completed(futs):  # report each run as soon as it finishes
            rid, res, wall, note = fut.result()
            st.write(f"{rid},{res},{wall:.0f},{note},{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            st.flush()
            print(f"{rid:14s} {res:18s} {wall:7.0f} s  {note}", flush=True)


if __name__ == "__main__":
    main()
