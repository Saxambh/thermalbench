#!/bin/bash
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
scp -q $S/make_tank_case.py $S/profile_summary.py $S/lab_convergence.sh labpc:thermbench/scripts/ || exit 1
ssh labpc 'nohup bash ~/thermbench/scripts/lab_convergence.sh > ~/thermbench/convergence.log 2>&1 < /dev/null & sleep 30; ls ~/of_runs/convergence; uptime'
