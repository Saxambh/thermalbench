#!/bin/bash
# Run a PCM design table: one case per row of a pcm_design.py CSV, N at a time, slowest
# (largest estimated core-hours) first so stragglers start early. Per case: generate, mesh,
# solve until melted (auto-stop), export thermbench.h5 + metrics.json, then mark DONE.
# Restartable: cases with DONE are skipped; an unfinished case is regenerated from scratch.
# Usage: pcm_batch.sh <design.csv> <out_dir> <jobs>     (on the machine that runs it)
unset LD_LIBRARY_PATH
CSV=$(readlink -f "$1"); OUT=$2; JOBS=${3:-4}
SCR=$(dirname "$(readlink -f "$0")")
# OpenFOAM's bashrc takes the caller's arguments as config files and sources them (it ran the
# CSV lines as commands in the 2026-11-02 pilot launch, harmlessly), so clear them first
set --
source /usr/lib/openfoam/openfoam2606/etc/bashrc
mkdir -p "$OUT" && cd "$OUT" || exit 1
LOG=$OUT/batch.log

one() {   # case_id args...
  local c=$1; shift
  [ -f $c/DONE ] && return 0
  # PCM_STAGGER=<s>: start cases at least <s> s apart, so many coded-source compilations do not
  # run at once (memory on pc3, 2026-11-03); only the first wave is affected
  if [ -n "$PCM_STAGGER" ]; then ( flock 9; sleep $PCM_STAGGER ) 9> "$LOG.stagger"; fi
  rm -rf $c
  local t0=$(date +%s)
  python3 $SCR/make_pcm_case.py $c "$@" > $c.gen.log 2>&1 || { echo "$c GEN_FAIL" >> $LOG; return 1; }
  ( cd $c && blockMesh > log.blockMesh 2>&1 && { [ ! -f system/topoSetDict ] || topoSet > log.topoSet 2>&1; } \
      && nice -n 5 buoyantPimpleFoam > log.solver 2>&1 ) || { echo "$c SOLVER_FAIL $(grep -m1 -A3 FATAL $c/log.solver | tr '\n' ' ' | cut -c1-200)" >> $LOG; return 1; }
  local wall=$(( $(date +%s) - t0 ))
  local f=$(ls $c/postProcessing/liquidFraction/*/volFieldValue.dat | head -1)
  local lf=$(awk '!/^#/{x=$2; t=$1} END{printf "%.4f at %.0f s", x, t}' $f)
  python3 $SCR/export_pcm_case.py $c > $c/export.log 2>&1 || { echo "$c EXPORT_FAIL" >> $LOG; return 1; }
  # slim after a successful export (decided 2026-11-02, disk space): drop the raw OpenFOAM
  # time directories (all but 0/) and the compiled code, gzip the solver log. Kept: case
  # setup (0, system, constant), postProcessing, logs, case.json, metrics.json, thermbench.h5,
  # so the case can be rerun exactly. Set PCM_KEEP_RAW=1 to keep everything.
  if [ -z "$PCM_KEEP_RAW" ]; then
    find $c -mindepth 1 -maxdepth 1 -type d -regex '.*/[0-9][0-9.e+-]*' ! -name 0 -exec rm -rf {} +
    gzip -f $c/log.solver
  fi
  rm -rf $c/dynamicCode
  touch $c/DONE
  echo "$c ok wall ${wall} s, liquid fraction $lf | $(tail -1 $c/export.log)" >> $LOG
}
export -f one; export SCR LOG PCM_KEEP_RAW PCM_STAGGER

echo "batch $(basename $CSV) started $(date -u '+%F %H:%M') UTC, $JOBS jobs" >> $LOG
python3 - "$CSV" <<'PY' | xargs -P $JOBS -L 1 bash -c 'one "$@"' _
import csv, sys
rows = sorted(csv.DictReader(open(sys.argv[1])), key=lambda r: -float(r["core_h_est"]))
for r in rows:
    print(r["case_id"], r["args"])
PY
echo "batch $(basename $CSV) finished $(date -u '+%F %H:%M') UTC" >> $LOG
