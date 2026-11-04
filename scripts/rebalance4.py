#!/usr/bin/env python3
"""Move queued tank runs to the idle lab (2026-11-04, Saxam approved).
T0449_lam is done and the lab's own lists are nearly empty, while the laptop's extra list
(laptopx) and pc3 still have long queues. Queued runs of both lists go into one pool; each run
(longest first) goes to the stream that would finish it earliest:
  laptopx  laptop, 8 slots, keeps the rest of its list
  pc3      pc3, 16 slots, keeps the rest of its list
  laby     a new lab batch, 16 slots, list ~/thermbench/design_v2_full_laby_n2.csv, run folders in
           the lab's ~/of_runs/full_h5mm_x (already gathered, distinct run ids from labx)
Run lengths come from each machine's own finished runs; running runs keep their slot until their
projected end. Moved runs get a placeholder in the source folder (DONE + MOVED_TO_LABY, built in a
temp folder and renamed into place, which fails if the source batch started that run meanwhile;
it then stays where it is). Runs on laptop/pc3 are never stopped.
Usage: rebalance4.py [--apply] [--dest laby|labz] [--slots N]     (run in WSL on the laptop)
  --dest labz --slots 8: a second lab batch added 2026-11-04 ~14:00 Nepal (Saxam: give pc3 runs to the lab)
"""
import csv, io, os, re, subprocess, sys, time
import numpy as np

R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
apply = "--apply" in sys.argv
now, H = time.time(), 3600.0
SRC = {  # stream: (host or None for local, list path on that host, run folder on that host, slots)
    "laptopx": (None, f"{R}/design_v2_full_laptopx_n2.csv", "~/of_runs/full_h5mm_x", 8),
    "pc3": ("saxam@pc3", "~/thermbench/design_v2_full_pc3_n2.csv", "~/of_runs/full_h5mm", 16),
}
DEST = sys.argv[sys.argv.index("--dest") + 1] if "--dest" in sys.argv else "laby"
LABY_SLOTS = int(sys.argv[sys.argv.index("--slots") + 1]) if "--slots" in sys.argv else 16
LAB_SLOW = 1.15 if DEST != "laby" else 1.0   # extra lab batch: lab threads then fully used


def sh(host, cmd):
    argv = ["bash", "-c", cmd] if host is None else ["ssh", "-o", "BatchMode=yes", host, cmd]
    return subprocess.run(argv, capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL).stdout


design = {r["run_id"]: r for r in csv.DictReader(open(f"{R}/design_v2_full.csv"))}


def feats(r):
    return [1.0, np.log(float(r["end_s"])), np.log(float(r["W"])), np.log(float(r["u_in"])),
            np.log(float(r["s"])), float(r["turb"] != "laminar")]


def model(status_text):
    X, y = [], []
    for l in csv.DictReader(io.StringIO(status_text)):
        if l.get("status") == "ok" and l["run_id"] in design and float(l["wall_s"]) > 60:
            X.append(feats(design[l["run_id"]])); y.append(np.log(float(l["wall_s"])))
    X, y = np.array(X), np.array(y)
    c = np.linalg.lstsq(X, y, rcond=None)[0]
    v = (y - X @ c).var()
    return (lambda r: float(np.exp(np.array(feats(r)) @ c + 0.5 * v))), len(y)


STATUS = "cat ~/of_runs/full_h5mm/batch_status.csv; tail -n +2 ~/of_runs/full_h5mm_x/batch_status.csv 2>/dev/null; true"
pred = {}
pred["laptopx"], n1 = model(sh(None, STATUS))
pred["pc3"], n2 = model(sh("saxam@pc3", STATUS))
lab_pred, n3 = model(sh("labpc", STATUS))
pred["laby"] = lambda r: lab_pred(r) * LAB_SLOW
print(f"run-length models from {n1} laptop, {n2} pc3, {n3} lab runs")

LIST = r"""cd {d} && now=$(date +%s); for x in T*/; do x=${{x%/}};
  if ls $x | grep -q MOVED; then echo "$x moved";
  elif [ -f $x/DONE ]; then echo "$x done";
  elif [ -f $x/log.solver ]; then t=$(tail -c 20000 $x/log.solver | grep "^Time = " | tail -1 | awk '{{print $3}}');
    c=$(tail -c 20000 $x/log.solver | grep -o "ClockTime = [0-9.]*" | tail -1 | awk '{{print $3}}');
    echo "$x run ${{t:-0}} ${{c:-0}}";
  else echo "$x other"; fi; done"""

