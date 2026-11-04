"""Split pcm_full.csv across the three machines (2026-11-03), each starting when its tank batch
ends. Cost per case from pcm_cost_pilot (lab-hours); machine speed per job relative to the lab,
from the same 5-fin test case on each machine next to its tank runs (pc3 10.5, laptop 15.2,
lab 30.1 us per step per cell; pc4 9.1 with 30 jobs at once). List scheduling, longest case
first, onto the machine where it would finish first. pc4 (added 2026-11-03, no backup power)
only takes cases of at most PC4_MAX_H of its own hours, so a power cut loses little. Writes pcm_full_<machine>.csv with core_h_est replaced by the recalibrated estimate in
that machine's own hours (pcm_batch.sh runs the largest core_h_est first).
    python pcm_split.py"""
import csv, heapq, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util, sys, io, contextlib
spec = importlib.util.spec_from_file_location("cost", os.path.join(HERE, "pcm_cost_pilot.py"))
PC4_MAX_H = 8.0
MACHINES = {            # jobs, speed vs lab, start (h after Wed 4 Nov 00:30 UTC)
    "pc4": (30, 3.3, -16.6),          # starts now, Tue 3 Nov ~07:55 UTC
    "pc3": (16, 2.9, 0.0),
    "laptop": (16, 2.0, 9.5),
    "lab": (12, 1.0, 37.5),
}
src = os.path.join(HERE, "pcm_full.csv")
rows = list(csv.DictReader(open(src)))
cost = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    sys.argv = ["x", src]; spec.loader.exec_module(cost)
w = {r["case_id"]: cost.wall_h(r) for r in rows}
heaps = {m: [st] * n for m, (n, sp, st) in MACHINES.items()}
assign = {m: [] for m in MACHINES}
for r in sorted(rows, key=lambda r: -w[r["case_id"]]):
    best = None
    for m, (n, sp, st) in MACHINES.items():
        d = w[r["case_id"]] / sp
        if m == "pc4" and d > PC4_MAX_H:
            continue
        fin = heaps[m][0] + d
        if best is None or fin < best[0]:
            best = (fin, m, d)
    fin, m, d = best
    heapq.heapreplace(heaps[m], fin)
    assign[m].append((r, d))
end = {m: max(h) if assign[m] else MACHINES[m][2] for m, h in heaps.items()}
for m, lst in assign.items():
    out = os.path.join(HERE, f"pcm_full_{m}.csv")
    with open(out, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=rows[0].keys()); wr.writeheader()
        for r, d in lst: wr.writerow(r | {"core_h_est": round(d, 1)})
    print(f"{m:7s} {len(lst):3d} cases, {sum(d for _, d in lst):6.0f} own core-h, "
          f"longest {max([d for _, d in lst] or [0]):5.1f} h, start +{MACHINES[m][2]:.1f} h, done +{end[m]:.0f} h -> {os.path.basename(out)}")
print(f"all done about +{max(end.values()):.0f} h after Wed 00:30 UTC ({max(end.values())/24:.1f} days)")
