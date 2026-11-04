#!/bin/bash
# Runs ON THE LAB PC (nohup). Mesh convergence, 3 levels x 2 regimes:
#   lam: laminar, uin 0.02 (Re ~1200), 600 s full charge
#   tur: kOmegaSST + OpenFOAM buoyancyTurbSource, uin 0.1 (Re ~6000), 150 s
# Real water properties (buoyantPimpleFoam), the production model.
# L1 5 mm serial, L2 3.33 mm on 2 cores, L3 2.22 mm on 5 cores.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
GEN=~/thermbench/scripts/make_tank_case.py
BASE=~/of_runs/convergence
mkdir -p $BASE
run() {  # name nproc args...
  local name=$1 np=$2; shift 2
  local c=$BASE/$name
  rm -rf $c
  python3 $GEN $c "$@" > $BASE/$name.gen.txt || return 1
  cd $c
  blockMesh > log.blockMesh 2>&1 || { echo "$name blockMesh FAILED" > $BASE/$name.done.txt; return 1; }
  local S=$SECONDS rc
  local app=$(foamDictionary -entry application -value system/controlDict)
  if [ $np -gt 1 ]; then
    cat > system/decomposeParDict <<EOF
FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains $np;
method scotch;
EOF
    decomposePar > log.decomposePar 2>&1
    mpirun -np $np $app -parallel > log.solver 2>&1; rc=$?
    reconstructPar > log.reconstructPar 2>&1
  else
    $app > log.solver 2>&1; rc=$?
  fi
  echo "$name np=$np rc=$rc wall=$((SECONDS-S))s steps=$(grep -c '^Time =' log.solver)" > $BASE/$name.done.txt
}
LAM="--uin 0.02 --end 600 --write 10 --props real"
TUR="--uin 0.1 --end 150 --write 15 --props real --turb kOmegaSST --buoy"
# 16 processes in total = one per physical core
run lam_L1 1 --h 0.005 $LAM &
run lam_L2 2 --h 0.0033333333333 $LAM &
run lam_L3 5 --h 0.0022222222222 $LAM &
run tur_L1 1 --h 0.005 $TUR &
run tur_L2 2 --h 0.0033333333333 $TUR &
run tur_L3 5 --h 0.0022222222222 $TUR &
wait
echo ALL_DONE > $BASE/ALL_DONE
