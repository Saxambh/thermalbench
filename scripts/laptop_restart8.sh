#!/bin/bash
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
R="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
pkill -f laptop_switch.sh; pkill -f run_batch.py; pkill -f buoyantPimpleFoam; sleep 5
echo "left: $(pgrep -fc buoyantPimpleFoam)  DONE: $(ls ~/of_runs/full_h5mm/*/DONE | wc -l)"
echo "$(date) rebalance: laptop restarted on design_v2_full_laptop2.csv (997 runs incl. 712 moved from lab), 8 jobs" >> ~/of_runs/chain.log
cd ~ && setsid nohup python3 $S/run_batch.py "$R/design_v2_full_laptop2.csv" ~/of_runs/full_h5mm --jobs 8 \
  > ~/of_runs/full_laptop2.log 2>&1 < /dev/null &
sleep 40
echo "solvers: $(pgrep -fc buoyantPimpleFoam)"
head -1 ~/of_runs/full_laptop2.log
free -g | head -2
