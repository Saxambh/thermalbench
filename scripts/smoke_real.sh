#!/bin/bash
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
B=~/of_runs/smoke_real; mkdir -p $B
one() {  # name, solver, args
  local n=$1 s=$2; shift 2
  rm -rf $B/$n; python3 $SRC/make_tank_case.py $B/$n "$@"
  cd $B/$n; blockMesh > log.blockMesh 2>&1 || { echo "$n blockMesh FAILED"; return; }
  $s > log.solver 2>&1; echo "$n rc=$? steps=$(grep -c '^Time =' log.solver)"
  grep -m1 -A10 "FOAM FATAL" log.solver
  echo "  meanT: $(tail -1 postProcessing/meanT/0/volFieldValue.dat 2>/dev/null)"
}
one regress buoyantBoussinesqPimpleFoam --uin 0.02 --end 5 --write 5
echo "  regression md5 (expect 7d3b88af04eff35753ea8737fa6ac3ba): $(md5sum $B/regress/5/T | cut -c1-32)"
one real_lam buoyantPimpleFoam --uin 0.02 --end 5 --write 5 --props real
one real_sst buoyantPimpleFoam --uin 0.1 --end 2 --write 1 --props real --turb kOmegaSST --buoy
grep -m2 -i "buoyancyTurbSource\|Applying" $B/real_sst/log.solver
