#!/bin/bash
# Pull finished runs (light files only: DONE, case.json, metrics.json, qc.json, thermbench.h5)
# from the lab and pc3 into ~/tb_data/<machine>/ on the laptop. Placeholders (MOVED_*) and
# unfinished runs are not copied. Safe to rerun: rsync only transfers new or changed files.
# Usage: bash gather.sh [batch ...]   (default: full_h5mm and full_h5mm_x, the runs
# redistributed on 2026-11-03 to a second lab batch and the laptop)
unset LD_LIBRARY_PATH
for B in ${@:-full_h5mm full_h5mm_x}; do
  for m in lab pc3; do
    [ $m = pc3 ] && [ $B = full_h5mm_x ] && continue   # pc3 has no redistributed runs
    host=$([ $m = lab ] && echo labpc || echo saxam@pc3)
    mkdir -p ~/tb_data/$m/$B
    # finished, real runs only (DONE + thermbench.h5, no MOVED_* marker)
    ssh -o BatchMode=yes $host "cd ~/of_runs/$B && for d in T*/; do d=\${d%/}; [ -f \$d/DONE ] && [ -f \$d/thermbench.h5 ] && ! ls \$d | grep -q MOVED && echo \$d; done" > /tmp/tb_$m.txt
    rsync -a --files-from=<(sed 's|$|/DONE|; p; s|DONE$|case.json|; p; s|case.json$|metrics.json|; p; s|metrics.json$|thermbench.h5|' /tmp/tb_$m.txt) \
          $host:of_runs/$B/ ~/tb_data/$m/$B/
    # qc.json appears later than DONE: copy the ones that exist, ignore missing
    rsync -a --ignore-missing-args --files-from=<(sed 's|$|/qc.json|' /tmp/tb_$m.txt) $host:of_runs/$B/ ~/tb_data/$m/$B/
    echo "$m $B: $(wc -l < /tmp/tb_$m.txt) finished runs, local copy $(du -sh ~/tb_data/$m/$B | cut -f1)"
  done
  echo "laptop $B: $(for d in ~/of_runs/$B/T*/; do [ -f $d/thermbench.h5 ] && [ -f $d/DONE ] && echo; done 2>/dev/null | wc -l) finished runs (used in place)"
done
