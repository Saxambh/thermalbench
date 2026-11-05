#!/bin/bash
# Live view of ThermalStorageBench training on this PC (run_final.sh / run_final_pcm.sh workers).
#   bash watch_training.sh          refreshes every 30 s, Ctrl+C to leave (nothing is stopped)
#   bash watch_training.sh all      laptop only: every worker over ssh, one block each
#   bash watch_training.sh once     print once and exit
# Shows per worker: current job and how long it has run, last logged epoch (every 10th), jobs done
# of planned, the latest test scores, and the GPU (load, memory, temperature). Read-only.
# Written 2026-11-05 (Saxam: "let me see the training console on each pc so that others can also see it").
cd "$(dirname "$(readlink -f "$0")")"
MODE=${1:-watch}

block() {   # summary of every run_final*.log under this folder
  local any=0
  for log in results*/run_final*.log; do
    [ -f "$log" ] || continue; any=1
    python3 - "$log" <<'PY'
import re, sys, time, datetime as dt
log = sys.argv[1]
L = open(log, errors="replace").read().splitlines()
head = next((l for l in L if l.startswith("=== run_final")), "")
w = re.search(r"worker (\S+)", head)
total = next((int(m.group(1)) for l in L if (m := re.match(r"(\d+) jobs for", l))), None)
jobs = [i for i, l in enumerate(L) if l.startswith("--- ") and "skipped" not in l]
skipped = sum("already done" in l for l in L)
done = sum(l.startswith("{'") for l in L) + skipped
fam = "PCM" if "pcm" in log else "tank"
print(f"== {fam} worker {w.group(1) if w else '?'}  ({log})")
if total:
    bar = int(30 * done / total)
    print(f"   jobs   [{'#' * bar}{'.' * (30 - bar)}] {done}/{total} done")
if any("worker" in l and " done " in l for l in L):
    print("   FINISHED: " + [l for l in L if " done " in l and "worker" in l][-1])
elif jobs:
    cur = L[jobs[-1]]
    m = re.search(r"\((\d+) epochs\) (\d\d):(\d\d)", cur)
    run = ""
    if m:
        now = dt.datetime.now(dt.timezone.utc)
        st = now.replace(hour=int(m.group(2)), minute=int(m.group(3)), second=0, microsecond=0)
        if st > now: st -= dt.timedelta(days=1)
        run = f", running {int((now - st).total_seconds() // 60)} min"
    print(f"   now    {cur[4:].split(' (')[0]}{' (' + m.group(1) + ' epochs)' if m else ''}{run}")
    ep = [l for l in L[jobs[-1]:] if l.startswith("epoch")]
    if ep:
        e = re.match(r"epoch +(\d+) +train RMSE ([\d.]+) +val RMSE ([\d.]+)", ep[-1])
        if e:
            print(f"   epoch  {e.group(1)}{'/' + m.group(1) if m else ''}  train error {float(e.group(2)):.4f}, validation error {float(e.group(3)):.4f} (theta)")
    else:
        print("   epoch  loading data / first epochs (logged every 10 epochs)")
res = [(i, l) for i, l in enumerate(L) if l.startswith("{'")]
if res:
    i, l = res[-1]
    job = next((L[j][4:].split(" (")[0] for j in range(i, -1, -1) if L[j].startswith("--- ")), "?")
    r = re.search(r"'rmse_K': ([\d.]+)", l)
    print(f"   last   {job}: test error {float(r.group(1)):.2f} K" if r else f"   last   {job}")
err = [l for l in L if "Error" in l or "Traceback" in l or "STOP" in l]
if err:
    print(f"   PROBLEM in log: {err[-1][:120]}")
PY
  done
  [ $any = 0 ] && echo "== no training log here yet (results*/run_final*.log)"
  local smi=nvidia-smi; command -v nvidia-smi > /dev/null || smi=/usr/lib/wsl/lib/nvidia-smi
  $smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null \
    | awk -F', ' '{printf "   GPU %s %s: load %s %%, memory %.1f of %.1f GB, %s C\n", $1, $2, $3, $4/1024, $5/1024, $6}'
}

show() {
  echo "ThermalStorageBench training on $(hostname)   $(TZ=Asia/Kathmandu date '+%a %H:%M') Nepal time"
  echo
  if [ "$MODE" = all ]; then
    block
    for x in lab:labpc:thermbench_ml pc3:saxam@pc3:thermbench_ml pc4:saxam@pc4:thermbench_ml pc6:saxam@pc6:thermbench_ml pc5:pc5:thermalbench/thermbench_ml; do
      IFS=: read -r w h d <<< "$x"; echo
      timeout 40 ssh -o BatchMode=yes -o ConnectTimeout=10 $h "bash ~/$d/watch_training.sh once | tail -n +3" < /dev/null 2>/dev/null \
        || echo "== $w not reachable (PC off or asleep, or its Ubuntu window closed)"
    done
  else
    block
  fi
}

if [ "$MODE" = once ]; then show; exit 0; fi
[ "$MODE" = all ] && MODE=all || MODE=watch
while true; do
  out=$(show 2>&1)
  clear; echo "$out"; echo; echo "(refreshes every 30 s; Ctrl+C closes this view, training keeps running)"
  sleep 30
done
