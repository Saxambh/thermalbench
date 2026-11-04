#!/bin/bash
# Laptop: let the three nearly finished runs end (max 45 min), then restart the driver on the laptop share only.
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
R="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
O=~/of_runs/full_h5mm; LOG=~/of_runs/chain.log
echo "$(date) switch: waiting for T0177 T0462 T0662" >> $LOG
for i in $(seq 1 45); do
  [ -f $O/T0177_lam/DONE ] && [ -f $O/T0462_lam/DONE ] && [ -f $O/T0662_lam/DONE ] && break
  sleep 60
done
pkill -f laptop_chain.sh; pkill -f run_batch.py; pkill -f buoyantPimpleFoam; sleep 5
# remove unfinished dirs that now belong to the lab share
python3 - "$R/design_v2_full_laptop.csv" $O >> $LOG 2>&1 <<'PY'
import csv, os, sys, shutil
keep = {r["run_id"] for r in csv.DictReader(open(sys.argv[1]))}
for d in os.listdir(sys.argv[2]):
    p = os.path.join(sys.argv[2], d)
    if os.path.isdir(p) and d not in keep and not os.path.exists(os.path.join(p, "DONE")):
        shutil.rmtree(p); print("removed lab-share partial", d)
PY
echo "$(date) switch: DONE count $(ls $O/*/DONE | wc -l); starting laptop share, 4 jobs" >> $LOG
cd ~ && python3 $S/run_batch.py "$R/design_v2_full_laptop.csv" $O --jobs 4 > ~/of_runs/full_laptop.log 2>&1
echo "$(date) laptop share driver exited" >> $LOG
