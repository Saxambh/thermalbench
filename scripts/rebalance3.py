#!/usr/bin/env python3
"""Split the lab's queued tank runs into three streams (2026-11-03, Saxam approved):
  labmain  - the lab's running batch (14 slots), keeps its share in its own order
  labx     - a second lab batch, 8 slots (the cores freed by pausing lou3d/sst_finelow)
  laptopx  - a laptop batch, 8 slots (idle laptop cores)
Each queued run (lab order, longest first) goes to the stream that would finish it earliest,
with run lengths from each machine's own finished runs. Moved runs get a placeholder in the
lab's batch folder (DONE + MOVED_TO_<stream>), so the running lab batch skips them; the new
streams run in ~/of_runs/full_h5mm_x, so no two processes ever share a run folder.
Usage: rebalance3.py [--apply]
"""
import csv, io, os, re, subprocess, sys, time
import numpy as np

R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
LAB_CSV = f"{R}/design_v2_full_lab_n2.csv"
SLOTS = {"labmain": 14, "labx": 8, "laptopx": 8}
SLOWDOWN = {"labmain": 1.0, "labx": 1.0, "laptopx": 1.15}   # laptop: 8 more busy threads
apply = "--apply" in sys.argv
now = time.time()
H = 3600.0


def ssh(cmd):
    return subprocess.run(["ssh", "-o", "BatchMode=yes", "labpc", cmd], capture_output=True, text=True,
                          check=True, stdin=subprocess.DEVNULL).stdout


rows = list(csv.DictReader(open(LAB_CSV)))
rows.sort(key=lambda r: -float(r["end_s"]) * float(r["W"]) / float(r["s"]))   # run_batch order
order = {r["run_id"]: k for k, r in enumerate(rows)}


def feats(r):
    return [1.0, np.log(float(r["end_s"])), np.log(float(r["W"])), np.log(float(r["u_in"])),
            np.log(float(r["s"])), float(r["turb"] != "laminar")]


design = {r["run_id"]: r for r in csv.DictReader(open(f"{R}/design_v2_full.csv"))}
for f in ("design_v2_full_laptop_n2.csv", "design_v2_full_pc3_n2.csv"):
    design.update({r["run_id"]: r for r in csv.DictReader(open(f"{R}/{f}"))})
design.update({r["run_id"]: r for r in rows})


def model(status_text):
    X, y = [], []
    for l in csv.DictReader(io.StringIO(status_text)):
        if l["status"] == "ok" and l["run_id"] in design and float(l["wall_s"]) > 60:
            X.append(feats(design[l["run_id"]])); y.append(np.log(float(l["wall_s"])))
    X, y = np.array(X), np.array(y)
    c = np.linalg.lstsq(X, y, rcond=None)[0]
    v = (y - X @ c).var()
    return (lambda r: float(np.exp(np.array(feats(r)) @ c + 0.5 * v))), len(y)


lab_pred, n_lab = model(ssh("cat ~/of_runs/full_h5mm/batch_status.csv"))
lap_pred, n_lap = model(open(os.path.expanduser("~/of_runs/full_h5mm/batch_status.csv")).read())
pred = {"labmain": lab_pred, "labx": lab_pred, "laptopx": lap_pred}

# lab state: per run folder, moved / done / running (sim time, clock, log age) / other
listing = ssh(r"""cd ~/of_runs/full_h5mm && now=$(date +%s); for d in T*/; do d=${d%/};
  if ls $d | grep -q MOVED; then echo "$d moved";
  elif [ -f $d/DONE ]; then echo "$d done";
  elif [ -f $d/log.solver ]; then t=$(tail -c 20000 $d/log.solver | grep "^Time = " | tail -1 | awk '{print $3}');
    c=$(tail -c 20000 $d/log.solver | grep -o "ClockTime = [0-9.]*" | tail -1 | awk '{print $3}');
    echo "$d run ${t:-0} ${c:-0} $(( now - $(stat -c %Y $d/log.solver) ))";
  else echo "$d other"; fi; done""")
