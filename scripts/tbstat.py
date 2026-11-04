#!/usr/bin/env python3
"""ThermBench progress on this machine: every OpenFOAM run under ~/of_runs that is
running now (log written in the last 5 min) plus finished/failed counts per batch."""
import csv
import glob
import os
import re
import socket
import time

ROOT = os.path.expanduser("~/of_runs")
now = time.time()


def tail(path, n=40000):
    with open(path, "rb") as f:
        f.seek(max(0, os.path.getsize(path) - n))
        return f.read().decode(errors="ignore")


def end_time(case):
    try:
        m = re.search(r"^endTime\s+([0-9.eE+-]+);", open(f"{case}/system/controlDict").read(), re.M)
        return float(m.group(1))
    except (OSError, AttributeError):
        return None


def fmt(sec):
    sec = int(sec)
    return f"{sec // 3600}h{sec % 3600 // 60:02d}m" if sec >= 3600 else f"{sec // 60}m{sec % 60:02d}s"


load = open("/proc/loadavg").read().split()[0]
mem = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo")}
print(f"=== {socket.gethostname()}  load {load} / {os.cpu_count()} threads  "
      f"memory free {mem['MemAvailable'] / 1e6:.1f} of {mem['MemTotal'] / 1e6:.1f} GB")
print(f"{'batch/run':34s} {'progress':>9s} {'sim time':>17s} {'elapsed':>8s} {'left':>8s}")
batches = {}
for log in sorted(glob.glob(f"{ROOT}/*/*/log.solver")):
    case = os.path.dirname(log)
    batch, run = case.split("/")[-2:]
    b = batches.setdefault(batch, {"done": 0, "running": 0, "stalled": 0})
    if os.path.exists(f"{case}/DONE"):
        b["done"] += 1
        continue
    age = now - os.path.getmtime(log)
    txt = tail(log)
    if "End\n" in txt[-200:] and "FOAM FATAL" not in txt:
        b["done"] += 1
        continue
    if age > 300:
        b["stalled"] += 1
        continue
    b["running"] += 1
    ts = re.findall(r"^Time = ([0-9.eE+-]+)", txt, re.M)
    cl = re.findall(r"ClockTime = ([0-9.]+) s", txt)
    T = end_time(case)
    if not ts or not cl or not T:
        print(f"{batch + '/' + run:34s} {'starting':>9s}")
        continue
    t, c = float(ts[-1]), float(cl[-1])
    left = (T - t) * c / t if t > 0 else 0
    print(f"{batch + '/' + run:34s} {100 * t / T:8.1f}% {t:8.1f}/{T:<8.6g} {fmt(c):>8s} {fmt(left):>8s}")
for batch, b in batches.items():
    st = f"{ROOT}/{batch}/batch_status.csv"
    # show batches that are active, or real batches (made by run_batch.py) from the last 3 days
    if b["running"] or (os.path.exists(st) and now - os.path.getmtime(st) < 3 * 86400):
        fails = 0
        if os.path.exists(st):
            fails = sum(1 for l in open(st) if "_failed" in l and "generator_failed" not in l
                        or ",incomplete," in l)
        print(f"  batch {batch}: {b['done']} finished, {b['running']} running, "
              f"{b['stalled']} stopped/waiting" + (f", {fails} FAILED" if fails else ""))
        qc = f"{ROOT}/{batch}/qc_report.csv"
        if os.path.exists(qc):
            v = [r["verdict"] for r in csv.DictReader(open(qc))]
            print(f"    quality check ({fmt(now - os.path.getmtime(qc))} ago): {len(v)} checked, "
                  f"{v.count('OK')} OK, {v.count('WARN')} warn, {v.count('FAIL')} FAIL")
