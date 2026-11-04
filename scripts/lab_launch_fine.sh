#!/bin/bash
# Launch the 128-case fidelity subset (3.33 mm) on the lab PC, detached (nohup/setsid).
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
D="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
scp -q $S/make_tank_case.py $S/export_case.py $S/make_design.py $S/run_batch.py $S/tbstat.py labpc:thermbench/scripts/ || exit 1
scp -q "$D/design_v2_fine128.csv" labpc:thermbench/ || exit 1
ssh labpc 'bash -s' <<'EOF'
cd ~/thermbench
md5sum scripts/run_batch.py scripts/make_tank_case.py design_v2_fine128.csv
setsid nohup python3 scripts/run_batch.py design_v2_fine128.csv ~/of_runs/fine128_h3mm --jobs 14 \
  > ~/thermbench/fine128.log 2>&1 < /dev/null &
sleep 60
head -2 ~/thermbench/fine128.log
echo "solvers: $(pgrep -fc buoyantPimpleFoam)"
ls ~/of_runs/fine128_h3mm | head -20
grep -l "FOAM FATAL" ~/of_runs/fine128_h3mm/*/log.solver 2>/dev/null | head
EOF
