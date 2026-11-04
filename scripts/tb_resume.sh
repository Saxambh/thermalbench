#!/bin/bash
# After a reboot or power cut: restart whatever ThermalStorageBench work on this machine is unfinished.
# Run at boot by tb-resume.service (tb_resume_install.sh); safe to run by hand any time, since a
# job that is already running is left alone. Finished runs (DONE) are skipped by the batch
# scripts; unfinished ones start again from scratch (tank, PCM) or from the last saved time (3D).
#   tb_resume.sh <laptop|lab|pc3|pc4> [--dry]        log: ~/tb_resume.log
M=$1; DRY=$2; LOG=~/tb_resume.log
R="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
SB=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
TS=~/thermbench/scripts
log() { echo "$(date -u '+%F %H:%M') [$M] $*" >> $LOG; [ -n "$DRY" ] && echo "$*"; }
running() {  # any process (not a shell wrapper or this script) whose command line matches $1
  for p in $(pgrep -f -- "$1"); do
    [ "$p" = $$ ] && continue
    c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null)
    case "$c" in *tb_resume*|"bash -c"*|"") ;; *) return 0;; esac
  done; return 1
}
alldone() {  # column csv dir: every id in the list has DONE in dir (moved-away placeholders count)
  python3 - "$1" "$2" "$3" <<'PY'
import csv, os, sys
col, f, d = sys.argv[1], sys.argv[2], os.path.expanduser(sys.argv[3])
if not os.path.exists(f): sys.exit(0)
sys.exit(0 if all(os.path.exists(f"{d}/{r[col]}/DONE") for r in csv.DictReader(open(f))) else 1)
PY
}
start() {  # name pattern cwd command...
  local name=$1 pat=$2 cwd=$3; shift 3
  if running "$pat"; then log "$name: running, left alone"; return; fi
  log "$name: STARTING $*"
  [ -n "$DRY" ] && return
  (cd "$cwd" && setsid nohup "$@" >> ~/tb_resume_$name.out 2>&1 < /dev/null &)
  sleep 5
}
lou_done() {  # last saved time (processor0) has reached endTime; "End" in the log also follows a pause
  local e=$(awk '/^endTime/{gsub(";",""); print $2}' "$1/system/controlDict" 2>/dev/null)
  local t=$(ls "$1/processor0" 2>/dev/null | grep -E "^[0-9.e+-]+$" | sort -g | tail -1)
  [ -n "$e" ] && [ -n "$t" ] && awk -v t="$t" -v e="$e" 'BEGIN{exit !(t >= e - 1e-6)}'
}
tank() {  # name csv dir jobs cwd launcher...: start the batch and its QC loop unless finished
  local name=$1 csv=$2 dir=$3; shift 3
  if alldone run_id "$csv" "$dir"; then log "$name: finished"; return 0; fi
  start "$name" "run_batch.py.*$(basename "$csv")" "$@"
  start "${name}_qc" "qc_loop.sh.*$dir" ~ bash $QCL $QCR $dir
  return 1
}
pcm() {  # jobs; tanks_done (0/1): start the PCM batch, or its after-tank watcher
  local J=$1 tanks=$2 csv=~/thermbench/pcm_full_$M.csv
  [ -f $csv ] || return
  if alldone case_id $csv ~/of_runs/pcm_full/runs; then log "pcm: finished"; return; fi
  if [ $tanks = 0 ]; then
    mkdir -p ~/of_runs/pcm_full/runs
    start pcm "pcm_batch.sh.*pcm_full_$M" ~/of_runs/pcm_full env PCM_STAGGER=30 bash $TS/pcm_batch.sh $csv ~/of_runs/pcm_full/runs $J
  else
    start pcm_watch "pcm_after_tank.sh $M" ~ bash $TS/pcm_after_tank.sh $M $J
  fi
}
more() {  # jobs: this machine's share of pc4's queue (pcm_rebalance.py 2026-11-04), after its tank runs
  local csv=~/thermbench/pcm_more_$M.csv
  [ -f $csv ] || return
  if alldone case_id $csv ~/of_runs/pcm_full/runs; then log "pcm_more: finished"; return; fi
  start pcm_more "pcm_more.sh $M" ~ bash $TS/pcm_more.sh $M $1 after_tank
}
log "=== resume check (boot $(uptime -s))"
case $M in
  laptop)
    QCL=$SB/qc_loop.sh; QCR=$SB/qc_runs.py; t=0
    tank tank "$R/design_v2_full_laptop_n2.csv" ~/of_runs/full_h5mm ~ python3 $SB/run_batch.py "$R/design_v2_full_laptop_n2.csv" ~/of_runs/full_h5mm --jobs 8 || t=1
    tank tankx "$R/design_v2_full_laptopx_n2.csv" ~/of_runs/full_h5mm_x ~ python3 $SB/run_batch.py "$R/design_v2_full_laptopx_n2.csv" ~/of_runs/full_h5mm_x --jobs 8 || t=1
    lou_done ~/of_runs/lou3d/sst && log "lou3d sst: finished" || start lou3d "lou3d_run.sh" ~/of_runs/lou3d bash $SB/lou3d_run.sh
    pcm 16 $t
    more 8
    start sync "pcm_sync_qc.sh" ~ bash "$R/scripts/pcm_sync_qc.sh"
    start dash "tb_dash_collect.py" ~ bash "$R/scripts/tb_dash.sh" ;;
  lab)
    QCL=$TS/qc_loop.sh; QCR=$TS/qc_runs.py; t=0
    tank tank ~/thermbench/design_v2_full_lab_n2.csv ~/of_runs/full_h5mm ~/thermbench python3 scripts/run_batch.py design_v2_full_lab_n2.csv ~/of_runs/full_h5mm --jobs 14 || t=1
    tank tankx ~/thermbench/design_v2_full_labx_n2.csv ~/of_runs/full_h5mm_x ~/thermbench python3 scripts/run_batch.py design_v2_full_labx_n2.csv ~/of_runs/full_h5mm_x --jobs 8 || t=1
    # laby: queued laptopx + pc3 runs moved to the lab (rebalance4.py, 2026-11-04), same run folder as labx
    tank tanky ~/thermbench/design_v2_full_laby_n2.csv ~/of_runs/full_h5mm_x ~/thermbench python3 scripts/run_batch.py design_v2_full_laby_n2.csv ~/of_runs/full_h5mm_x --jobs 16 || t=1
    tank tankz ~/thermbench/design_v2_full_labz_n2.csv ~/of_runs/full_h5mm_x ~/thermbench python3 scripts/run_batch.py design_v2_full_labz_n2.csv ~/of_runs/full_h5mm_x --jobs 8 || t=1
    alldone case_id $TS/pcm_pilot.csv ~/of_runs/pcm_pilot && log "pilot: finished" || \
      start pilot "pcm_batch.sh.*pcm_pilot" $TS bash $TS/pcm_batch.sh $TS/pcm_pilot.csv ~/of_runs/pcm_pilot 8
    if lou_done ~/of_runs/lou3d/sst_finelow; then log "lou3d finelow: finished"
    elif [ $t = 0 ]; then start lou3d "lou3d_run_lab.sh" ~ bash $TS/lou3d_run_lab.sh
    else start pcm_watch "pcm_after_tank.sh lab" ~ bash $TS/pcm_after_tank.sh lab 12; fi   # resumes lou3d after the tanks
    more 12
    ;;
  pc3)
    QCL=$TS/qc_loop.sh; QCR=$TS/qc_runs.py; t=0
    tank tank ~/thermbench/design_v2_full_pc3_n2.csv ~/of_runs/full_h5mm ~/thermbench python3 scripts/run_batch.py design_v2_full_pc3_n2.csv ~/of_runs/full_h5mm --jobs 16 || t=1
    pcm 24 0; more 4 ;;   # extra list 4 jobs: 28 PCM jobs on 28 threads after the tanks (2026-11-04)   # pc3 runs PCM alongside its tank runs from 2026-11-03 (split 2)
  pc4)
    pcm 30 0 ;;
  *) echo "usage: tb_resume.sh <laptop|lab|pc3|pc4> [--dry]"; exit 1 ;;
esac
log "=== done"
