#!/bin/bash
# Bit-identity check for a new OpenFOAM machine (2026-11-04, pc5 container vs pc4): a 5-fin PCM case
# (P0377's settings, conducting fins, tilt 45) run for 30 s simulated; prints md5 of the final T,
# U and alpha fields. Same md5 on two machines = identical results.
#   bash pcm_bitcheck.sh <work_dir>
unset LD_LIBRARY_PATH
set --
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SCR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
W=${BITCHECK_DIR:-$HOME/of_runs/bitcheck}; mkdir -p $W && cd $W && rm -rf case
python3 $SCR/make_pcm_case.py case --material octadecane --W 0.056 --H 0.1 --right wall --top wall --tw 49.57 --t0 13.56 \
  --h 0.0005 --tilt 45 --melt-range 27.99,28.01 --Cu 1e+06 --maxdt 0.5 --nfins 5 --fin-len 0.0235 --fin-t 0.003 \
  --fin-model conduct --k-fin 130 --end 30 --write 30 > gen.log 2>&1 || { echo GEN_FAIL; exit 1; }
cd case && blockMesh > log.blockMesh 2>&1 && { [ ! -f system/topoSetDict ] || topoSet > log.topoSet 2>&1; } \
  && buoyantPimpleFoam > log.solver 2>&1 || { echo SOLVER_FAIL; tail -5 log.solver; exit 1; }
t=$(foamListTimes -latestTime 2>/dev/null | tail -1)
echo "host $(hostname) last time $t; $(grep -c '^Time =' log.solver) steps"
for f in $(ls $t | grep -v uniform); do [ -f $t/$f ] && echo "$f $(md5sum < $t/$f | cut -c1-16)"; done
