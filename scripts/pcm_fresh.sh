#!/bin/bash
# Fresh run of one PCM case from t = 0 with the dataset settings (no solver change), in parallel
# (2026-11-07, Saxam: rerun P0495, which broke after a resume). Same steps as pcm_rerun.sh otherwise.
#   pcm_fresh.sh <case_id> <np> <design.csv> <out_dir>      log: <case>/log.rerun
unset LD_LIBRARY_PATH
C=$1; NP=${2:-4}; CSV=$(readlink -f "$3"); OUT=$(readlink -f "$4")
SCR=$(dirname "$(readlink -f "$0")")
set --
source /usr/lib/openfoam/openfoam2606/etc/bashrc
cd "$OUT" || exit 1
LOG=$OUT/batch.log
ARGS=$(python3 -c "import csv,sys; print(next(r['args'] for r in csv.DictReader(open('$CSV')) if r['case_id']=='$C'))") || exit 1
[ -e $C ] && { echo "$C exists in $OUT, not touched"; exit 1; }
t0=$(date +%s)
eval python3 $SCR/make_pcm_case.py $C $ARGS > $C.gen.log 2>&1 || { echo "$C GEN_FAIL (rerun)" >> $LOG; exit 1; }
echo "$ARGS" > $C/batch_args.txt
cd $C
exec >> log.rerun 2>&1
echo "$(date -u '+%F %H:%M') rerun $C on $(hostname), $NP cores, dataset solver settings (fresh run)"
cat > system/decomposeParDict <<E
FoamFile { format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains $NP;
method scotch;
E
ok=1
blockMesh > log.blockMesh 2>&1 && { [ ! -f system/topoSetDict ] || topoSet > log.topoSet 2>&1; } \
  && decomposePar > log.decomposePar 2>&1 \
  && nice -n 5 mpirun -np $NP buoyantPimpleFoam -parallel > log.solver 2>&1 \
  && reconstructPar > log.reconstructPar 2>&1 || ok=0
cd ..
if [ $ok = 0 ]; then echo "$C SOLVER_FAIL (rerun) $(grep -m1 -A3 FATAL $C/log.solver | tr '\n' ' ' | cut -c1-200)" >> $LOG; exit 1; fi
rm -rf $C/processor*
wall=$(( $(date +%s) - t0 ))
f=$(ls $C/postProcessing/liquidFraction/*/volFieldValue.dat | head -1)
lf=$(awk '!/^#/{x=$2; t=$1} END{printf "%.4f at %.0f s", x, t}' $f)
python3 $SCR/export_pcm_case.py $C > $C/export.log 2>&1 || { echo "$C EXPORT_FAIL (rerun)" >> $LOG; exit 2; }
find $C -mindepth 1 -maxdepth 1 -type d -regex '.*/[0-9][0-9.e+-]*' ! -name 0 -exec rm -rf {} +
gzip -f $C/log.solver
rm -rf $C/dynamicCode
touch $C/DONE
echo "$C ok (fresh rerun, dataset settings, on $NP cores) wall ${wall} s, liquid fraction $lf | $(tail -1 $C/export.log)" >> $LOG
