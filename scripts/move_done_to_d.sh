#!/bin/bash
# Move finished cases from a laptop scratch folder inside Ubuntu to D: (2026-11-06, Saxam: "use d from now",
# laptop C: nearly full). Every 10 min: each case with DONE is copied to <dest>, checked (same file count and
# bytes), then removed from the scratch folder. Stops when <n> cases have been moved. Log <dest>/moved.log
#   setsid nohup bash move_done_to_d.sh ~/of_runs/pcm_rerunB /mnt/d/ThermBench_data/pcm_rerunB 7 > /dev/null 2>&1 &
S=${1:?scratch dir}; D=${2:?dest}; N=${3:-1000}
mkdir -p "$D"; L="$D/moved.log"
echo "$(date -u '+%F %H:%M') watcher pid $$: $S -> $D, until $N cases" >> "$L"
while true; do
  for d in "$S"/P*/; do
    c=$(basename "$d"); [ -f "$S/$c/DONE" ] || continue
    rsync -rt --no-perms "$S/$c/" "$D/$c/" || { echo "$(date -u '+%H:%M') $c copy FAILED" >> "$L"; continue; }
    a=$(find "$S/$c" -type f | wc -l); b=$(find "$D/$c" -type f | wc -l)
    sa=$(du -sb --apparent-size "$S/$c" | cut -f1); sb=$(du -sb --apparent-size "$D/$c" | cut -f1)
    if [ "$a" = "$b" ] && [ "$sa" = "$sb" ]; then rm -rf "$S/$c"; echo "$(date -u '+%H:%M') $c moved ($b files, $sb bytes)" >> "$L"
    else echo "$(date -u '+%H:%M') $c copy differs ($a/$b files), kept in $S" >> "$L"; fi
  done
  [ -f "$S/batch.log" ] && cp "$S/batch.log" "$D/batch.log"
  [ "$(grep -c ' moved (' "$L")" -ge "$N" ] && { echo "$(date -u '+%F %H:%M') all $N moved, watcher ends" >> "$L"; exit 0; }
  sleep 600
done
