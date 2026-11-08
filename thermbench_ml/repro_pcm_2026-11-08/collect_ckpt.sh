#!/bin/bash
# Release checkpoints for the PCM family (8 November 2026): copy every neural checkpoint from the worker that
# produced its stored score (the "sources" field of the merged results), never from another copy.
# Writes ../results_pcm_release/ckpt/ and ckpt_sources.tsv (split, name, worker, md5).
cd "$(dirname "$(readlink -f "$0")")/.."
OUT=results_pcm_release/ckpt; mkdir -p $OUT
declare -A HOST=([lab]=labpc [pc3]=saxam@pc3 [pc4]=saxam@pc4 [pc6]=saxam@pc6 [pc7]=saxam@pc7 [laptop]=)
python3 - > /tmp/pcm_ckpt_list.tsv <<'PY'
import json
for d, sub in (("results_pcm_merged", "results_pcm"), ("results_pcm_ts_merged", "results_pcm_ts")):
    for s in ("random", "ood_fins", "ood_drive", "ood_material", "ood_material_r", "ood_tilt"):
        r = json.load(open(f"{d}/{s}.json"))
        for name, w in sorted(r["sources"].items()):
            if any(name.startswith(m) for m in ("fno", "unet", "transolver")):
                print(s, name, w, sub, sep="\t")
PY
echo "$(wc -l < /tmp/pcm_ckpt_list.tsv) checkpoints listed"
: > repro_pcm_2026-11-08/ckpt_sources.tsv
while IFS=$'\t' read -r s name w sub; do
  f=ckpt_pcm_${name}_${s}.pt; h=${HOST[$w]-MISSINGHOST}
  if [ "$h" = MISSINGHOST ]; then echo "unknown worker $w for $s/$name"; continue; fi
  if [ -z "$h" ]; then cp "$sub/ckpt/$f" $OUT/ || echo "MISSING laptop $sub/ckpt/$f"
  else scp -q "$h:thermbench_ml/$sub/ckpt/$f" $OUT/ < /dev/null || echo "MISSING $w $sub/ckpt/$f"; fi
  printf '%s\t%s\t%s\t%s\n' "$s" "$name" "$w" "$(md5sum $OUT/$f 2>/dev/null | cut -c1-32)" >> repro_pcm_2026-11-08/ckpt_sources.tsv
done < /tmp/pcm_ckpt_list.tsv
echo "copied: $(ls $OUT | wc -l)"
