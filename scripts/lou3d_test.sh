#!/bin/bash
# Short parallel test of the 3D Lou case: 3 s simulated on 4 cores.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
C=~/of_runs/lou3d/test; rm -rf $C
python3 $S/make_lou3d.py $C --turb kOmegaSST --end 3 > /dev/null || exit 1
ls $C/0
cd $C
foamDictionary system/controlDict -entry writeInterval -set 1 > /dev/null
cat > system/decomposeParDict <<'D'
FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains 4;
method          scotch;
D
decomposePar > log.decomposePar 2>&1 || { tail log.decomposePar; exit 1; }
S0=$SECONDS
nice -n 5 mpirun -np 4 buoyantPimpleFoam -parallel > log.solver 2>&1
echo "exit $? wall $((SECONDS-S0)) s"
grep -m1 -A8 "FOAM FATAL" log.solver
grep "^Time = " log.solver | tail -1; grep -c "^Time = " log.solver
grep "Courant Number" log.solver | tail -1; grep "^deltaT" log.solver | tail -1
grep "Solving for p_rgh" log.solver | tail -2
grep "ExecutionTime" log.solver | tail -1
tail -2 postProcessing/meanT/0/volFieldValue.dat
