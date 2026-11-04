#!/bin/bash
# v2606: (a) laminar 5 s check against v2012 (meanT 293.480 K at 5 s),
# (b) laminar vs SST vs SST+buoyancyTurbSource vs SST+our k-buoyancy at Re ~6000.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
BASE=~/of_runs/thermbench_turb_2606
mkdir -p $BASE
run() {  # name, extra args
  local name=$1; shift
  local case=$BASE/$name
  rm -rf $case
  python3 $SRC/make_tank_case.py $case "$@" > $BASE/$name.gen.txt || return 1
  cd $case
  blockMesh > log.blockMesh 2>&1 || { echo "$name blockMesh FAILED" > $BASE/$name.done.txt; return 1; }
  local S=$(date +%s)
  buoyantBoussinesqPimpleFoam > log.solver 2>&1
  local rc=$? E=$(date +%s)
  echo "$name rc=$rc wall=$((E-S))s steps=$(grep -c '^Time =' log.solver)" > $BASE/$name.done.txt
}
T="--h 0.005 --uin 0.1 --end 150 --write 15"
run check_lam5 --h 0.005 --uin 0.02 --end 5 --write 5 &
run laminar $T &
run sst $T --turb kOmegaSST &
run sst_bts $T --turb kOmegaSST --buoy &
run sst_buoyk $T --turb kOmegaSST --buoyk &
wait
echo "=== v2012 reference for check_lam5: meanT at 5 s = 293.480 K"
for n in check_lam5 laminar sst sst_bts sst_buoyk; do
  cat $BASE/$n.gen.txt; cat $BASE/$n.done.txt 2>/dev/null
  grep -m1 -i -A8 "fatal" $BASE/$n/log.solver
  echo "  meanT at end: $(tail -1 $BASE/$n/postProcessing/meanT/0/volFieldValue.dat)"
  [ $n != check_lam5 ] && python3 $SRC/profile_summary.py $BASE/$n
  echo
done
