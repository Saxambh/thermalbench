#!/bin/bash
# Restart the fine subset on the lab PC with the GAMG pressure solver.
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
scp -q $S/make_tank_case.py $S/run_batch.py labpc:thermbench/scripts/ || exit 1
ssh labpc 'bash -s' <<'EOF'
pkill -u saxam -f run_batch.py
pkill -u saxam -f buoyantPimpleFoam
sleep 5
echo "left running: $(pgrep -u saxam -fc buoyantPimpleFoam)"
mv ~/of_runs/fine128_h3mm ~/of_runs/fine128_h3mm_pcg_aborted
grep -c GAMG ~/thermbench/scripts/make_tank_case.py
cd ~/thermbench
setsid nohup python3 scripts/run_batch.py design_v2_fine128.csv ~/of_runs/fine128_h3mm --jobs 14 \
  > ~/thermbench/fine128.log 2>&1 < /dev/null &
sleep 45
echo "solvers: $(pgrep -u saxam -fc buoyantPimpleFoam)"
grep -h "solver  *GAMG" ~/of_runs/fine128_h3mm/*/system/fvSolution | head -1
grep -l "FOAM FATAL" ~/of_runs/fine128_h3mm/*/log.solver 2>/dev/null | head
rm -rf ~/of_runs/fine128_h3mm_pcg_aborted
EOF
