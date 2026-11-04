#!/bin/bash
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
R="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
head -1 "$R/design_v2_full_laptop_n2.csv"
echo "=== laptop"; python3 $S/pace.py "$R/design_v2_full_laptop_n2.csv" ~/of_runs/full_h5mm
scp -q $S/pace.py labpc:thermbench/scripts/pace.py
echo "=== lab"; ssh -o BatchMode=yes labpc 'python3 ~/thermbench/scripts/pace.py ~/thermbench/design_v2_full_lab_n2.csv ~/of_runs/full_h5mm'
