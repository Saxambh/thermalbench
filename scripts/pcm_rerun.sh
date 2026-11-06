#!/bin/bash
# Rerun one PCM case from t = 0 with a stronger pressure solver, in parallel (2026-11-06, Saxam: P0124 option 1).
# P0124 (lauric, 5 fins of 42 mm, Ra 1.95e8) stalled on pc5: with the standard GAMG p_rgh solver the pressure
# residual stayed ~0.8-0.9 at every step, every solve hit the iteration cap, spurious velocities held the time
# step at ~0.014 s and the run slowed to ~5 s simulated per hour after t ~ 1450 s. Lab test from the t = 1378 s
# save (~/of_runs/p0124_test): p_rgh PCG + DIC converges (residual 0.011, time step 0.30 s) and passes that
# point; the melt fraction agrees with the stalled run up to there. Healthy cases have residuals 0.003-0.025
# with the standard setting, so only this case is changed. Physics, mesh and every other setting are as in
# pcm_batch.sh; the change is recorded in SOLVER_NOTE.txt and batch.log.
#   pcm_rerun.sh <case_id> <np> <design.csv> <out_dir>      log: <case>/log.rerun
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
echo "$(date -u '+%F %H:%M') rerun $C on $(hostname), $NP cores, p_rgh PCG + DIC"
foamDictionary system/fvSolution -entry solvers/p_rgh/solver -set PCG > /dev/null
foamDictionary system/fvSolution -entry solvers/p_rgh/preconditioner -set DIC > /dev/null
foamDictionary system/fvSolution -entry solvers/p_rgh/smoother -remove > /dev/null
# 2026-11-06 fix (found in the audit): p_rghFinal is its own entry once the file is written out, so setting only
# p_rgh left every final pressure solve on GAMG + GaussSeidel. Set p_rghFinal explicitly and check both.
foamDictionary system/fvSolution -entry solvers/p_rghFinal/solver -set PCG > /dev/null
foamDictionary system/fvSolution -entry solvers/p_rghFinal/preconditioner -set DIC > /dev/null
foamDictionary system/fvSolution -entry solvers/p_rghFinal/smoother -remove > /dev/null 2>&1
foamDictionary system/fvSolution -entry solvers/p_rghFinal/maxIter -set 2000 > /dev/null
# (foamDictionary -expand prints the whole file in v2606, so the two blocks are read out of it with awk)
key() { foamDictionary -expand system/fvSolution 2>/dev/null | awk -v e="$1" -v k="$2" '$1==e{f=1;next} f&&$1=="}"{exit} f&&$1==k{sub(/;$/,"",$2); print $2; exit}'; }
for e in p_rgh p_rghFinal; do
  s=$(key $e solver); p=$(key $e preconditioner)
  [ "$s" = PCG ] && [ "$p" = DIC ] || { echo "$e is '$s'/'$p', not PCG/DIC: stopped"; cd ..; echo "$C SOLVER_SETUP_FAIL (rerun)" >> $LOG; exit 1; }
done
echo "pressure solvers: p_rgh and p_rghFinal both PCG + DIC (checked)"
cat > SOLVER_NOTE.txt <<N
$C was rerun from t = 0 with the pressure solver PCG + DIC for p_rgh and p_rghFinal (p_rghFinal maxIter 2000)
instead of GAMG + GaussSeidel (maxIter 200), on $NP cores, $(date -u '+%F'). Reason: with GAMG the pressure did not converge
(residual ~0.85 every step), the time step collapsed and the run stalled at t ~ 1450 s. Everything else as
in the other cases. See scripts/pcm_rerun.sh.
N
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
echo "$C ok (rerun with p_rgh + p_rghFinal PCG + DIC on $NP cores, SOLVER_NOTE.txt) wall ${wall} s, liquid fraction $lf | $(tail -1 $C/export.log)" >> $LOG
