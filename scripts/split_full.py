# Split design_v2_full.csv between laptop (4 jobs) and lab (14 jobs) by predicted cost.
# Cost model fitted on finished runs: wall/sim-second ~ u_in^b * W^c * (turbulent factor).
import csv, os, numpy as np
R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
rows = list(csv.DictReader(open(f"{R}/design_v2_full.csv")))
design = {r["run_id"]: r for r in rows}
pil = {r["run_id"]: r for r in csv.DictReader(open(f"{R}/design_v2_pilot.csv"))}
X = []
for B, D in (("full_h5mm", design), ("pilot_v2", pil)):
    for r in csv.DictReader(open(os.path.expanduser(f"~/of_runs/{B}/batch_status.csv"))):
        if r["status"] == "ok" and r["run_id"] in D:
            d = D[r["run_id"]]
            X.append((float(d["u_in"]), float(d["W"]), d["turb"] != "laminar", float(d["end_s"]), float(r["wall_s"])))
u, W, tb, e, w = map(np.array, zip(*X))
A = np.c_[np.ones(len(u)), np.log(u), np.log(W), tb]
c, *_ = np.linalg.lstsq(A, np.log(w/e), rcond=None)
print("fit:", c.round(3), "median factor error", np.median(np.exp(np.abs(A@c - np.log(w/e)))).round(2))
cost = lambda d: np.exp(c @ [1, np.log(float(d["u_in"])), np.log(float(d["W"])), d["turb"] != "laminar"]) * float(d["end_s"])
# laptop keeps everything it has finished or is running now
started = {r for r in os.listdir(os.path.expanduser("~/of_runs/full_h5mm")) if r in design}
cap = {"laptop": 4, "lab": 14}
load = {"laptop": 0.0, "lab": 0.0}
assign = {"laptop": [], "lab": []}
for rid in started:
    assign["laptop"].append(rid)
    if not os.path.exists(os.path.expanduser(f"~/of_runs/full_h5mm/{rid}/DONE")):
        load["laptop"] += cost(design[rid])
for r in sorted((r for r in rows if r["run_id"] not in started), key=cost, reverse=True):
    m = min(cap, key=lambda k: (load[k] + cost(r)) / cap[k])
    assign[m].append(r["run_id"]); load[m] += cost(r)
for m in cap:
    keep = set(assign[m])
    with open(f"{R}/design_v2_full_{m}.csv", "w", newline="") as f:
        wri = csv.DictWriter(f, fieldnames=rows[0].keys()); wri.writeheader()
        wri.writerows(r for r in rows if r["run_id"] in keep)
    print(f"{m}: {len(keep)} runs, ~{load[m]/3600:.0f} core-h left, ~{load[m]/3600/cap[m]:.0f} h wall at {cap[m]} jobs")
assert not set(assign["laptop"]) & set(assign["lab"]) and len(assign["laptop"]) + len(assign["lab"]) == len(rows)
