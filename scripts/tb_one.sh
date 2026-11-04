#!/bin/bash
# Status of one machine's share of the full 5 mm batch (called by tb_all.sh, locally or over ssh).
# Usage: tb_one.sh <design.csv>
B=~/of_runs/full_h5mm
L=$1
moved=$(ls -d $B/*/MOVED_TO_* 2>/dev/null | wc -l)
total=$(( $(tail -n +2 "$L" | wc -l) - moved ))
done_n=$(( $(ls $B/*/DONE 2>/dev/null | wc -l) - moved ))
pct=$(( total > 0 ? 100 * done_n / total : 0 ))
bar=$(printf '%*s' $(( pct * 30 / 100 )) '' | tr ' ' '#'); pad=$(printf '%*s' $(( 30 - pct * 30 / 100 )) '' | tr ' ' '.')
echo "$done_n of $total done [$bar$pad] $pct%   load $(cut -d' ' -f1 /proc/loadavg)"
line=""; n=0
for c in $B/T*/; do
  c=${c%/}; [ -f $c/DONE ] && continue; [ -f $c/log.solver ] || continue
  t=$(tail -c 3000 $c/log.solver | grep '^Time = ' | tail -1 | awk '{printf "%.0f", $3}')
  e=$(grep -m1 '^endTime' $c/system/controlDict | awk '{printf "%.0f", $2}')
  [ -n "$t" ] && [ -n "$e" ] && [ "$e" -gt 0 ] || continue
  line+=$(printf '  %-10s %3d%%' $(basename $c) $(( 100 * t / e ))); n=$((n + 1))
  if [ $n -eq 4 ]; then echo "$line"; line=""; n=0; fi
done
[ -n "$line" ] && echo "$line"
for C in ~/of_runs/lou3d/*/; do
  Lg=$(ls -t $C/log* 2>/dev/null | head -1); [ -n "$Lg" ] || continue
  [ $(( $(date +%s) - $(stat -c %Y "$Lg") )) -lt 600 ] || continue
  t=$(tail -c 5000 "$Lg" | grep '^Time = ' | tail -1 | awk '{printf "%.1f", $3}')
  echo "  3D validation $(basename $C): $t of 750 s simulated ($(awk -v t=$t 'BEGIN{printf "%.1f", 100*t/750}')%)"
done
