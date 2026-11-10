#!/bin/bash
# Referee fix 3 (PLAN.md): the discharge ceiling. Train on the diagnostic split mode_ceiling (splits.py): half of the
# discharge designs held out, the other half plus all charge runs in training. 4 models x 3 seeds = 12 jobs with the
# final benchmark's settings (run_final.sh COMMON; FNO 60 epochs, U-Net 100):
#   fno_canon, unet_canon, fno_hybrid_canon, unet_hybrid_canon.
# Compared afterwards with the ood_mode (charge-only) checkpoints on the same held-out runs (ceiling_compare.py).
#   bash referee_fixes_2026-11-10/run_ceiling.sh <lab|pc4|pc3|pc6|pc7>
set -e
cd "$(dirname "$0")/.."
M=manifest_full_h5mm.json
PY=${PY:-~/venvs/tbml-gpu/bin/python}
COMMON="--manifest $M --gpu-data --amp --batch 16 --threads 2"
W=${1:?worker}; OUT=results_ceiling; mkdir -p $OUT
# 2026-11-10: the first launch split "--hybrid --canon" at the space (those jobs failed at once); flags are now
# comma-joined, done jobs are skipped, and the relaunch waits for the first launch's job still running on this GPU
while pgrep -f "[t]rain.py --model .* --split mode_ceiling" > /dev/null; do sleep 120; done
declare -A JOBS=(
  [lab]="unet|--hybrid,--canon|0 unet|--canon|0 fno|--hybrid,--canon|2"
  [pc4]="unet|--hybrid,--canon|1 fno|--hybrid,--canon|0"
  [pc6]="unet|--hybrid,--canon|2 fno|--canon|0 fno|--canon|2"
  [pc7]="unet|--canon|1 fno|--hybrid,--canon|1"
  [pc3]="unet|--canon|2 fno|--canon|1"
)
echo "=== ceiling worker $W $(date -u '+%F %H:%M') UTC on $(hostname), manifest md5 $(md5sum $M | cut -c1-12)" >> $OUT/run.log
for j in ${JOBS[$W]}; do
  IFS='|' read -r model flags seed <<< "$j"; flags=${flags//,/ }
  ep=60; [ $model = unet ] && ep=100
  name=$model$( [[ $flags == *hybrid* ]] && echo _hybrid || true )_canon$( [ $seed != 0 ] && echo _s$seed || true )
  if [ -f $OUT/mode_ceiling.json ] && python3 -c "import json,sys; sys.exit(0 if '$name' in json.load(open('$OUT/mode_ceiling.json'))['results'] else 1)"; then
    echo "--- $name already done, skipped" >> $OUT/run.log; continue; fi
  echo "--- mode_ceiling: $model $flags seed $seed ($ep epochs) $(date -u '+%H:%M')" >> $OUT/run.log
  $PY train.py --model $model $flags --split mode_ceiling --seed $seed --epochs $ep $COMMON --outdir $OUT 2>&1 \
    | grep -vE "^epoch +[0-9]*[1-9] " >> $OUT/run.log
done
echo "=== worker $W done $(date -u '+%F %H:%M') UTC" >> $OUT/run.log
