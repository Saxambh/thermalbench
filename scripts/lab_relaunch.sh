#!/bin/bash
# Stop the Boussinesq convergence batch (only saxam's own processes), keep its partial
# results under a new name, and launch the real-property batch.
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
scp -q $S/make_tank_case.py $S/lab_convergence.sh labpc:thermbench/scripts/ || exit 1
ssh labpc 'bash -s' <<'EOF'
pkill -u saxam -f lab_convergence.sh
pkill -u saxam -f buoyantBoussinesqPimpleFoam
pkill -u saxam -f mpirun
sleep 5
echo "remaining solver processes: $(pgrep -u saxam -fc buoyant)"
cd ~/of_runs && rm -rf convergence_boussinesq_partial && mv convergence convergence_boussinesq_partial
nohup bash ~/thermbench/scripts/lab_convergence.sh > ~/thermbench/convergence.log 2>&1 < /dev/null &
sleep 45
ls ~/of_runs/convergence
for n in lam_L1 lam_L3 tur_L3; do grep -m1 -A6 "FOAM FATAL" ~/of_runs/convergence/$n/log.solver; grep "^Time =" ~/of_runs/convergence/$n/log.solver | tail -1; done
echo "solver processes: $(pgrep -u saxam -fc buoyantPimpleFoam)"; uptime
EOF
