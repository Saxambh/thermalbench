#!/bin/bash
# Referee fixes, tank CFD on one PC: runs the "<run_id> <variant>" lines of a job file with tank_verify.sh
# (design_v2_full.csv, the dataset's own list) into ~/of_runs/referee_2026-11-10, N at a time.
#   run_tank_cfd.sh <jobfile> <N>        TV_NP=<cores> for parallel solver runs (inlet test)
J=$(readlink -f "$1"); N=${2:-4}
mkdir -p ~/of_runs/referee_2026-11-10
xargs -P $N -L 1 bash -c 'bash ~/thermbench/scripts/tank_verify.sh "$0" "$1" ~/thermbench_verify/design_v2_full.csv ~/of_runs/referee_2026-11-10' < $J
echo "$(date -u '+%F %H:%M') $(basename $J) finished" >> ~/of_runs/referee_2026-11-10/batch.log
