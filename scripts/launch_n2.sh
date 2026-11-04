#!/bin/bash
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
R="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
python3 $S/split_n2.py || exit 1
# generator check
python3 $S/make_tank_case.py /tmp/n2check --props real > /dev/null && grep nOuter /tmp/n2check/system/fvSolution; rm -rf /tmp/n2check
scp -q $S/make_tank_case.py $S/run_batch.py $S/export_case.py $S/qc_runs.py labpc:thermbench/scripts/ || exit 1
scp -q "$R/design_v2_full_lab_n2.csv" labpc:thermbench/ || exit 1
echo "$(date) n2 restart: laptop design_v2_full_laptop_n2.csv 8 jobs; lab design_v2_full_lab_n2.csv 14 jobs" >> ~/of_runs/chain.log
cd ~ && setsid nohup python3 $S/run_batch.py "$R/design_v2_full_laptop_n2.csv" ~/of_runs/full_h5mm --jobs 8 \
  > ~/of_runs/full_laptop_n2.log 2>&1 < /dev/null &
ssh labpc 'bash -s' <<'X'
cd ~/thermbench
setsid nohup python3 scripts/run_batch.py design_v2_full_lab_n2.csv ~/of_runs/full_h5mm --jobs 14 > ~/thermbench/full_lab_n2.log 2>&1 < /dev/null &
sleep 50
echo "lab solvers: $(pgrep -u saxam -fc buoyantPimpleFoam)  nOuter: $(grep -h nOuter ~/of_runs/full_h5mm/*/system/fvSolution | sort | uniq -c)"
grep -l "FOAM FATAL" ~/of_runs/full_h5mm/*/log.solver 2>/dev/null | head -3
X
echo "laptop solvers: $(pgrep -fc buoyantPimpleFoam)  nOuter: $(grep -h nOuter ~/of_runs/full_h5mm/*/system/fvSolution | sort | uniq -c)"
grep -l "FOAM FATAL" ~/of_runs/full_h5mm/*/log.solver 2>/dev/null | head -3
