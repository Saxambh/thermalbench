#!/bin/bash
# Stage the final training on the GPU machines from the laptop (the hub; direct copies between
# pc3, lab and pc4 go through a relay at < 2 MB/s, laptop -> pc4 ~16 MB/s, measured 2026-11-03).
# Copies: the Python environment (lab, pc4; pc3 has it), this code folder, and every finished tank
# run (light files) the machine does not already hold. Safe to rerun: rsync sends only what is new.
#   bash stage_ml.sh [venv] [code] [data]      (default: all three)
unset LD_LIBRARY_PATH
HERE="$(dirname "$(readlink -f "$0")")"
# pc5 (friend's PC, Ubuntu 26.04, user sure, ssh alias pc5) has its own venv built there (Python 3.14)
W=${STAGE_TO:-"labpc:lab saxam@pc3:pc3 saxam@pc4:pc4 pc5:pc5"}   # STAGE_TO="pc5:pc5" stages one machine only
STEPS=${@:-venv code data}
R="ionice -c3 nice -n 10 rsync -a"
light() { sed 's|$|/DONE|; p; s|DONE$|case.json|; p; s|case.json$|metrics.json|; p; s|metrics.json$|qc.json|; p; s|qc.json$|thermbench.h5|'; }
finished() { for d in "$1"/T*/; do d=${d%/}; [ -f $d/DONE ] && [ -f $d/thermbench.h5 ] && ! ls $d | grep -q MOVED && basename $d; done; }
for w in $W; do
  h=${w%%:*}; m=${w##*:}
  if [[ " $STEPS " == *" venv "* ]] && [ $m != pc3 ] && [ $m != pc5 ]; then
    ssh -o BatchMode=yes $h 'mkdir -p ~/venvs' < /dev/null; $R ~/venvs/tbml-gpu/ $h:venvs/tbml-gpu/ && echo "$m: venv $(ssh -o BatchMode=yes $h '~/venvs/tbml-gpu/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"' < /dev/null)"
  fi
  if [[ " $STEPS " == *" code "* ]]; then
    $R --delete --exclude "*.pt" --exclude "results*" --exclude "__pycache__" --exclude "manifest_*.json" "$HERE/" $h:thermbench_ml/ && echo "$m: code synced"
  fi
  # pc5 sits behind Tailscale's relay (~0.3 MB/s): it gets temperature-only copies instead (make_slim.py, freeze_all.sh step 5)
  if [[ " $STEPS " == *" data "* ]] && [ $m != pc5 ]; then
    for src in "laptop:$HOME/of_runs/full_h5mm" "laptop:$HOME/of_runs/full_h5mm_x" "lab:$HOME/tb_data/lab/full_h5mm" \
               "lab:$HOME/tb_data/lab/full_h5mm_x" "pc3:$HOME/tb_data/pc3/full_h5mm"; do
      o=${src%%:*}; dir=${src#*:}; B=$(basename $dir)
      [ $o = $m ] && continue          # the machine's own runs are already there
      [ -d "$dir" ] || continue
      finished "$dir" > /tmp/stage_${m}_${o}_${B}.txt
      ssh -o BatchMode=yes $h "mkdir -p ~/tb_data/$o/$B" < /dev/null
      light < /tmp/stage_${m}_${o}_${B}.txt | $R --ignore-missing-args --files-from=- "$dir/" $h:tb_data/$o/$B/
      echo "$m: $o/$B $(wc -l < /tmp/stage_${m}_${o}_${B}.txt) runs staged $(date -u +%H:%M)"
    done
  fi
done
echo "staging done $(date -u '+%F %H:%M') UTC"
