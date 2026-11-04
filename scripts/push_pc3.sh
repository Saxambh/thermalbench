#!/bin/bash
# Pre-stage the tank training data on pc3 (light files only), so pc3 can train as soon as the
# batch ends. Safe to rerun: rsync only sends new or changed files. Run again after the batch.
#   laptop runs  ~/of_runs/full_h5mm       -> pc3 ~/tb_data/laptop/full_h5mm
#   lab runs     (gather.sh to the laptop)  -> pc3 ~/tb_data/lab/full_h5mm
# Afterwards the files read here are dropped from the laptop's page cache (laptop lag fix).
unset LD_LIBRARY_PATH
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
ML="/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/thermbench_ml"
B=full_h5mm
bash "$ML/gather.sh" $B
for d in ~/of_runs/$B/T*/; do d=${d%/}; d=${d##*/}
  [ -f ~/of_runs/$B/$d/DONE ] && [ -f ~/of_runs/$B/$d/thermbench.h5 ] && ! ls ~/of_runs/$B/$d | grep -q MOVED && echo $d
done > /tmp/tb_laptop.txt
ssh -o BatchMode=yes saxam@pc3 "mkdir -p ~/tb_data/laptop/$B ~/tb_data/lab/$B" < /dev/null
ionice -c3 nice -n 10 rsync -a --files-from=<(sed 's|$|/DONE|; p; s|DONE$|case.json|; p; s|case.json$|metrics.json|; p; s|metrics.json$|thermbench.h5|' /tmp/tb_laptop.txt) \
      ~/of_runs/$B/ saxam@pc3:tb_data/laptop/$B/
rsync -a --ignore-missing-args --files-from=<(sed 's|$|/qc.json|' /tmp/tb_laptop.txt) ~/of_runs/$B/ saxam@pc3:tb_data/laptop/$B/
ionice -c3 nice -n 10 rsync -a ~/tb_data/lab/$B/ saxam@pc3:tb_data/lab/$B/
python3 $S/uncache_all.py > /dev/null 2>&1
ssh -o BatchMode=yes saxam@pc3 "for m in laptop lab; do echo \"pc3 copy of \$m: \$(ls -d ~/tb_data/\$m/$B/T* | wc -l) runs, \$(du -sh ~/tb_data/\$m/$B | cut -f1)\"; done
  echo \"pc3 own finished runs: \$(ls ~/of_runs/$B/T*/DONE | wc -l)\"" < /dev/null
echo "pushed $(date -u '+%F %H:%M') UTC"
