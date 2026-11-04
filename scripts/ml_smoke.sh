#!/bin/bash
cd "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml"
for m in fno unet; do
  nice -n 10 ~/venvs/tbml/bin/python train.py --model $m --roots ~/of_runs/full_h5mm ~/of_runs/pilot_v2 \
    --epochs 2 --stride 30 --width 16 --threads 3 2>&1 | tail -5
done
