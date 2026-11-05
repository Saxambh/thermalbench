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
  # a solver already working in this case (an older batch still alive, as the lab's orphans of
  # 2026-11-02): leave it alone instead of deleting the folder under it
  local p; for p in $(pgrep buoyantPimple); do
    [ "$(readlink /proc/$p/cwd)" = "$(readlink -f $c)" ] && { echo "$c SKIPPED: a solver is already running in it" >> $LOG; return 0; }
  done
  # PCM_STAGGER=<s>: start cases at least <s> s apart, so many coded-source compilations do not
  # run at once (memory on pc3, 2026-11-03); only the first wave is affected
  if [ -n "$PCM_STAGGER" ]; then ( flock 9; sleep $PCM_STAGGER ) 9> "$LOG.stagger"; fi
  # PCM_MAX_SOLVERS=<n> (2026-11-05): start only while fewer than n solvers run in this batch folder
  # (all batches sharing it), e.g. when a batch is restarted while cases of the old one still run.
  # One case at a time passes the gate, with a pause so its solver is up before the next count.
  if [ -n "$PCM_MAX_SOLVERS" ]; then
    ( flock 8
      while [ "$(for q in $(pgrep buoyantPimple); do readlink /proc/$q/cwd; done | grep -c "^$PWD/")" -ge "$PCM_MAX_SOLVERS" ]; do sleep 60; done
      sleep 90 ) 8> "$LOG.slots"
  fi
  # Resume after an interruption (2026-11-05, pc3 switched off by mistake: its restart threw away
  # hours per case): an unfinished case with a solved time > 0, made with the same arguments
  # (batch_args.txt; older cases have none and are accepted, case ids are unique per design), is
  # continued from its latest complete time on one core by pcm_continue.sh, which also exports,
  # slims and writes DONE. Only if that fails does the case start over. PCM_FRESH=1 always starts over.
  if [ -z "$PCM_FRESH" ] && [ -f $c/case.json ] && { [ -f $c/log.solver ] || [ -f $c/log.solver.gz ]; } \
     && { [ ! -f $c/batch_args.txt ] || [ "$(cat $c/batch_args.txt)" = "$*" ]; } \
     && ls $c | grep -E '^[0-9][0-9.e+-]*$' | grep -qvx '0'; then
    echo "$c resuming after an interruption from t = $(ls $c | grep -E '^[0-9][0-9.e+-]*$' | sort -g | tail -1) $(date -u '+%F %H:%M')" >> $LOG
    bash $SCR/pcm_continue.sh $c 1; local rc=$?
    [ $rc = 0 ] && return 0
    [ $rc = 2 ] && return 1          # solved, export failed: keep the case (EXPORT_FAIL is in the log)
    cp $c/log.continue $c.resume_failed.log 2>/dev/null
    echo "$c resume failed (log kept as $c.resume_failed.log), starting over" >> $LOG
  fi
  rm -rf $c
  local t0=$(date +%s)
  python3 $SCR/make_pcm_case.py $c "$@" > $c.gen.log 2>&1 || { echo "$c GEN_FAIL" >> $LOG; return 1; }
  echo "$*" > $c/batch_args.txt
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
