#!/bin/bash
# Every 2 h: copy finished PCM cases (light files only) from pc4, pc3 and the lab pilot to the
# laptop (~/tb_data/<machine>/...), run pcm_qc.py on everything, log a summary and any batch
# failures to ~/tb_data/pcm_qc.log. Started 2026-11-03; stop: kill the PID in the log.
#   setsid nohup bash pcm_sync_qc.sh > /dev/null 2>&1 < /dev/null &
unset LD_LIBRARY_PATH
QC="$(dirname "$(readlink -f "$0")")/pcm_qc.py"
LOG=~/tb_data/pcm_qc.log; mkdir -p ~/tb_data
echo "$(date -u '+%F %H:%M') pcm_sync_qc pid $$ started" >> $LOG
pull() {  # host remote_dir local_dir
  local list; list=$(timeout 60 ssh -o BatchMode=yes -o ConnectTimeout=15 $1 "cd $2 2>/dev/null && ls -d */DONE 2>/dev/null | cut -d/ -f1; true" < /dev/null) || { echo "  $1: not reachable" >> $LOG; return; }
  [ -z "$list" ] && { echo "  $1: no finished cases yet" >> $LOG; return; }
  mkdir -p $3
  echo "$list" | sed 's|$|/DONE|; p; s|DONE$|case.json|; p; s|case.json$|metrics.json|; p; s|metrics.json$|thermbench.h5|; p; s|thermbench.h5$|export.log|' \
    | timeout 3000 rsync -a --ignore-missing-args --files-from=- $1:$2/ $3/ 2>> $LOG
  timeout 60 scp -q $1:$2/batch.log $3/batch.log 2>/dev/null
  echo "  $1: $(echo "$list" | wc -l) finished, $(grep -c FAIL $3/batch.log 2>/dev/null) batch failures$(grep FAIL $3/batch.log 2>/dev/null | tail -3 | sed 's/^/ | /' | tr '\n' ' ')" >> $LOG
}
while true; do
  echo "$(date -u '+%F %H:%M') sync" >> $LOG
  pull saxam@pc4 of_runs/pcm_full/runs ~/tb_data/pc4/pcm_full
  pull saxam@pc3 of_runs/pcm_full/runs ~/tb_data/pc3/pcm_full
  pull labpc of_runs/pcm_pilot ~/tb_data/lab/pcm_pilot
  # 2026-11-04 pcm_rebalance.py: the lab and pc5 also run pc4 cases (pcm_more.sh)
  pull labpc of_runs/pcm_full/runs ~/tb_data/lab/pcm_full
  pull pc5 of_runs/pcm_full/runs ~/tb_data/pc5/pcm_full
  pull saxam@pc6 of_runs/pcm_full/runs ~/tb_data/pc6/pcm_full    # pc6 added 2026-11-05
  pull saxam@pc7 of_runs/pcm_full/runs ~/tb_data/pc7/pcm_full    # pc7 added 2026-11-06
  [ -f ~/of_runs/pcm_full/runs/batch.log ] && echo "  laptop: $(ls ~/of_runs/pcm_full/runs/*/DONE 2>/dev/null | wc -l) finished, $(grep -c FAIL ~/of_runs/pcm_full/runs/batch.log) batch failures" >> $LOG
  nice -n 10 python3 "$QC" ~/tb_data/pc4/pcm_full ~/tb_data/pc3/pcm_full ~/of_runs/pcm_full/runs ~/tb_data/lab/pcm_pilot ~/tb_data/lab/pcm_full ~/tb_data/pc5/pcm_full ~/tb_data/pc6/pcm_full ~/tb_data/pc7/pcm_full 2>&1 \
    | grep -v "No such file\|no finished cases" | sed 's/^/  qc /' >> $LOG
  sleep 7200
done
