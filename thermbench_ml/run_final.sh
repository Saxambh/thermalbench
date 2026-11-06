#!/bin/bash
# Final benchmark training on the frozen full 5 mm dataset (decided 2026-11-01):
#   8 models, a 2 x 2 ablation (physics base yes/no x canonical frame yes/no) per architecture
#   (fno, fno_canon, fno_hybrid, fno_hybrid_canon: 60 epochs; the same four for unet: 100
#   epochs) x 4 splits x 3 seeds = 96 jobs, bf16, batch 16, data held on the GPU, every run
#   restricted to the frozen manifest. On ood_mode (seed 0): fno 18.0 K, fno_canon 1.75 K,
#   fno_hybrid 2.98 K, fno_hybrid_canon 0.66 K.
#   The canonical-frame hybrid (train.py --canon) is the main model since 2026-11-02 (Saxam).
# Distributed over the four GPUs (2026-11-03, Saxam): ~215 GPU-hours on the laptop's RTX 4060
# alone (~9 days), ~1.5 days on all four. Jobs are assigned deterministically (longest first, to
# the GPU where it would finish first, by relative speed); U-Net on the three large splits needs
# more than 8 GB and only goes to the 12 GB cards. The laptop also runs the non-neural baselines.
# Each machine writes its own results/; merge_results.py combines them on the laptop.
#   bash run_final.sh plan               # print the assignment and expected hours per GPU
#   bash run_final.sh <laptop|pc3|lab|pc4|pc5a|pc5b>
#   bash run_final.sh check              # 60 vs 150 epoch check (done 2026-11-03 on the rehearsal set)
set -e
cd "$(dirname "$0")"
M=manifest_full_h5mm.json
PY=${PY:-~/venvs/tbml-gpu/bin/python}
COMMON="--manifest $M --gpu-data --amp --batch 16 --threads 2"

plan() {  # prints "<worker> <model> <split> <seed> <epochs> <flags...>" lines, longest job first per worker
python3 - "$1" <<'EOF'
import heapq, sys
# speed vs laptop, GB. Measured 2026-11-04 (1-epoch test, rehearsal set, machines busy with CFD):
# lab FNO 43 s / U-Net 46 s, pc4 65 s / 70 s, laptop 48 s / 63 s. pc3 not yet measured.
GPUS = {"laptop": (1.0, 8), "pc3": (1.0, 8), "lab": (1.25, 12), "pc4": (0.8, 12),
        # pc5 (friend's PC, added 2026-11-04): 2x RTX 3080 Ti 12 GB, one worker per GPU. 1-epoch test on
        # 102 runs: FNO 4.0, U-Net 3.6 ms/sample (laptop 8.0 / 10.4 on the rehearsal set) = 2.0x / 2.9x;
        # 1.8 used (small set, both GPUs busy at once)
        "pc5a": (1.8, 12), "pc5b": (1.8, 12)}
FRAC = {"random": 0.80, "ood_flow": 0.81, "ood_geom": 0.76, "ood_mode": 0.45}          # share of runs in train
EPOCH_H = {"fno": 81 / 3600 / 0.80, "unet": 107 / 3600 / 0.80}   # h per epoch at train share 1 (measured 2026-11-03)
jobs = []
for split in FRAC:
    for model, flags, ep in (("fno", "", 60), ("fno", "--canon", 60), ("fno", "--hybrid", 60), ("fno", "--hybrid --canon", 60),
                             ("unet", "", 100), ("unet", "--canon", 100), ("unet", "--hybrid", 100), ("unet", "--hybrid --canon", 100)):
        for seed in range(3):
            h = ep * EPOCH_H[model] * FRAC[split] + 0.08
            big = model == "unet" and FRAC[split] > 0.7
            jobs.append((h, model, split, seed, ep, flags, big))
free = {g: 0.0 for g in GPUS}
out = {g: [] for g in GPUS}
for h, model, split, seed, ep, flags, big in sorted(jobs, reverse=True):
    # 2026-11-04 test: U-Net on the 8 GB laptop GPU, 702 train runs, peak 5.3 GB (4.7 GB at 505);
    # linear to ~1,000 train runs gives ~6.2 GB, so large U-Net jobs fit on 8 GB cards too
    ok = [g for g in GPUS if GPUS[g][1] >= 8 or not big]
    g = min(ok, key=lambda g: free[g] + h / GPUS[g][0])
    free[g] += h / GPUS[g][0]
    out[g].append(f"{model} {split} {seed} {ep} {flags}".strip())
if sys.argv[1] == "summary":
    for g in GPUS:
        print(f"{g:7s} {len(out[g]):3d} jobs, about {free[g]:5.1f} h")
else:
    print("\n".join(out[sys.argv[1]]))
EOF
}

