#!/bin/bash
# Build the tank case at three cell sizes, run each for a short window, report speed.
source /opt/OpenFOAM/OpenFOAM-v2012/etc/bashrc WM_COMPILER=Gcc63
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
BASE=~/of_runs/thermbench_test
END=${1:-60}
mkdir -p $BASE
for lvl in "L1 0.005" "L2 0.0033333333333333335" "L3 0.0022222222222222222"; do
  set -- $lvl; name=$1; h=$2
  case=$BASE/tank_$name
  rm -rf $case
  python3 $SRC/make_tank_case.py $case --h $h --end $END --write $END || exit 1
  cd $case
  blockMesh > log.blockMesh 2>&1 || { echo "$name blockMesh FAILED"; tail -20 log.blockMesh; exit 1; }
  checkMesh > log.checkMesh 2>&1; grep -E "cells:|Mesh OK|FAILED" log.checkMesh | head -3
  S=$(date +%s.%N)
  buoyantBoussinesqPimpleFoam > log.solver 2>&1
  rc=$?
  E=$(date +%s.%N)
  steps=$(grep -c '^Time =' log.solver)
  printf "%s h=%s rc=%s wall=%.1fs steps=%s last:%s\n" $name $h $rc $(echo "$E-$S" | bc) $steps "$(grep '^Time =' log.solver | tail -1)"
  grep -m1 -i "fatal" log.solver && tail -30 log.solver
  tail -1 postProcessing/meanT/0/volFieldValue.dat
done
