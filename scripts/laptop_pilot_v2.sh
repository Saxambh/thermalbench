#!/bin/bash
# Pilot rerun on the laptop with the fixed outlet and GAMG. Detached so it survives Claude Code.
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
R="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
cd ~ && setsid nohup python3 $S/run_batch.py "$R/design_v2_pilot.csv" ~/of_runs/pilot_v2 --jobs 4 \
  > ~/of_runs/pilot_v2.log 2>&1 < /dev/null &
sleep 40
echo "solvers: $(pgrep -fc buoyantPimpleFoam)"
grep -h -A2 outlet ~/of_runs/pilot_v2/*/0/p_rgh | grep type | sort | uniq -c
grep -l "FOAM FATAL" ~/of_runs/pilot_v2/*/log.solver 2>/dev/null
tail -3 ~/of_runs/pilot_v2.log
