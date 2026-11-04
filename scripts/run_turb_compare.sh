#!/bin/bash
# Laminar vs k-omega SST vs k-omega SST + buoyancy at a turbulent inlet (Re ~6000).
source /opt/OpenFOAM/OpenFOAM-v2012/etc/bashrc WM_COMPILER=Gcc63
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
BASE=~/of_runs/thermbench_turb
mkdir -p $BASE
run() {  # name, extra args
  local name=$1; shift
  local case=$BASE/$name
  rm -rf $case
  python3 $SRC/make_tank_case.py $case --h 0.005 --uin 0.1 --end 150 --write 15 "$@" > $BASE/$name.gen.txt || return 1
  cd $case
  blockMesh > log.blockMesh 2>&1 || { echo "$name blockMesh FAILED"; return 1; }
  local S=$(date +%s)
  buoyantBoussinesqPimpleFoam > log.solver 2>&1
  local rc=$? E=$(date +%s)
  echo "$name rc=$rc wall=$((E-S))s steps=$(grep -c '^Time =' log.solver)" > $BASE/$name.done.txt
}
run laminar &
run sst --turb kOmegaSST &
run sst_buoy --turb kOmegaSST --buoy &
wait
for n in laminar sst sst_buoy; do
  cat $BASE/$n.gen.txt; cat $BASE/$n.done.txt 2>/dev/null
  grep -m1 -i -A8 fatal $BASE/$n/log.solver
  grep -m2 -i "buoyancyTurbSource" $BASE/$n/log.solver
  echo "  meanT at end: $(tail -1 $BASE/$n/postProcessing/meanT/0/volFieldValue.dat)"
  python3 $SRC/profile_summary.py $BASE/$n
  echo
done
