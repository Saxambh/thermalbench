#!/bin/bash
# Start a spot-check batch once a blocking job is gone (spotcheck.py, 2026-11-04). Log ~/spot_launch.log.
#   spot_launch.sh tank   laptop: after its tank batches (run_batch.py on the laptop lists), 6 jobs
#   spot_launch.sh pcm    pc4: after the PCM validation re-runs (pcm_validate_fix.sh), 6 jobs
F=$1; LOG=~/spot_launch.log; SCR=$(dirname "$(readlink -f "$0")")
echo "$(date -u '+%F %H:%M') spot_launch $F pid $$ waiting" >> $LOG
if [ "$F" = tank ]; then
  while pgrep -af "run_batch.py .*design_v2_full_laptop" > /dev/null; do sleep 300; done
  echo "$(date -u '+%F %H:%M') laptop tank batches gone, starting the tank spot check" >> $LOG
  python3 $SCR/run_batch.py $SCR/spot_tank.csv ~/of_runs/spot_tank --jobs 6 >> ~/of_runs/spot_tank.out 2>&1
else
  while pgrep -f "pcm_validate_fix.sh" > /dev/null; do sleep 300; done
  echo "$(date -u '+%F %H:%M') validation re-runs gone, starting the PCM spot check" >> $LOG
  PCM_STAGGER=30 bash $SCR/pcm_batch.sh ~/thermbench/spot_pcm.csv ~/of_runs/spot_pcm 6 >> ~/of_runs/spot_pcm.out 2>&1
fi
echo "$(date -u '+%F %H:%M') spot check $F finished" >> $LOG
