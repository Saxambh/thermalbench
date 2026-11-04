#!/bin/bash
setsid nohup bash /mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench/ml_early.sh > /dev/null 2>&1 < /dev/null &
sleep 3; pgrep -fa ml_early.sh
