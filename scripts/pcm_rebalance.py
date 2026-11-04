#!/usr/bin/env python3
"""Spread pc4's queued PCM cases over the other machines as they free up (2026-11-04 ~20:30 Nepal,
Saxam: "distribute pc4 data for optimal use of time"). pc4 is the PCM bottleneck: 48/401 done,
cases run 1.45x their list estimate there (48 finished cases), ~50 h of queue on 30 slots.
Each queued case (longest first) goes to the slot that finishes it earliest:
  machine  slots  speed/job vs pc4  free from (h from now)       source of the numbers
  pc4      30     1.0               running cases' left_h        dashboard ~/tb_dash/status.json
  pc5      16     0.8 (guess)       --pc5-start (OpenFOAM in a container, needs Saxam's sudo once)
  laptop    8     0.61              tank tail + lou3d end         pcm_split: laptop 2.0 / pc4 3.3 per job vs lab
  lab      12     0.30              tank queue empty              lab 1.0 / 3.3 (lab runs pilot + tanks too)
  pc3      16     0.6               tank queue empty (Thu ~14:00) 2.9/3.3, x0.7 for 40 jobs on 28 threads
Moved cases get a placeholder on pc4 (DONE + MOVED_TO_<M>, built in a temp folder and renamed into
place, which fails if pc4 started the case meanwhile: it then stays on pc4). pcm_data.index skips
placeholders (no thermbench.h5). Destination lists: ~/thermbench/pcm_more_<m>.csv (same columns).
  pcm_rebalance.py [--apply] [--pc5-start H] [--no-pc5] [--only m1,m2]     (WSL on the laptop)"""
import csv, heapq, io, json, os, re, subprocess, sys, time

R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
apply = "--apply" in sys.argv
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
PC4_FACTOR = 1.45          # actual pc4 wall h / list estimate (48 finished cases, 2026-11-04)
M = {  # machine: [slots, speed vs pc4 per job, free from (h from now), ssh host]
    "pc4": [30, 1.0, None, "saxam@pc4"],
    "pc5": [16, 0.8, float(arg("--pc5-start", 2.0)), "pc5"],
    "laptop": [8, 0.61, 4.5, None],
    "lab": [12, 0.30, 8.0, "labpc"],
    "pc3": [16, 0.6, 18.0, "saxam@pc3"],
}
if "--no-pc5" in sys.argv:
    del M["pc5"]
if "--only" in sys.argv:
    keep = set(arg("--only", "").split(",")) | {"pc4"}
    M = {k: v for k, v in M.items() if k in keep}


def sh(host, cmd):
    argv = ["bash", "-c", cmd] if host is None else ["ssh", "-o", "BatchMode=yes", host, cmd]
    return subprocess.run(argv, capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL).stdout


rows = list(csv.DictReader(io.StringIO(sh("saxam@pc4", "cat ~/thermbench/pcm_full_pc4.csv"))))
fields = list(rows[0])
state = dict(l.split() for l in sh("saxam@pc4", "cd ~/of_runs/pcm_full/runs && for d in P*/; do d=${d%/}; "
             "if [ -f $d/DONE ]; then echo $d done; else echo $d started; fi; done").splitlines() if l.strip())
queued = [r for r in rows if r["case_id"] not in state]
dash = json.load(open(os.path.expanduser("~/tb_dash/status.json")))
left = sorted(r["left_h"] for r in dash["hosts"]["pc4"]["runs"] if r["batch"] == "runs")
print(f"pc4: {len(rows)} in list, {sum(v == 'done' for v in state.values())} done, "
      f"{sum(v == 'started' for v in state.values())} started, {len(queued)} queued; "
      f"dashboard {(time.time() - dash['updated']) / 60:.0f} min old")

h4 = lambda r: float(r["core_h_est"]) * PC4_FACTOR          # hours on a pc4 slot
heaps = {}
for m, (n, sp, start, _) in M.items():
    heaps[m] = (left + [0.0] * n)[:n] if m == "pc4" else [start] * n
    heapq.heapify(heaps[m])
base = list(heaps["pc4"])
plan = {m: [] for m in M}
for r in sorted(queued, key=lambda r: -h4(r)):
    fin, m = min((heaps[m][0] + h4(r) / M[m][1], m) for m in M)
    heapq.heapreplace(heaps[m], fin)
    plan[m].append(r)
for r in sorted(queued, key=lambda r: -h4(r)):        # pc4 alone, for comparison
    heapq.heapreplace(base, base[0] + h4(r))
now = time.time()
fmt = lambda h: time.strftime("%a %H:%M", time.gmtime(now + h * 3600 + 5.75 * 3600))
for m in M:
    print(f"  {m:6s} {len(plan[m]):3d} cases, {M[m][0]:2d} slots, last finish {fmt(max(heaps[m]))} Nepal"
          + (f"  (free from {fmt(M[m][2])})" if M[m][2] is not None else ""))
print(f"  all done {fmt(max(max(v) for v in heaps.values()))} Nepal; pc4 alone {fmt(max(base))} Nepal")
if not apply:
    print("dry run; --apply places the placeholders on pc4 and copies the lists")
    sys.exit()

for m in M:
    if m == "pc4" or not plan[m]:
        continue
    ids = [r["case_id"] for r in plan[m]]
    out = sh("saxam@pc4", f"""cd ~/of_runs/pcm_full/runs && ok=""; lost=""; for c in {' '.join(ids)}; do
  tmp=.tmp_$c; mkdir -p $tmp && touch $tmp/DONE $tmp/MOVED_TO_{m.upper()};
  if [ ! -e $c ] && mv -T $tmp $c 2>/dev/null && [ -f $c/MOVED_TO_{m.upper()} ]; then ok="$ok $c"; else rm -rf $tmp; lost="$lost $c"; fi;
done; echo "ok:$ok"; echo "lost:$lost" """)
    ok = set(re.search(r"ok:(.*)", out).group(1).split())
    lost = re.search(r"lost:(.*)", out).group(1).split()
    path = f"{R}/scripts/pcm_more_{m}.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(r for r in plan[m] if r["case_id"] in ok)
    host = M[m][3]
    if host is None:
        subprocess.run(["cp", path, os.path.expanduser("~/thermbench/")], check=True)
    else:
        subprocess.run(["ssh", "-o", "BatchMode=yes", host, "mkdir -p ~/thermbench"], check=True, stdin=subprocess.DEVNULL)
        subprocess.run(["scp", "-q", path, f"{host}:thermbench/"], check=True)
    print(f"{m}: {len(ok)} cases moved (placeholders on pc4), list pcm_more_{m}.csv copied; "
          f"stayed on pc4 (started meanwhile): {' '.join(lost) or 'none'}")
