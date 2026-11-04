#!/bin/bash
# Final PCM benchmark training on the frozen PCM manifest (option A runs, 2026-11-04), the PCM
# counterpart of run_final.sh: fno and unet, each plain and --hybrid (correction to the Front
# baseline), x 6 splits x 3 seeds = 72 jobs (FNO 60 epochs, U-Net 100, as the tank benchmark),
# bf16. Distributed over the six GPU workers like run_final.sh (one per GPU, two on pc5); each
# writes its own results_pcm*/, merge_results.py combines them. The laptop also runs the
# non-neural PCM baselines (pcm_evaluate.py).
#   bash run_final_pcm.sh plan               # assignment and expected hours per worker
#   bash run_final_pcm.sh <laptop|pc3|lab|pc4|pc5a|pc5b>
set -e
cd "$(dirname "$0")"
M=manifest_pcm.json
PY=${PY:-~/venvs/tbml-gpu/bin/python}
COMMON="--manifest $M --amp --batch 16 --threads 2"

plan() {
python3 - "$1" <<'EOF'
import sys
# GPU speed vs the laptop and memory (GB), as run_final.sh (tank measurements, 2026-11-04)
GPUS = {"laptop": 1.0, "pc3": 1.0, "lab": 1.25, "pc4": 0.8, "pc5a": 1.8, "pc5b": 1.8}
# share of the runs in train per split (pcm_splits.py; dev set 2026-11-02: fins 0.66, drive 0.81,
# material 0.47, material_r 0.44, tilt 0.66)
FRAC = {"random": 0.80, "ood_fins": 0.66, "ood_drive": 0.81, "ood_material": 0.47, "ood_material_r": 0.44, "ood_tilt": 0.66}
# h per epoch on the laptop at train share 1 with 500 runs: measured 2026-11-04 on 41 train runs
# (stride 5, ~23 samples per run): FNO 22.3 s / 950 samples, U-Net 19.6 s (laptop CPU busy with CFD)
SAMPLES = 500 * 23
EPOCH_H = {"fno": SAMPLES * 22.3 / 950 / 3600, "unet": SAMPLES * 19.6 / 950 / 3600}
jobs = []
for split in FRAC:
    for model, flags, ep in (("fno", "", 60), ("fno", "--hybrid", 60), ("unet", "", 100), ("unet", "--hybrid", 100)):
        for seed in range(3):
            jobs.append((ep * EPOCH_H[model] * FRAC[split] + 0.1, model, split, seed, ep, flags))
free = {g: 0.0 for g in GPUS}
out = {g: [] for g in GPUS}
for h, model, split, seed, ep, flags in sorted(jobs, reverse=True):
    g = min(GPUS, key=lambda g: free[g] + h / GPUS[g])
    free[g] += h / GPUS[g]
    out[g].append(f"{model} {split} {seed} {ep} {flags}".strip())
if sys.argv[1] == "summary":
    for g in GPUS:
        print(f"{g:7s} {len(out[g]):3d} jobs, about {free[g]:5.1f} h")
else:
    print("\n".join(out[sys.argv[1]]))
EOF
}

if [ "$1" = plan ]; then plan summary; exit 0; fi
[ -f $M ] || { echo "freeze the PCM manifest first: python pcm_freeze_manifest.py"; exit 1; }
OUT=results_pcm
case "$1" in pc5a) export CUDA_VISIBLE_DEVICES=0; OUT=results_pcm_pc5a ;; pc5b) export CUDA_VISIBLE_DEVICES=1; OUT=results_pcm_pc5b ;; esac
mkdir -p $OUT
exec > >(tee -a $OUT/run_final_pcm.log) 2>&1
W=${1:?worker: laptop, pc3, lab, pc4, pc5a or pc5b}
echo "=== run_final_pcm worker $W $(date -u '+%F %H:%M') UTC on $(hostname), manifest md5 $(md5sum $M | cut -c1-12)"
python3 check_data.py $M || { echo "data check failed: not all frozen PCM runs are here and intact"; exit 1; }
if [ "$W" = laptop ]; then
  for split in random ood_fins ood_drive ood_material ood_material_r ood_tilt; do $PY pcm_evaluate.py --split $split --manifest $M --outdir $OUT; done
fi
mapfile -t JOBS < <(plan $W)
echo "${#JOBS[@]} jobs for $W"
for j in "${JOBS[@]}"; do
  read -r model split seed ep flags <<< "$j"
  name=$model$( [[ $flags == *hybrid* ]] && echo _hybrid )$( [ $seed != 0 ] && echo _s$seed )
  if [ -f $OUT/$split.json ] && python3 -c "import json,sys; sys.exit(0 if '$name' in json.load(open('$OUT/$split.json'))['results'] else 1)"; then
    echo "--- $split: $name already done, skipped"; continue
  fi
  echo "--- $split: $model $flags seed $seed ($ep epochs) $(date -u '+%H:%M')"
  $PY pcm_train.py --model $model $flags --split $split --seed $seed --epochs $ep $COMMON --outdir $OUT \
    | grep -vE "^epoch +[0-9]*[1-9] "
done
echo "=== worker $W done $(date -u '+%F %H:%M') UTC"
