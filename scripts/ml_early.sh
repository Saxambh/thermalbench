#!/bin/bash
# Early sanity training on the runs finished so far (detached; log in ~/of_runs/ml_early.log)
cd "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml"
{
date
~/venvs/tbml/bin/python evaluate.py --roots ~/of_runs/full_h5mm ~/of_runs/pilot_v2 --split random --stride 10
for m in fno unet; do
  nice -n 10 ~/venvs/tbml-gpu/bin/python train.py --model $m --roots ~/of_runs/full_h5mm ~/of_runs/pilot_v2 \
    --epochs 150 --stride 10 --width 32 --threads 2 2>&1 | grep -v Warning | awk 'NR<=3 || /epoch +(50|100|150) / || /rmse/'
done
date
} > ~/of_runs/ml_early.log 2>&1
