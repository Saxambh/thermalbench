"""Second PCM split (2026-11-03 ~13:15 UTC, Saxam: use lab, pc3 and pc4 fully). Re-assigns the
99 cases of the first split that had not started (pcm_full_pc3.csv + pcm_full_laptop.csv; the
first split's lists are kept in split_v1_2026-11-03/). pc4 keeps its 401 cases and gets more
after them (its list grows: the running batch read its list at start and is not affected).
  pc3     24 jobs, from now (alongside its last tank runs)      speed vs lab ~2.2
  laptop  16 jobs, from its tank queue emptying (~Wed 04:45)    ~1.7 (3D case + tank tail)
  lab     16 jobs, from its tank queue emptying (~Wed 22:30)    ~0.8 (pilot + tank tail)
  pc4     30 jobs, after its 401 (~Thu 11:00), cases <= 8 h     3.3
Times in hours after Wed 4 Nov 00:30 UTC; cost per case from pcm_cost_pilot (lab hours)."""
import contextlib, csv, heapq, importlib.util, io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cost", os.path.join(HERE, "pcm_cost_pilot.py"))
cost = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    sys.argv = ["x", os.path.join(HERE, "pcm_full.csv")]; spec.loader.exec_module(cost)
V1 = os.path.join(HERE, "split_v1_2026-11-03")
pool = list(csv.DictReader(open(f"{V1}/pcm_full_pc3.csv"))) + list(csv.DictReader(open(f"{V1}/pcm_full_laptop.csv")))
pc4_v1 = list(csv.DictReader(open(f"{V1}/pcm_full_pc4.csv")))
M = {"pc3": (24, 2.2, -11.25, None), "laptop": (16, 1.7, 4.2, None), "lab": (16, 0.8, 21.9, None), "pc4": (30, 3.3, 34.5, 8.0)}
heaps = {m: [st] * n for m, (n, sp, st, cap) in M.items()}
assign = {m: [] for m in M}
for r in sorted(pool, key=lambda r: -cost.wall_h(r)):
    best = None
    for m, (n, sp, st, cap) in M.items():
        d = cost.wall_h(r) / sp
        if cap and d > cap:
            continue
        fin = heaps[m][0] + d
        if best is None or fin < best[0]:
            best = (fin, m, d)
    fin, m, d = best
    heapq.heapreplace(heaps[m], fin); assign[m].append((r, d))
fields = list(pool[0].keys())
for m, lst in assign.items():
    rows = [r | {"core_h_est": round(d, 1)} for r, d in lst]
    if m == "pc4":
        rows = pc4_v1 + rows
    with open(os.path.join(HERE, f"pcm_full_{m}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    end = max(heaps[m]) if lst else M[m][2]
    print(f"{m:7s} +{len(lst):3d} new cases ({len(rows)} in list), {sum(d for _, d in lst):5.0f} own h, "
          f"longest {max([d for _, d in lst] or [0]):4.1f} h, start {M[m][2]:+.1f} h, done {end:+.0f} h")
print(f"all PCM done about {max(max(h) for m, h in heaps.items() if assign[m]):+.0f} h after Wed 00:30 UTC")
