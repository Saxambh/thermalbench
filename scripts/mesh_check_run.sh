#!/bin/bash
# Mesh check driver on the lab (2026-11-06, Saxam: "lets do mesh check first").
# Tank: 5 dataset runs at 2.5 mm and 4 at 10 mm (production numerics); 5 mm baseline = stage 1A p2 runs on pc4.
# PCM: 3 levels 1.0 / 0.5 / 0.25 mm for P0131 and P0301 with W rounded to whole mm (22 / 26 mm) so all
# levels fit, plus P0021 at 1.0 mm (its 0.5 and 0.25 mm runs exist). Not dataset runs: for the order of convergence.
V=~/thermbench_verify
( xargs -P 9 -L 1 bash -c 'bash ~/thermbench/scripts/tank_verify.sh "$0" "$1" ~/thermbench_verify/design_h5mm_full.csv ~/of_runs/tank_mesh' < $V/jobs_mesh.txt
  echo "$(date -u '+%F %H:%M') tank mesh runs finished" >> ~/of_runs/tank_mesh/batch.log ) &
PCM_STAGGER=30 bash ~/thermbench/scripts/pcm_batch.sh $V/pcm_mesh_gci.csv ~/of_runs/pcm_mesh 5
wait
