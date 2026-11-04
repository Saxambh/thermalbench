#!/bin/bash
# Run this machine's share of pc4's PCM queue (pcm_rebalance.py, 2026-11-04): the list
# ~/thermbench/pcm_more_<machine>.csv goes into the usual ~/of_runs/pcm_full/runs with <jobs> jobs,
# started at once (now) or when no tank batch (run_batch.py) is left on the machine (after_tank).
# On pc5 the solver runs inside the OpenFOAM container "ofbox" (pc5_container/pc5_container.sh).
# Restartable like pcm_batch.sh (DONE cases are skipped). Log ~/pcm_more.log.
#   pcm_more.sh <machine> <jobs> <now|after_tank>
M=$1; J=$2; WHEN=${3:-after_tank}
CSV=~/thermbench/pcm_more_$M.csv; LOG=~/pcm_more.log
SCR=$(dirname "$(readlink -f "$0")")
echo "$(date -u '+%F %H:%M') pcm_more pid $$: $M, $J jobs, $WHEN, $(tail -n +2 $CSV | wc -l) cases" >> $LOG
if [ "$WHEN" = after_tank ]; then
  while pgrep -a python3 | grep -q "run_batch.py"; do sleep 300; done
  echo "$(date -u '+%F %H:%M') no tank batch left, starting" >> $LOG
fi
mkdir -p ~/of_runs/pcm_full/runs
if [ "$M" = pc5 ]; then
  podman start ofbox > /dev/null
  podman exec -e PCM_STAGGER=30 ofbox bash $SCR/pcm_batch.sh $CSV $HOME/of_runs/pcm_full/runs $J >> ~/of_runs/pcm_full/batch_more.out 2>&1
else
  PCM_STAGGER=30 bash $SCR/pcm_batch.sh $CSV ~/of_runs/pcm_full/runs $J >> ~/of_runs/pcm_full/batch_more.out 2>&1
fi
echo "$(date -u '+%F %H:%M') pcm_more for $M finished ($(grep -c . $CSV) lines in list)" >> $LOG
