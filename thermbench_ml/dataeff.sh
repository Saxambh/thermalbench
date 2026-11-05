#!/bin/bash
# Data-efficiency study for the tank benchmark (2026-11-05, Saxam: "start the data efficiency study on pc6").
# How much training data do the networks need? The main model (fno --hybrid --canon) and plain fno are
# trained on 5, 10, 25 and 50 % of the random split's training runs (train.py --train-frac: nested by
# design point, a run kept at 5 % is also in the 10 % set), 3 seeds each; 100 % is the main benchmark
# run (run_final.sh, results_merged). Same settings as run_final.sh: 60 epochs, bf16, batch 16, data on
# the GPU, frozen manifest, the same validation and test runs. Epochs are fixed, so smaller sets also
# get fewer optimiser steps (as in most data-efficiency studies; noted in the paper).
#   bash dataeff.sh plan        list the jobs
#   bash dataeff.sh             run them (skips jobs already in results_dataeff/random.json)
# Log results_dataeff/run_final_dataeff.log (watch_training.sh shows it). 24 jobs, ~8-9 h on an RTX 4060.
cd "$(dirname "$0")"
M=manifest_full_h5mm.json
PY=${PY:-~/venvs/tbml-gpu/bin/python}
OUT=results_dataeff
COMMON="--manifest $M --gpu-data --amp --batch 16 --threads 2 --split random --epochs 60 --outdir $OUT"
jobs() {
  for flags in "--hybrid --canon" ""; do
    for frac in 0.05 0.1 0.25 0.5; do
      for seed in 0 1 2; do echo "$frac $seed $flags"; done
    done
  done
}
if [ "$1" = plan ]; then jobs; exit 0; fi
[ -f $M ] || { echo "frozen manifest $M missing"; exit 1; }
mkdir -p $OUT
exec > >(tee -a $OUT/run_final_dataeff.log) 2>&1
echo "=== run_final worker $(hostname)-dataeff $(date -u '+%F %H:%M') UTC, manifest md5 $(md5sum $M | cut -c1-12)"
python3 check_data.py $M || { echo "data check failed"; exit 1; }
mapfile -t J < <(jobs)
echo "${#J[@]} jobs for dataeff"
for j in "${J[@]}"; do
  read -r frac seed flags <<< "$j"
  name=fno$([[ $flags == *hybrid* ]] && echo _hybrid)$([[ $flags == *canon* ]] && echo _canon)_f$(python3 -c "print(round(100*$frac))")$([ $seed != 0 ] && echo _s$seed)
  if [ -f $OUT/random.json ] && python3 -c "import json,sys; sys.exit(0 if '$name' in json.load(open('$OUT/random.json'))['results'] else 1)"; then
    echo "--- random: $name already done, skipped"; continue
  fi
  echo "--- random: fno $flags train-frac $frac seed $seed (60 epochs) $(date -u '+%H:%M')"
  $PY train.py --model fno $flags --seed $seed --train-frac $frac $COMMON | grep -vE "^epoch +[0-9]*[1-9] "
done
echo "=== worker dataeff done $(date -u '+%F %H:%M') UTC"