lab_state = {l.split()[0]: l.split()[1:] for l in listing.splitlines() if l.strip()}

slots = {s: [] for s in SLOTS}
for rid, st in lab_state.items():
    if st[0] == "run" and rid in design:
        r = design[rid]
        t, clock, age = float(st[1]), float(st[2]), float(st[3])
        frac = t / float(r["end_s"])
        model_left = lab_pred(r) * (1 - frac)
        left = (float(r["end_s"]) - t) * clock / t if t > 0 and frac > 0.1 else model_left
        slots["labmain"].append(now + left)
for s, n in SLOTS.items():
    slots[s] += [now] * (n - len(slots[s]))
    slots[s] = slots[s][:max(n, len(slots[s]))]

queued = [r for r in rows if r["run_id"] not in lab_state]
plan = {s: [] for s in SLOTS}
for r in queued:            # lab order = longest first, so this is longest-processing-time list scheduling
    best = None
    for s in SLOTS:
        k = int(np.argmin(slots[s]))
        end = slots[s][k] + pred[s](r) * SLOWDOWN[s]
        if best is None or end < best[0]:
            best = (end, s, k)
    end, s, k = best
    slots[s][k] = end
    plan[s].append(r)

fmt = lambda t: time.strftime("%a %d %b %H:%M", time.gmtime(t))
running = sum(1 for v in lab_state.values() if v[0] == "run")
print(f"lab: {len(rows)} runs in list, {running} running, {len(queued)} queued; models from {n_lab} lab / {n_lap} laptop runs")
for s in SLOTS:
    d = [pred[s](r) * SLOWDOWN[s] / H for r in plan[s]]
    print(f"  {s:8s} {SLOTS[s]:2d} slots: {len(plan[s]):3d} runs, {sum(d):6.0f} slot-h"
          + (f", run lengths {min(d):.1f}-{max(d):.1f} h" if d else "") + f", last finish {fmt(max(slots[s]))} UTC")
print(f"  all lab-list runs finished: {fmt(max(max(v) for v in slots.values()))} UTC (before: about Tue 10 Nov 03:00)")
if not apply:
    print("dry run; --apply to write the lists, place the lab placeholders and start the two batches")
    sys.exit()

# --- apply ---------------------------------------------------------------------------------
fields = list(rows[0])
for s, host_csv in (("labx", "design_v2_full_labx_n2.csv"), ("laptopx", "design_v2_full_laptopx_n2.csv")):
    with open(f"{R}/{host_csv}", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(plan[s])
# placeholders: build each in a temp folder, then rename into place, which fails if the lab
# batch has created that run folder in the meantime (the run then simply stays on the lab)
moves = " ".join(f"{r['run_id']}:{'LABX' if s == 'labx' else 'LAPTOP'}" for s in ("labx", "laptopx") for r in plan[s])
out = ssh(f"""cd ~/of_runs/full_h5mm && ok=0; lost=""; for m in {moves}; do rid=${{m%%:*}}; to=${{m##*:}};
  tmp=.tmp_$rid; mkdir -p $tmp && touch $tmp/DONE $tmp/MOVED_TO_$to;
  if [ ! -e $rid ] && mv -T $tmp $rid 2>/dev/null && [ -f $rid/MOVED_TO_$to ]; then ok=$((ok+1)); else rm -rf $tmp; lost="$lost $rid"; fi;
done; echo "placeholders $ok; kept on lab main (started meanwhile):$lost" """)
print(out.strip())
lost = set(re.sub(r".*:", "", out.strip().splitlines()[-1]).split())
if lost:   # rewrite the lists without the runs the lab batch already started
    for s, host_csv in (("labx", "design_v2_full_labx_n2.csv"), ("laptopx", "design_v2_full_laptopx_n2.csv")):
        plan[s] = [r for r in plan[s] if r["run_id"] not in lost]
        with open(f"{R}/{host_csv}", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(plan[s])
print(f"labx {len(plan['labx'])} runs, laptopx {len(plan['laptopx'])} runs")
