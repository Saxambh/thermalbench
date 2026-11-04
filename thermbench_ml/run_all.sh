#!/bin/bash
# Full benchmark pass: gather runs from all machines, score the non-neural baselines and train
# the neural ones on every split (SEEDS seeds each), then write the tables.
# Usage: bash run_all.sh [EPOCHS] [SEEDS]      (defaults 150, 3). Log: results/run_all.log
EPOCHS=${1:-150}
SEEDS=${2:-3}
cd "$(dirname "$0")"
mkdir -p results
exec > >(tee -a results/run_all.log) 2>&1
echo "=== run_all $(date -u '+%F %H:%M') UTC, epochs $EPOCHS, seeds $SEEDS"
bash gather.sh
PY=~/venvs/tbml-gpu/bin/python
for split in random ood_flow ood_geom ood_mode; do
  echo "--- $split: non-neural baselines"
  $PY evaluate.py --split $split
  for model in fno unet; do
    for hyb in "" --hybrid; do
      for seed in $(seq 0 $((SEEDS - 1))); do
        echo "--- $split: $model $hyb seed $seed"
        $PY train.py --model $model --split $split --epochs $EPOCHS --seed $seed $hyb | grep -vE "^epoch +[0-9]*[1-9] "
      done
    done
  done
done
$PY tables.py
echo "=== done $(date -u '+%F %H:%M') UTC"
