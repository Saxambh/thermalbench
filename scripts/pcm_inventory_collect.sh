#!/bin/bash
# one TSV row per PCM case folder found on this machine: case folder kind done moved qc energy_err t_melt solver size mtime
H=$(hostname)
for base in ~/of_runs/pcm_full/runs /mnt/d/ThermBench_data/tb_data/pc5/pcm_full ~/of_runs/pcm_rerunB ~/of_runs/pcm_rerunC ~/of_runs/pcm_rerunD /mnt/d/ThermBench_data/pcm_rerunB ~/of_runs/pcm_full/halffix ~/of_runs/pcm_rerunB_halffix; do
  [ -d $base ] || continue
  for d in $base/P[0-9][0-9][0-9][0-9]; do [ -d $d ] || continue; c=$(basename $d)
    done_=$([ -f $d/DONE ] && echo 1 || echo 0); mv=$(ls $d/MOVED_* 2>/dev/null | head -1 | xargs -r basename)
    qc=$(python3 -c "import json;print(json.load(open('$d/qc.json')).get('status',''))" 2>/dev/null)
    l=$(tail -1 $d/export.log 2>/dev/null); e=$(echo "$l" | grep -o "max error [0-9.na]*" | tail -1 | cut -d" " -f3); tm=$(echo "$l" | grep -o "t_melt [0-9.na]*" | cut -d" " -f2)
    [ -f $d/metrics.json ] && { e=$(python3 -c "import json;m=json.load(open('$d/metrics.json'));print(round(100*m['energy_balance_max_abs_err'],3), m['t_melt_s'])" 2>/dev/null); tm=${e#* }; e=${e% *}; }
    solver=dataset; [ -f $d/SOLVER_NOTE.txt ] && solver=PCG_fix; grep -q "fresh run" $d/log.rerun 2>/dev/null && solver=fresh_rerun
    [ -f $d/thermbench.h5.series_bug ] && solver="$solver+series_repaired"
    fx=$(python3 -c "import re,sys;p='$d/system/fvSolution';import os
if not os.path.exists(p): print('fix' if 'v1_relTol' not in p else 'nofix'); sys.exit()
m=re.search(r'p_rghFinal\s*\{[^}]*?relTol\s+([0-9.eE+-]+)\s*;', open(p).read(), re.S); print('fix' if m and float(m.group(1))==0 else 'nofix')" 2>/dev/null); solver="$solver/$fx"
    sz=$(stat -c %s $d/thermbench.h5 2>/dev/null || echo 0); mt=$(stat -c %Y $d/thermbench.h5 2>/dev/null || echo 0)
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$c" "$H" "$base" "$done_" "${mv:--}" "${qc:--}" "${e:--}" "${tm:--}" "$solver" "$sz" "$mt"
  done
done
