#!/bin/bash
# Restart the fine subset on the lab PC with the fixed outlet (fixedMean p_rgh, zeroGradient T) and GAMG.
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
scp -q $S/make_tank_case.py $S/run_batch.py $S/export_case.py labpc:thermbench/scripts/ || exit 1
ssh labpc 'bash -s' <<'R'
echo "running before: $(pgrep -u saxam -fc buoyantPimpleFoam)"
mkdir -p ~/of_runs/outlet_bug_evidence
for c in T0033_lam T0054_lam; do cp ~/of_runs/fine128_h3mm/$c/case.json ~/of_runs/outlet_bug_evidence/$c.case.json; tail -c 2000000 ~/of_runs/fine128_h3mm/$c/log.solver > ~/of_runs/outlet_bug_evidence/$c.log_tail; done
rm -rf ~/of_runs/fine128_h3mm
grep -c "fixedMean" ~/thermbench/scripts/make_tank_case.py
cd ~/thermbench
setsid nohup python3 scripts/run_batch.py design_v2_fine128.csv ~/of_runs/fine128_h3mm --jobs 14 \
  > ~/thermbench/fine128.log 2>&1 < /dev/null &
sleep 60
echo "solvers: $(pgrep -u saxam -fc buoyantPimpleFoam)"
grep -h -A1 "outlet" ~/of_runs/fine128_h3mm/*/0/p_rgh | grep type | sort | uniq -c
grep -h "solver  *GAMG" ~/of_runs/fine128_h3mm/*/system/fvSolution | sort | uniq -c
grep -l "FOAM FATAL" ~/of_runs/fine128_h3mm/*/log.solver 2>/dev/null | head
free -g | head -2
R
