#!/bin/bash
# Extra seeds 3 and 4 on the PCM material-transfer splits (finemesh_2026-11-10/PLAN.md, Part B):
# fno, unet, transolver, each plain and --hybrid, x ood_material, ood_material_r x seeds 3, 4 = 24 jobs,
# the paper's settings (run_final_pcm.sh COMMON; FNO/Transolver 60 epochs, U-Net 100; Transolver lr 3e-4).
# Run from anywhere:  bash extra_seeds_2026-11-10/run_seeds.sh <lab|pc4|pc3|pc6|pc7>
set -e
cd "$(dirname "$0")/.."
M=manifest_pcm.json
PY=${PY:-~/venvs/tbml-gpu/bin/python}
COMMON="--manifest $M --amp --batch 16 --threads 2"
W=${1:?worker}
OUT=results_pcm_s34; mkdir -p $OUT
# fixed assignment: job k (in this order) goes to WORKERS[k mod 6]; lab (fastest GPU) is listed twice, so lab 8 jobs, others 4
WORKERS=(lab pc4 pc3 lab pc6 pc7)
JOBS=()
for split in ood_material ood_material_r; do for model in transolver unet fno; do for flags in "" "--hybrid"; do for seed in 3 4; do
  JOBS+=("$model $split $seed $flags"); done; done; done; done
echo "=== seeds worker $W $(date -u '+%F %H:%M') UTC on $(hostname), manifest md5 $(md5sum $M | cut -c1-12)" >> $OUT/run.log
python3 check_data.py $M >> $OUT/run.log 2>&1 || { echo "data check failed" >> $OUT/run.log; exit 1; }
for ((k=0; k<${#JOBS[@]}; k++)); do
  [ "${WORKERS[$((k % ${#WORKERS[@]}))]}" = "$W" ] || continue
  read -r model split seed flags <<< "${JOBS[$k]}"
  ep=60; lr=""; [ $model = unet ] && ep=100; [ $model = transolver ] && lr="--lr 3e-4"
  name=$model$( [ -n "$flags" ] && echo _hybrid || true )_s$seed
  if [ -f $OUT/$split.json ] && python3 -c "import json,sys; sys.exit(0 if '$name' in json.load(open('$OUT/$split.json'))['results'] else 1)"; then
    echo "--- $split: $name already done, skipped" >> $OUT/run.log; continue; fi
  echo "--- $split: $name ($ep epochs) $(date -u '+%H:%M')" >> $OUT/run.log
  $PY pcm_train.py --model $model $flags --split $split --seed $seed --epochs $ep $lr $COMMON --outdir $OUT 2>&1 \
    | grep -vE "^epoch +[0-9]*[1-9] " >> $OUT/run.log
done
echo "=== worker $W done $(date -u '+%F %H:%M') UTC" >> $OUT/run.log
