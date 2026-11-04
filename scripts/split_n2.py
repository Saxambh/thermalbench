# Fresh split of the full 5 mm batch for the nOuterCorrectors=2 rerun, by predicted cost and
# measured machine throughput (laptop 8 jobs at 1.86x per run, lab 14 jobs at 3.6x).
import csv, numpy as np
R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
c = np.array([3.129, 0.523, 1.329, 0.255])
N2 = 1.75                                   # measured wall-time factor of 2 outer correctors
cost = lambda d: N2 * np.exp(c @ [1, np.log(float(d["u_in"])), np.log(float(d["W"])), d["turb"] != "laminar"]) * float(d["end_s"])
rows = list(csv.DictReader(open(f"{R}/design_v2_full.csv")))
rate = {"laptop": 8 / 1.86, "lab": 14 / 3.6}  # laptop-run-equivalents in parallel
load = {k: 0.0 for k in rate}; assign = {k: set() for k in rate}
for r in sorted(rows, key=cost, reverse=True):
    m = min(rate, key=lambda k: (load[k] + cost(r)) / rate[k])
    assign[m].add(r["run_id"]); load[m] += cost(r)
for m in rate:
    with open(f"{R}/design_v2_full_{m}_n2.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader()
        w.writerows(r for r in rows if r["run_id"] in assign[m])
    print(f"{m}: {len(assign[m])} runs, ~{load[m] / rate[m] / 3600:.0f} h")
assert not assign["laptop"] & assign["lab"] and sum(map(len, assign.values())) == len(rows)
