#!/bin/bash
# Lab: stop the 3.33 mm subset (finished runs kept), start its share of the 5 mm full batch.
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
R="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
scp -q $S/make_tank_case.py $S/run_batch.py $S/export_case.py labpc:thermbench/scripts/ || exit 1
scp -q "$R/design_v2_full_lab.csv" labpc:thermbench/ || exit 1
ssh labpc 'bash -s' <<'X'
pkill -u saxam -f run_batch.py
pkill -u saxam -f buoyantPimpleFoam
sleep 5
echo "left running: $(pgrep -u saxam -fc buoyantPimpleFoam)"
echo "fine128 kept as DONE: $(ls ~/of_runs/fine128_h3mm/*/DONE 2>/dev/null | wc -l)"
cd ~/thermbench
wc -l design_v2_full_lab.csv
setsid nohup python3 scripts/run_batch.py design_v2_full_lab.csv ~/of_runs/full_h5mm --jobs 14 \
  > ~/thermbench/full_lab.log 2>&1 < /dev/null &
sleep 45
echo "solvers: $(pgrep -u saxam -fc buoyantPimpleFoam)"
grep -h -A2 outlet ~/of_runs/full_h5mm/*/0/p_rgh | grep type | sort | uniq -c
grep -h "solver  *GAMG" ~/of_runs/full_h5mm/*/system/fvSolution | sort | uniq -c
grep -l "FOAM FATAL" ~/of_runs/full_h5mm/*/log.solver 2>/dev/null | head
head -2 ~/thermbench/full_lab.log
X
