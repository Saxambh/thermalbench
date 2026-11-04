#!/bin/bash
# Detached chain on the laptop: wait for pilot_v2, run the gate, start the full 5 mm batch only on PASS.
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
R="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
LOG=~/of_runs/chain.log
echo "$(date) waiting for pilot_v2" >> $LOG
while pgrep -f "run_batch.py.*pilot_v2" > /dev/null; do sleep 120; done
echo "$(date) pilot_v2 batch finished" >> $LOG
if python3 $S/pilot_gate.py ~/of_runs/pilot_v2 >> $LOG 2>&1; then
  echo "$(date) gate PASS, starting full batch (laptop, 4 jobs)" >> $LOG
  cd ~ && python3 $S/run_batch.py "$R/design_v2_full.csv" ~/of_runs/full_h5mm --jobs 4 > ~/of_runs/full_h5mm.log 2>&1
  echo "$(date) full batch driver exited" >> $LOG
else
  echo "$(date) gate FAIL, full batch NOT started" >> $LOG
fi
