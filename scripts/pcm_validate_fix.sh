#!/bin/bash
# PCM validation re-run with the final solver set-up (2026-11-04, Saxam: option A). Same model
# choices as the 500-case design: p_rghFinal relTol 0 + maxIter 200 (the fix), mushy constant 1e6,
# melting range (octadecane 27.99-28.01, lauric 43.5-48.2), conducting aluminium fins (k 130), 0.5 mm.
#   vogel_fix       Vogel & Thess 2019 B-2D (octadecane), 3.5 h, dt 0.1   -> validation_Vogel2019_pcm.md
#   kam_n0/n1/n3    Kamkari & Shokouhmand 2014, 70 C, 0/1/3 fins            -> validation_Kamkari2014_fins.md
#   kam_t45/t90     Kamkari, Shokouhmand & Bruno 2014, 45 deg and heated from below (tilt = 90 - theta)
# Run on pc4 in ~/of_runs/pcm_valfix, 6 single-core jobs.   bash pcm_validate_fix.sh
unset LD_LIBRARY_PATH
set --
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SCR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
W=~/of_runs/pcm_valfix; mkdir -p $W && cd $W || exit 1
K="--material lauric --W 0.05 --H 0.12 --right wall --top wall --tw 70 --t0 25 --h 0.0005 --fin-len 0.025 --fin-t 0.004 --melt-range 43.5,48.2 --Cu 1e6 --end 12000 --write 300 --stop-at 0.995"
run() {  # name args...
  local c=$1; shift
  rm -rf $c && python3 $SCR/make_pcm_case.py $c "$@" > $c.gen.log 2>&1 || { echo "$c GEN_FAIL" >> valfix.log; return; }
  grep -q "relTol *0;" $c/system/fvSolution || { echo "$c: fix missing in fvSolution" >> valfix.log; return; }
  ( cd $c && blockMesh > log.blockMesh 2>&1 && { [ ! -f system/topoSetDict ] || topoSet > log.topoSet 2>&1; } \
      && nice -n 5 buoyantPimpleFoam > log.solver 2>&1 )
  echo "$c finished $(date -u '+%F %H:%M') UTC, exit $?" >> valfix.log
}
echo "started $(date -u '+%F %H:%M') UTC (make_pcm_case md5 $(md5sum < $SCR/make_pcm_case.py | cut -c1-8))" >> valfix.log
run vogel_fix --h 0.0005 --maxdt 0.1 --melt-range 27.99,28.01 --Cu 1e6 --end 12600 --write 300 &
run kam_n0 $K &
run kam_n1 $K --nfins 1 --fin-y 0.060 --fin-model conduct --k-fin 130 &
run kam_n3 $K --nfins 3 --fin-y 0.029,0.060,0.091 --fin-model conduct --k-fin 130 &
run kam_t45 $K --tilt 45 &
run kam_t90 $K --tilt 90 &
wait
echo "all done $(date -u '+%F %H:%M') UTC" >> valfix.log
