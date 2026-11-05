#!/bin/bash
# Keep the distributed training going (2026-11-05, after the seed-0 bug ended the lab worker): every 5 min,
# for each worker, if its run_final script is not running and its log does not say it is done, start it
# again. Finished jobs are skipped by run_final(_pcm).sh, so a restart loses only the minutes until it is
# noticed. A worker is not touched if its machine does not answer (no restart on a network hiccup). After
# 6 restarts of one worker it is left alone and flagged (a job that crashes every time needs a look).
#   setsid nohup bash train_supervisor.sh tank > /dev/null 2>&1 < /dev/null &      (WSL on the laptop)
#   bash train_supervisor.sh pcm      (the PCM training: run_final_pcm.sh, 7 workers with pc6)
# Log ~/train_supervisor_<family>.log. Stops when every worker is done.
F=${1:?tank or pcm}
ML="$(dirname "$(readlink -f "$0")")"
LOG=~/train_supervisor_$F.log
if [ $F = tank ]; then S=run_final.sh; P=results; WORKERS="laptop lab pc3 pc4 pc5a pc5b"
else S=run_final_pcm.sh; P=results_pcm; WORKERS="laptop lab pc3 pc4 pc5a pc5b pc6"; fi
host() { case $1 in laptop) echo "";; lab) echo labpc;; pc3|pc4|pc6) echo saxam@$1;; pc5a|pc5b) echo pc5;; esac; }
dir()  { case $1 in pc5a|pc5b) echo thermalbench/thermbench_ml;; *) echo thermbench_ml;; esac; }
logf() { case $1 in pc5a|pc5b) echo ${P}_$1/${S%.sh}.log;; *) echo $P/${S%.sh}.log;; esac; }
on() {  # worker command: run on the worker's machine (laptop: locally, in the code folder)
  local h=$(host $1); shift
  if [ -z "$h" ]; then (cd "$ML" && bash -c "$*"); else timeout 60 ssh -o BatchMode=yes -o ConnectTimeout=20 $h "cd ~/$(dir $W) && $*" < /dev/null; fi
}
declare -A N
echo "$(date -u '+%F %H:%M') supervisor pid $$ for $F: $WORKERS" >> $LOG
while true; do
  left=0
  for W in $WORKERS; do
    st=$(on $W "if pgrep -f '$S $W\$' > /dev/null; then echo running; elif grep -q '=== worker $W done' $(logf $W) 2>/dev/null; then echo done; else echo stopped; fi") || { echo "$(date -u '+%H:%M') $W: no answer, left alone" >> $LOG; left=1; continue; }
    case $st in
      running) left=1 ;;
      done) ;;
      stopped)
        left=1
        if [ "${N[$W]:-0}" -ge 6 ]; then echo "$(date -u '+%H:%M') $W: PROBLEM stopped again after 6 restarts, left for a look" >> $LOG; continue; fi
        N[$W]=$(( ${N[$W]:-0} + 1 ))
        on $W "setsid nohup bash $S $W >> ~/run_final_$W.out 2>&1 < /dev/null &" > /dev/null
        echo "$(date -u '+%H:%M') $W: stopped before the end, restarted (restart ${N[$W]}); last log line: $(on $W "tail -1 $(logf $W)" | cut -c1-100)" >> $LOG ;;
    esac
  done
  [ $left = 0 ] && { echo "$(date -u '+%F %H:%M') all $F workers done, supervisor ends" >> $LOG; exit 0; }
  sleep 300
done
