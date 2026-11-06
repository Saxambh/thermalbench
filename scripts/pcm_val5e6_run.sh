#!/bin/bash
# Kamkari validation at the exact dataset settings (2026-11-06, Saxam: "start case 1 now and case 2 at 02:30").
# Dataset settings = make_pcm_case.py as used for the 500 cases (pressure fix option A built in) with the
# frozen lauric choices: melting range 43.5-48.2 C, mushy constant 5e6, conducting Al fins k 130.
# Run in parallel (scotch); decomposition changes round-off only.
#   val_run.sh <name> <np> <generator args...>        in ~/of_runs/pcm_val5e6, log val.log
unset LD_LIBRARY_PATH
c=$1; NP=$2; shift 2
SCR=$(dirname "$(readlink -f "$0")")
source /usr/lib/openfoam/openfoam2606/etc/bashrc
W=~/of_runs/pcm_val5e6; mkdir -p $W && cd $W || exit 1
rm -rf $c; python3 $SCR/make_pcm_case.py $c "$@" > $c.gen.log 2>&1 || { echo "$c GEN_FAIL" >> val.log; exit 1; }
grep -q "relTol *0;" $c/system/fvSolution || { echo "$c: pressure fix missing" >> val.log; exit 1; }
echo "$(date -u '+%F %H:%M') $c started on $(hostname), $NP cores, generator md5 $(md5sum < $SCR/make_pcm_case.py | cut -c1-8): $*" >> val.log
cat > $c/system/decomposeParDict <<E
FoamFile { format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains $NP;
method scotch;
E
t0=$(date +%s)
( cd $c && blockMesh > log.blockMesh 2>&1 && { [ ! -f system/topoSetDict ] || topoSet > log.topoSet 2>&1; } \
   && decomposePar > log.decomposePar 2>&1 && nice -n 5 mpirun -np $NP buoyantPimpleFoam -parallel > log.solver 2>&1 \
   && reconstructPar > log.reconstructPar 2>&1 ); rc=$?
f=$(ls $c/postProcessing/*/*/volFieldValue.dat 2>/dev/null | head -1)
echo "$(date -u '+%F %H:%M') $c finished, exit $rc, wall $(( $(date +%s) - t0 )) s, last liquid fraction $(awk '!/^#/{x=$2; t=$1} END{printf "%.4f at %.0f s", x, t}' $f 2>/dev/null)" >> val.log
