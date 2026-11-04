#!/bin/bash
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
scp -q $S/make_tank_case.py $S/export_case.py $S/qc_runs.py labpc:thermbench/scripts/ || exit 1
ssh labpc 'python3 ~/thermbench/scripts/qc_runs.py ~/of_runs/full_h5mm; python3 ~/thermbench/scripts/qc_runs.py ~/of_runs/fine128_h3mm; grep -c outletHflux ~/thermbench/scripts/make_tank_case.py'
