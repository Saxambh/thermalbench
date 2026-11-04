#!/bin/bash
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
python3 $S/pilot_gate.py ~/of_runs/pilot_v2 | tail -12
setsid nohup bash $S/laptop_chain.sh > /dev/null 2>&1 < /dev/null &
sleep 2; pgrep -fa laptop_chain.sh; cat ~/of_runs/chain.log
