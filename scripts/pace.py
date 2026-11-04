#!/usr/bin/env python3
"""Batch pace vs plan: share of the design's predicted cost done (finished + running fraction).
Usage: pace.py <design.csv> <batch_dir>"""
import csv
import os
import re
import subprocess
import sys

design, batch = sys.argv[1], os.path.expanduser(sys.argv[2])
rows = list(csv.DictReader(open(design)))
cols = rows[0].keys()
idcol = "run_id"
# split_n2.py cost model (laptop-seconds of one run)
import numpy as np
c = np.array([3.129, 0.523, 1.329, 0.255])
cost = {r[idcol]: 1.75 * np.exp(c @ [1, np.log(float(r["u_in"])), np.log(float(r["W"])), r["turb"] != "laminar"]) * float(r["end_s"]) for r in rows}
print("runs:", len(rows), f"predicted total {sum(cost.values()) / 3600:.0f} laptop-run-hours")
tot = sum(cost.values())
done = run_part = 0.0
nd = 0
order = [r[idcol] for r in rows]
for rid, c in cost.items():
    d = os.path.join(batch, rid)
    if not os.path.isdir(d):
        continue
    if os.path.exists(f"{d}/DONE"):
        done += c; nd += 1
    elif os.path.exists(f"{d}/log.solver"):
        tl = subprocess.run(f"grep '^Time = ' {d}/log.solver | tail -1", shell=True, capture_output=True, text=True).stdout.split()
        try:
            import json
            end = json.load(open(f"{d}/case.json")).get("end_time_s")
            run_part += c * float(tl[2]) / float(end)
        except Exception:
            pass
print(f"finished {nd}, predicted-cost share done {100 * done / tot:.1f} % + running {100 * run_part / tot:.1f} %")
print("first 5 in order costs:", [round(cost[i], 2) for i in order[:5]], "last 5:", [round(cost[i], 2) for i in order[-5:]])
