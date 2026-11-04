#!/bin/bash
setsid nohup bash /mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench/laptop_switch.sh > /dev/null 2>&1 < /dev/null &
sleep 2; pgrep -fa laptop_switch.sh; tail -2 ~/of_runs/chain.log; ls ~/of_runs/full_h5mm/*/DONE | wc -l