rows, state, slots, fields = {}, {}, {}, None
for s, (host, lst, d, n) in SRC.items():
    text = open(lst).read() if host is None else sh(host, f"cat {lst}")
    rows[s] = list(csv.DictReader(io.StringIO(text)))
    fields = fields or list(rows[s][0])
    state[s] = {l.split()[0]: l.split()[1:] for l in sh(host, LIST.format(d=d)).splitlines() if l.strip()}
    ends = []
    for rid, st in state[s].items():
        if st[0] == "run" and rid in design:
            r, t, clock = design[rid], float(st[1]), float(st[2])
            frac = t / float(r["end_s"])
            left = (float(r["end_s"]) - t) * clock / t if t > 0 and frac > 0.1 else pred[s](r) * (1 - frac)
            ends.append(now + left)
    slots[s] = sorted(ends)[:n] + [now] * max(0, n - len(ends))
slots["laby"] = [now] * LABY_SLOTS

pool = []
for s in SRC:
    q = [r for r in rows[s] if r["run_id"] not in state[s]]
    print(f"{s}: {len(rows[s])} in list, {sum(v[0] == 'run' for v in state[s].values())} running, {len(q)} queued")
    pool += [(r, s) for r in q]
pool.sort(key=lambda x: -float(x[0]["end_s"]) * float(x[0]["W"]) / float(x[0]["s"]))   # run_batch order

before = {s: list(v) for s, v in slots.items()}
plan = {s: [] for s in slots}
for r, src in pool:
    best = None
    for s in (src, "laby"):          # a run stays home or moves to the lab, never laptop <-> pc3
        k = int(np.argmin(slots[s]))
        end = slots[s][k] + pred[s](r)
        if best is None or end < best[0]:
            best = (end, s, k)
    end, s, k = best
    slots[s][k] = end
    plan[s].append((r, src))

# projection without the move, for comparison
for s in SRC:
    b = before[s]
    for r in [r for r, src in pool if src == s]:
        k = int(np.argmin(b)); b[k] += pred[s](r)
fmt = lambda t: time.strftime("%a %d %b %H:%M", time.gmtime(t))
for s in slots:
    d = [pred[s](r) / H for r, _ in plan[s]]
    moved_from = {src: sum(1 for _, x in plan[s] if x == src) for src in SRC} if s == "laby" else {}
    print(f"  {s:8s}: {len(plan[s]):3d} queued runs" + (f" (from {moved_from})" if moved_from else "")
          + f", last finish {fmt(max(slots[s]))} UTC" + (f"   (without move: {fmt(max(before[s]))})" if s in SRC else ""))
print(f"  all these runs finished: {fmt(max(max(v) for v in slots.values()))} UTC "
      f"(without move: {fmt(max(max(before[s]) for s in SRC))})")
if not apply:
    print("dry run; --apply to place the placeholders, write the laby list and copy it to the lab")
    sys.exit()

moved = []
for s, (host, lst, d, n) in SRC.items():
    ids = [r["run_id"] for r, src in plan["laby"] if src == s]
    if not ids:
        continue
    out = sh(host, f"""cd {d} && ok=""; lost=""; for rid in {' '.join(ids)}; do
  tmp=.tmp_$rid; mkdir -p $tmp && touch $tmp/DONE $tmp/MOVED_TO_{DEST.upper()};
  if [ ! -e $rid ] && mv -T $tmp $rid 2>/dev/null && [ -f $rid/MOVED_TO_{DEST.upper()} ]; then ok="$ok $rid"; else rm -rf $tmp; lost="$lost $rid"; fi;
done; echo "ok:$ok"; echo "lost:$lost" """)
    ok = re.search(r"ok:(.*)", out).group(1).split()
    lost = re.search(r"lost:(.*)", out).group(1).split()
    print(f"{s}: {len(ok)} placeholders; kept at home (started meanwhile): {' '.join(lost) or 'none'}")
    moved += ok
mv = set(moved)
laby = [r for r, _ in plan["laby"] if r["run_id"] in mv]
with open(f"{R}/design_v2_full_{DEST}_n2.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader(); w.writerows(laby)
subprocess.run(["scp", "-q", f"{R}/design_v2_full_{DEST}_n2.csv", f"labpc:thermbench/design_v2_full_{DEST}_n2.csv"], check=True)
print(f"{DEST} list: {len(laby)} runs, copied to labpc:~/thermbench/")
