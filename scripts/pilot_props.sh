#!/bin/bash
# Pilot: real water properties (buoyantPimpleFoam) vs constant-property Boussinesq.
# Boussinesq references already exist: laminar 600 s (L1 run) and sst_buoyk 150 s.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
BASE=~/of_runs/pilot_props; mkdir -p $BASE
run() {
  local n=$1 s=$2; shift 2
  rm -rf $BASE/$n; python3 $SRC/make_tank_case.py $BASE/$n "$@" > $BASE/$n.gen.txt
  cd $BASE/$n; blockMesh > log.blockMesh 2>&1
  local S=$SECONDS; $s > log.solver 2>&1
  echo "$n rc=$? wall=$((SECONDS-S))s steps=$(grep -c '^Time =' log.solver)" > $BASE/$n.done.txt
}
run real_lam buoyantPimpleFoam --uin 0.02 --end 600 --write 10 --props real &
run bous_lam buoyantBoussinesqPimpleFoam --uin 0.02 --end 600 --write 10 &
run real_sst buoyantPimpleFoam --uin 0.1 --end 150 --write 15 --props real --turb kOmegaSST --buoy &
wait
for n in real_lam bous_lam real_sst; do
  cat $BASE/$n.gen.txt $BASE/$n.done.txt
  grep -m1 -A8 "FOAM FATAL" $BASE/$n/log.solver
  echo "  meanT at end: $(tail -1 $BASE/$n/postProcessing/meanT/0/volFieldValue.dat)"
  python3 $SRC/profile_summary.py $BASE/$n
  echo
done
echo "Boussinesq turbulent reference: ~/of_runs/thermbench_turb_2606/sst_buoyk"
