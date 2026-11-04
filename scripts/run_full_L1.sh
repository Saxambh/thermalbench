#!/bin/bash
# Full 600 s charge on the coarse mesh: real runtime + stratification profiles.
source /opt/OpenFOAM/OpenFOAM-v2012/etc/bashrc WM_COMPILER=Gcc63
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
case=~/of_runs/thermbench_test/tank_L1_full
rm -rf $case
python3 $SRC/make_tank_case.py $case --h 0.005 --end 600 --write 60 || exit 1
cd $case
blockMesh > log.blockMesh 2>&1 || exit 1
S=$(date +%s)
buoyantBoussinesqPimpleFoam > log.solver 2>&1
rc=$?
E=$(date +%s)
echo "rc=$rc wall=$((E-S))s steps=$(grep -c '^Time =' log.solver)"
grep -m1 -i fatal log.solver
grep 'deltaT' log.solver | tail -1
echo "--- mean T every 60 s:"
awk 'NR>4 && ($1%60<0.05 || $1%60>59.95) {print}' postProcessing/meanT/0/volFieldValue.dat | head -20
ls postProcessing/profile/
