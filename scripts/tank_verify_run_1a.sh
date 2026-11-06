#!/bin/bash
# Stage 1A driver (2026-11-06): 7 dataset runs x 4 variants, 7 at a time, on pc4.
J=~/thermbench_verify/jobs_1a.txt; OUT=~/of_runs/tank_verify
echo "$(date -u '+%F %H:%M') stage 1A start, $(wc -l < $J) runs, 7 at a time" >> $OUT/batch.log
xargs -P 7 -L 1 bash -c 'bash ~/thermbench/scripts/tank_verify.sh "$0" "$1" ~/thermbench_verify/design_h5mm_full.csv ~/of_runs/tank_verify' < $J
echo "$(date -u '+%F %H:%M') stage 1A finished" >> $OUT/batch.log
