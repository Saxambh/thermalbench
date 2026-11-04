#!/bin/bash
# Start this machine's share of the PCM full design as soon as its tank QUEUE is empty (v2,
# 2026-11-03, Saxam: use the machines fully): when every row of each running run_batch.py list
# has been started, the remaining tank runs finish alongside the PCM batch, so no core idles
# through the tank tail. On the lab it also resumes the paused 3D Lou case once the tank runs
# have all finished. Log: ~/pcm_watch.log. Cancel: kill this script's PID (in the log).
#   pcm_after_tank.sh <machine> <jobs>      machine = pc3 | laptop | lab
M=$1; J=$2; CSV=~/thermbench/pcm_full_$M.csv; LOG=~/pcm_watch.log
echo "$(date -u '+%F %H:%M') watcher v2 pid $$ for $M, $J jobs, $CSV ($(tail -n +2 $CSV | wc -l) cases)" >> $LOG
tank() { pgrep -a python3 | grep -q "run_batch.py"; }   # processes named python3 only, not bash wrappers
queued() {  # tank runs not yet started by the running run_batch.py processes (no run folder yet)
  python3 - <<'PY'
import csv, os, subprocess
n = 0
for line in subprocess.run(["pgrep", "-a", "python3"], capture_output=True, text=True).stdout.splitlines():
    pid, *argv = line.split(" ")
    if not any(a.endswith("run_batch.py") for a in argv):
        continue
    try:
        argv = open(f"/proc/{pid}/cmdline").read().split("\0"); cwd = os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        continue
    i = next(k for k, a in enumerate(argv) if a.endswith("run_batch.py"))
    f, out = (os.path.join(cwd, x) for x in argv[i + 1:i + 3])
    n += sum(not os.path.exists(os.path.join(out, r["run_id"])) for r in csv.DictReader(open(f)))
print(n)
PY
}
while tank && [ "$(queued)" -gt 0 ]; do sleep 300; done
echo "$(date -u '+%F %H:%M') tank queue empty ($(pgrep -c buoyantPimple) solvers still running)" >> $LOG
if [ "$(tail -n +2 $CSV | wc -l)" -gt 0 ]; then
  mkdir -p ~/of_runs/pcm_full/runs
  PCM_STAGGER=30 setsid nohup bash ~/thermbench/scripts/pcm_batch.sh $CSV ~/of_runs/pcm_full/runs $J > ~/of_runs/pcm_full/batch.out 2>&1 < /dev/null &
  echo "$(date -u '+%F %H:%M') started pcm_batch.sh (pid $!)" >> $LOG
fi
if [ "$M" = lab ]; then
  while tank; do sleep 300; done
  for b in ~/of_runs/full_h5mm ~/of_runs/full_h5mm_x; do
    [ -d $b ] && echo "$(date -u '+%F %H:%M') tank batch ended: $b has $(ls $b/*/DONE 2>/dev/null | wc -l) DONE" >> $LOG
  done
  setsid nohup bash ~/thermbench/scripts/lou3d_run_lab.sh > ~/of_runs/lou3d_finelow.out 2>&1 < /dev/null &
  echo "$(date -u '+%F %H:%M') resumed lou3d/sst_finelow (pid $!)" >> $LOG
fi
