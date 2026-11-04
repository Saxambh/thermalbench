#!/bin/bash
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
echo "== laptop"; python3 $S/speed_cmp.py
scp -q $S/speed_cmp.py labpc:thermbench/scripts/
echo "== lab"; ssh labpc 'python3 ~/thermbench/scripts/speed_cmp.py; lscpu | grep -E "MHz|Model name"; cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null'
echo "== laptop cpu"; lscpu | grep -E "Model name|MHz"
