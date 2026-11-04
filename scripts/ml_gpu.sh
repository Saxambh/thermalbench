#!/bin/bash
cd "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml"
EP=${1:-3}
for m in fno unet; do
  nice -n 10 ~/venvs/tbml-gpu/bin/python train.py --model $m --roots ~/of_runs/full_h5mm ~/of_runs/pilot_v2 \
    --epochs $EP --stride 10 --width 32 --threads 2 2>&1 | grep -v Warning | tail -4
done
nvidia-smi --query-gpu=memory.used --format=csv,noheader
