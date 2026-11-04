#!/usr/bin/env python3
"""Third PCM split (2026-11-04 ~22:00 Nepal, Saxam: option A). Every one of the 500 full-design
cases is (re)run with the pressure fix in make_pcm_case.py (p_rghFinal relTol 0, maxIter 200,
~1.25x run time); the first-round runs are kept aside as runs_v1_relTol1e-3. All 500 cases go,
longest first, to the stream that finishes them earliest. Cost per case on a pc4 slot =
pcm_cost_pilot wall_h / 3.3 (pc4 vs lab per job) x 1.45 (measured on pc4) x 1.25 (fix).
  stream         list                        jobs speed/job vs pc4  starts (h from now)
  pc4            pcm_full_pc4.csv            30   1.0               0, cases <= 10 h only (no backup power)
  pc5            pcm_more_pc5.csv            16   0.8 (guess)       0 (container ofbox)
  laptop         pcm_full_laptop.csv         16   0.61              0
  laptop+        pcm_more_laptop.csv          8   0.61              4.5 (tank tail + lou3d)
  pc3            pcm_full_pc3.csv            24   0.6               0
  pc3+           pcm_more_pc3.csv            16   0.6               18 (tank runs)
  lab            pcm_more_lab.csv            12   0.3               8 (tank queue)
The lists before this split are kept in split_v2_2026-11-04/. Writes the lists here; deploying
them is done by the caller.   pcm_split3.py [--write]"""
import contextlib, csv, importlib.util, io, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cost", os.path.join(HERE, "pcm_cost_pilot.py"))
cost = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    sys.argv = ["x", os.path.join(HERE, "pcm_full.csv")] + sys.argv[1:]; spec.loader.exec_module(cost)
rows = list(csv.DictReader(open(os.path.join(HERE, "pcm_full.csv"))))
fields = list(rows[0])
h = lambda r: cost.wall_h(r) / 3.3 * 1.45 * 1.25
S = [("pc4", "pcm_full_pc4.csv", 30, 1.0, 0, 10.0), ("pc5", "pcm_more_pc5.csv", 16, 0.8, 0, None),
     ("laptop", "pcm_full_laptop.csv", 16, 0.61, 0, None), ("laptop+", "pcm_more_laptop.csv", 8, 0.61, 4.5, None),
     ("pc3", "pcm_full_pc3.csv", 24, 0.6, 0, None), ("pc3+", "pcm_more_pc3.csv", 16, 0.6, 18, None),
     ("lab", "pcm_more_lab.csv", 12, 0.3, 8, None)]
slots = [[t0, k] for k, (_, _, n, _, t0, _) in enumerate(S) for _ in range(n)]
out = {k: [] for k in range(len(S))}
for r in sorted(rows, key=lambda r: -h(r)):
    ok = [s for s in slots if S[s[1]][5] is None or h(r) <= S[s[1]][5]]
    s = min(ok, key=lambda s: s[0] + h(r) / S[s[1]][3])
    d = h(r) / S[s[1]][3]
    s[0] += d
    out[s[1]].append(r | {"core_h_est": round(d, 1)})
for k, (name, f, n, sp, t0, cap) in enumerate(S):
    end = max(s[0] for s in slots if s[1] == k)
    print(f"  {name:8s} {f:22s} {len(out[k]):3d} cases, {n:2d} jobs, last finish +{end:.0f} h")
print(f"  all 500 done +{max(s[0] for s in slots):.0f} h")
if "--write" in sys.argv:
    keep = os.path.join(HERE, "split_v2_2026-11-04"); os.makedirs(keep, exist_ok=True)
    for f in [x for x in os.listdir(HERE) if x.startswith(("pcm_full_", "pcm_more_")) and x.endswith(".csv")]:
        shutil.copy2(os.path.join(HERE, f), keep)
    for k, (name, f, *_ ) in enumerate(S):
        with open(os.path.join(HERE, f), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(out[k])
    with open(os.path.join(HERE, "pcm_full_lab.csv"), "w", newline="") as fh:   # lab runs pcm_more_lab only
        csv.DictWriter(fh, fieldnames=fields).writeheader()
    print("lists written; old ones in", keep)
