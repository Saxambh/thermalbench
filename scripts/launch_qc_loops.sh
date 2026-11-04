#!/bin/bash
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
pkill -f qc_loop.sh
setsid nohup bash $S/qc_loop.sh $S/qc_runs.py ~/of_runs/full_h5mm > /dev/null 2>&1 < /dev/null &
scp -q $S/qc_loop.sh labpc:thermbench/scripts/
ssh labpc 'pkill -f qc_loop.sh; setsid nohup bash ~/thermbench/scripts/qc_loop.sh ~/thermbench/scripts/qc_runs.py ~/of_runs/full_h5mm > /dev/null 2>&1 < /dev/null & sleep 1; pgrep -fa qc_loop.sh'
pgrep -fa qc_loop.sh
