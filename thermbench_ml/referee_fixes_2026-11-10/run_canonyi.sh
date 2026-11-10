#!/bin/bash
# Referee fix 3c (PLAN.md, amendment): test of the mechanism found by diag_canon.py. The canonical frame mirrors the
# initial field of a pre-stratified discharge run but not its interface-height input y_init; train.py --canon-yi
# mirrors it too. fno and unet, --canon --canon-yi, on ood_mode, seeds 0-2 = 6 jobs (FNO 60 epochs, U-Net 100), the
# final benchmark's settings. Output results_canonyi/. Queued behind this GPU's ceiling jobs.
#   bash referee_fixes_2026-11-10/run_canonyi.sh <lab|pc4|pc3|pc6|pc7>
set -e
cd "$(dirname "$0")/.."
M=manifest_full_h5mm.json
PY=${PY:-~/venvs/tbml-gpu/bin/python}
COMMON="--manifest $M --gpu-data --amp --batch 16 --threads 2"
W=${1:?worker}; OUT=results_canonyi; mkdir -p $OUT
declare -A JOBS=([lab]="unet|0 fno|0" [pc4]="unet|1" [pc3]="fno|1" [pc6]="unet|2" [pc7]="fno|2")
while pgrep -f "[r]un_ceiling" > /dev/null; do sleep 120; done
echo "=== canonyi worker $W $(date -u '+%F %H:%M') UTC on $(hostname), train.py md5 $(md5sum train.py | cut -c1-12)" >> $OUT/run.log
for j in ${JOBS[$W]}; do
  IFS='|' read -r model seed <<< "$j"
  ep=60; [ $model = unet ] && ep=100
  echo "--- ood_mode: ${model}_canonyi seed $seed ($ep epochs) $(date -u '+%H:%M')" >> $OUT/run.log
  $PY train.py --model $model --canon --canon-yi --split ood_mode --seed $seed --epochs $ep $COMMON --outdir $OUT 2>&1 \
    | grep -vE "^epoch +[0-9]*[1-9] " >> $OUT/run.log
done
echo "=== worker $W done $(date -u '+%F %H:%M') UTC" >> $OUT/run.log
