#!/bin/bash
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
cmp -s $S/make_tank_case.py <(ssh labpc cat thermbench/scripts/make_tank_case.py) && echo "lab make_tank_case.py identical" || echo "WARNING lab make_tank_case.py differs"
scp -q $S/make_lou3d.py $S/lou3d_hj.py $S/lou3d_run_lab.sh $S/lou3d_status.sh labpc:thermbench/scripts/ || exit 1
ssh labpc 'bash -s' <<'X'
ls /usr/lib/openfoam/openfoam2606/etc/bashrc >/dev/null || { echo "no OpenFOAM path"; exit 1; }
which mpirun >/dev/null 2>&1 || (source /usr/lib/openfoam/openfoam2606/etc/bashrc; which mpirun) || echo "no mpirun?"
cd ~ && setsid nohup bash ~/thermbench/scripts/lou3d_run_lab.sh > ~/of_runs/lou3d_finelow.out 2>&1 < /dev/null &
sleep 240
C=~/of_runs/lou3d/sst_finelow
echo "--- gen"; grep -E 'open_area|hole_radius|cells|u_in|area_ratio|mesh_ok' $C/case.json
grep -E 'Mesh OK|Failed|\*\*\*' $C/log.checkMesh | head -5
echo "--- run"; echo "ranks: $(pgrep -fc 'buoyantPimpleFoam -parallel')"
grep '^Time = ' $C/log.solver | tail -1; grep 'Courant' $C/log.solver | tail -1; grep -c FATAL $C/log.solver
tail -2 ~/of_runs/lou3d_finelow.out
uptime
X