if [ "$1" = plan ]; then plan summary; exit 0; fi
[ -f $M ] || { echo "freeze the manifest first: python freeze_manifest.py"; exit 1; }
# pc5 runs two workers side by side (one per GPU): each gets its own GPU and results folder
OUT=results
case "$1" in pc5a) export CUDA_VISIBLE_DEVICES=0; OUT=results_pc5a ;; pc5b) export CUDA_VISIBLE_DEVICES=1; OUT=results_pc5b ;; esac
mkdir -p $OUT
exec > >(tee -a $OUT/run_final.log) 2>&1

if [ "$1" = check ]; then
  echo "=== epoch check $(date -u '+%F %H:%M') UTC"
  for ep in 60 150; do
    $PY train.py --model fno --hybrid --canon --split random --seed 0 --epochs $ep $COMMON --outdir results_epochcheck_ep$ep \
      | grep -vE "^epoch +[0-9]*[1-9] " | sed "s/^/[ep$ep] /"
  done
  exit 0
fi

W=${1:?worker: laptop, pc3, lab, pc4, pc5a, pc5b, pc6 or pc7}
echo "=== run_final worker $W $(date -u '+%F %H:%M') UTC on $(hostname), manifest md5 $(md5sum $M | cut -c1-12)"
python3 check_data.py $M || { echo "data check failed: not all frozen runs are here and intact"; exit 1; }
if [ "$W" = laptop ]; then
  # baselines already scored (a restarted worker, 2026-11-05) are not run again (~2 h of CPU)
  for split in random ood_flow ood_geom ood_mode; do
    if [ -f $OUT/$split.json ] && python3 -c "import json,sys; r=json.load(open('$OUT/$split.json'))['results']; sys.exit(0 if {'initial','knn','nn','idw','rbf'} <= set(r) else 1)"; then
      echo "--- $split: baselines already scored, skipped"; continue; fi
    $PY evaluate.py --split $split --manifest $M; done
fi
# Rebalanced list (2026-11-05: pc5's GPU 0 failed and the laptop dropped out, rebalance_final.py):
# jobs_<worker>.txt, if present, replaces the planned list. Before each job the worker waits until
# its GPU is free (a job of an earlier copy of this worker, or pc6's data-efficiency study), so a
# worker can be switched to a new list while its current job finishes.
if [ -f jobs_$W.txt ]; then mapfile -t JOBS < <(grep . jobs_$W.txt); else mapfile -t JOBS < <(plan $W); fi
busy() { if [[ $W == pc5? ]]; then pgrep -f -- "--outdir $OUT\$" > /dev/null; else pgrep -f "train.py|dataeff.sh" > /dev/null; fi; }
echo "${#JOBS[@]} jobs for $W"
for j in "${JOBS[@]}"; do
  read -r model split seed ep flags <<< "$j"
  while busy; do sleep 60; done
  # || true: under set -e a seed-0 job made this assignment fail and ended the worker (2026-11-05)
  name=$model$( [[ $flags == *hybrid* ]] && echo _hybrid )$( [[ $flags == *canon* ]] && echo _canon )$( [ $seed != 0 ] && echo _s$seed || true )
  if [ -f $OUT/$split.json ] && python3 -c "import json,sys; sys.exit(0 if '$name' in json.load(open('$OUT/$split.json'))['results'] else 1)"; then
    echo "--- $split: $name already done, skipped"; continue
  fi
  echo "--- $split: $model $flags seed $seed ($ep epochs) $(date -u '+%H:%M')"
  $PY train.py --model $model $flags --split $split --seed $seed --epochs $ep $COMMON --outdir $OUT \
    | grep -vE "^epoch +[0-9]*[1-9] "
done
echo "=== worker $W done $(date -u '+%F %H:%M') UTC"
