#!/bin/bash
# Transolver on the PCM benchmark (PLAN.md, amendment 1): plain and --hybrid x 6 splits x 3 seeds = 36 jobs,
# 60 epochs, the same settings as the FNO jobs (run_final_pcm.sh COMMON). Run from thermbench_ml/.
#   bash extra_baselines_2026-11-08/run_transolver_pcm.sh pilot <lr>          # random, plain, seed 0 -> results_pcm_ts_pilot_<lr>
#   LR=<lr> bash extra_baselines_2026-11-08/run_transolver_pcm.sh <worker>    # its share -> results_pcm_ts
set -e
cd "$(dirname "$0")/.."
M=manifest_pcm.json
PY=${PY:-~/venvs/tbml-gpu/bin/python}
COMMON="--manifest $M --amp --batch 16 --threads 2"
if [ "$1" = pilot ]; then
  OUT=results_pcm_ts_pilot_$2; mkdir -p $OUT
  $PY pcm_train.py --model transolver --split random --seed 0 --epochs 60 --lr $2 $COMMON --outdir $OUT > $OUT/train.log 2>&1
  exit 0
fi
W=${1:?worker}; LR=${LR:?set LR from the pilot}
OUT=results_pcm_ts; mkdir -p $OUT
# job k of the 36 goes to worker k mod 6 in this fixed order (jobs sorted by split size, largest first)
WORKERS=(lab pc4 pc3 pc6 pc7 laptop)
JOBS=()
for split in ood_material ood_material_r ood_tilt ood_fins random ood_drive; do for flags in "" "--hybrid"; do for seed in 0 1 2; do
  JOBS+=("$split $seed $flags"); done; done; done
i=0; for w in "${WORKERS[@]}"; do [ "$w" = "$W" ] && break; i=$((i+1)); done
echo "=== transolver pcm worker $W lr $LR $(date -u '+%F %H:%M') UTC on $(hostname), manifest md5 $(md5sum $M | cut -c1-12)" >> $OUT/run.log
for ((k=i; k<${#JOBS[@]}; k+=${#WORKERS[@]})); do
  read -r split seed flags <<< "${JOBS[$k]}"
  name=transolver$( [ -n "$flags" ] && echo _hybrid || true )$( [ $seed != 0 ] && echo _s$seed || true )
  if [ -f $OUT/$split.json ] && python3 -c "import json,sys; sys.exit(0 if '$name' in json.load(open('$OUT/$split.json'))['results'] else 1)"; then
    echo "--- $split: $name already done, skipped" >> $OUT/run.log; continue; fi
  echo "--- $split: $name $(date -u '+%H:%M')" >> $OUT/run.log
  $PY pcm_train.py --model transolver $flags --split $split --seed $seed --epochs 60 --lr $LR $COMMON --outdir $OUT 2>&1 \
    | grep -vE "^epoch +[0-9]*[1-9] " >> $OUT/run.log
done
echo "=== worker $W done $(date -u '+%F %H:%M') UTC" >> $OUT/run.log
