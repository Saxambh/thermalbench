#!/bin/bash
# Referee fix (thermbench_ml/referee_fixes_2026-11-10/PLAN.md): Kamkari, Shokouhmand & Bruno 2014 tilted cases
# rerun at the dataset's lauric settings, mushy constant 5e6 (the 4 November runs, pcm_validate_fix.sh, used 1e6).
# Otherwise identical to pcm_validate_fix.sh: 0.5 mm, melting range 43.5-48.2, 70 C wall, 25 C start; tilt = 90 - theta.
# Run on pc4 in ~/of_runs/pcm_tilt5e6, 2 single-core jobs.   bash kamkari_tilt_5e6.sh
unset LD_LIBRARY_PATH
set --
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SCR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
W=~/of_runs/pcm_tilt5e6; mkdir -p $W && cd $W || exit 1
K="--material lauric --W 0.05 --H 0.12 --right wall --top wall --tw 70 --t0 25 --h 0.0005 --fin-len 0.025 --fin-t 0.004 --melt-range 43.5,48.2 --Cu 5e6 --end 12000 --write 300 --stop-at 0.995"
run() {
  local c=$1; shift
  rm -rf $c && python3 $SCR/make_pcm_case.py $c "$@" > $c.gen.log 2>&1 || { echo "$c GEN_FAIL" >> tilt.log; return; }
  grep -q "relTol *0;" $c/system/fvSolution || { echo "$c: fix missing in fvSolution" >> tilt.log; return; }
  ( cd $c && blockMesh > log.blockMesh 2>&1 && { [ ! -f system/topoSetDict ] || topoSet > log.topoSet 2>&1; } \
      && nice -n 5 buoyantPimpleFoam > log.solver 2>&1 )
  echo "$c finished $(date -u '+%F %H:%M') UTC, exit $?" >> tilt.log
}
echo "started $(date -u '+%F %H:%M') UTC (make_pcm_case md5 $(md5sum < $SCR/make_pcm_case.py | cut -c1-8))" >> tilt.log
run kam_t45_cu5e6 $K --tilt 45 &
run kam_t90_cu5e6 $K --tilt 90 &
wait
echo "all done $(date -u '+%F %H:%M') UTC" >> tilt.log
