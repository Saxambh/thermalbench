#!/bin/bash
# PCM freeze in one command (counterpart of freeze_all.sh), run in WSL on the laptop (the hub) once
# all 500 option-A cases have finished. Stops at the first problem.
#   bash pcm_freeze_all.sh --dry    rehearsal: steps 0-3 with a scratch manifest; stages and starts nothing
#   bash pcm_freeze_all.sh          the real freeze: steps 0-5, then PCM training on the six GPU workers
# Steps: 0 every PCM list finished, no PCM solver running   1 pull finished cases to the laptop + pcm_qc.py
#        2 pcm_freeze_manifest.py (QC FAIL and old-solver runs left out)   3 checks: split sizes, loader
#        4 stage: PCM data to lab, pc3, pc4 (rsync), pc5 (temperature + liquid fraction copies via GitHub);
#          code (pc5 via git) and the manifest to all     5 start run_final_pcm.sh on all six workers
# Written 2026-11-04. Log ~/pcm_freeze_all.log. Merge afterwards: python merge_results.py <results_pcm folders>
unset LD_LIBRARY_PATH
DRY=$([ "$1" = --dry ] && echo 1)
ML="$(dirname "$(readlink -f "$0")")"
R="$(dirname "$ML")"
PY=~/venvs/tbml-gpu/bin/python
MAN="$ML/manifest_pcm.json"; [ -n "$DRY" ] && MAN=/tmp/manifest_pcm_dry.json
exec > >(tee -a ~/pcm_freeze_all.log) 2>&1
say() { echo "=== $* ($(TZ=Asia/Kathmandu date +%H:%M) Nepal)"; }
die() { echo "STOP: $*"; exit 1; }
rsh() { ssh -o BatchMode=yes -o ConnectTimeout=20 "$@" < /dev/null; }
HOSTS="laptop: lab:labpc pc3:saxam@pc3 pc4:saxam@pc4 pc5:pc5 pc6:saxam@pc6"   # pc6 added 2026-11-05     # machine:ssh host (laptop local)
say "pcm_freeze_all ${DRY:+DRY RUN }start"
[ -z "$DRY" ] && [ -f "$MAN" ] && die "$MAN already exists (frozen before?); move it away first"

say "0. every PCM list finished, no PCM solver running"
STATE='cd ~/of_runs/pcm_full/runs 2>/dev/null || cd /tmp   # no run folder yet: every listed case still to do
  n=0; d=0; for f in ~/thermbench/pcm_full_$M.csv ~/thermbench/pcm_more_$M.csv; do [ -f $f ] || continue
    for c in $(tail -n +2 $f | cut -d, -f1); do n=$((n+1)); [ -f $c/DONE ] && d=$((d+1)); done; done
  r=0; for p in $(pgrep buoyantPimple); do [[ "$(readlink /proc/$p/cwd)" == */pcm_full/runs/* ]] && r=$((r+1)); done
  echo "$n $d $r"'
left=0; running=0
for x in $HOSTS; do m=${x%%:*}; h=${x#*:}
  s=$(if [ -z "$h" ]; then M=$m bash -c "$STATE"; else rsh $h "M=$m; $STATE"; fi) || die "state of $m (unreachable?)"
  read n d r <<< "$s"; echo "  $m: $d/$n done, $r PCM solvers running"
  left=$((left + n - d)); running=$((running + r))
done
if [ "$left" != 0 ] || [ "$running" != 0 ]; then [ -n "$DRY" ] && echo "(dry run: carrying on)" || die "$left PCM cases not finished, $running solvers running"; fi

say "1. pull finished cases to the laptop and QC them"
pull() {  # host remote_dir local_dir   (as pcm_sync_qc.sh: light files only)
  local list; list=$(rsh $1 "cd $2 2>/dev/null && ls -d */DONE 2>/dev/null | cut -d/ -f1; true") || return 1
  mkdir -p $3; [ -z "$list" ] && return 0
  echo "$list" | sed 's|$|/DONE|; p; s|DONE$|case.json|; p; s|case.json$|metrics.json|; p; s|metrics.json$|thermbench.h5|; p; s|thermbench.h5$|export.log|; p; s|export.log$|system/fvSolution|' \
    | rsync -a --ignore-missing-args --files-from=- $1:$2/ $3/
}
for x in lab:labpc pc3:saxam@pc3 pc4:saxam@pc4 pc5:pc5 pc6:saxam@pc6; do
  pull ${x#*:} of_runs/pcm_full/runs ~/tb_data/${x%%:*}/pcm_full || die "pull from ${x%%:*}"
done
nice python3 "$R/scripts/pcm_qc.py" ~/of_runs/pcm_full/runs ~/tb_data/{lab,pc3,pc4,pc5,pc6}/pcm_full | grep -E "^/|FAIL" | tail -25

say "2. manifest -> $MAN"
cd "$ML" && $PY pcm_freeze_manifest.py --out "$MAN" | tee /tmp/pcm_fz_manifest.txt || die "pcm_freeze_manifest"
grep -q "no QC verdict" /tmp/pcm_fz_manifest.txt && { [ -n "$DRY" ] && echo "(dry run: carrying on)" || { rm -f "$MAN"; die "runs without QC verdict"; }; }

say "3. checks: loader and split sizes"
$PY - "$MAN" <<'PY' || { [ -n "$DRY" ] && echo "(dry run: carrying on)" || { rm -f "$MAN"; die "split check"; }; }
import json, sys
from pcm_data import DEFAULT_ROOTS, index
from pcm_splits import SPLITS, split_runs
runs = index(DEFAULT_ROOTS, manifest=sys.argv[1])
print(f"loader: {len(runs)} runs")
bad = []
for s in SPLITS:
    n = {k: len(v) for k, v in split_runs(runs, s).items()}
    print(f"  {s:15s} {n}")
    if min(n.values()) < 10: bad.append(s)
print("splits with a part under 10 runs:", bad or "none"); sys.exit(1 if bad else 0)
PY
[ -n "$DRY" ] && { say "DRY RUN done: nothing staged or started (manifest $MAN, md5 $(md5sum $MAN | cut -c1-12))"; exit 0; }

say "4. stage PCM data, code and manifest"
SRC="laptop:$HOME/of_runs/pcm_full/runs lab:$HOME/tb_data/lab/pcm_full pc3:$HOME/tb_data/pc3/pcm_full pc4:$HOME/tb_data/pc4/pcm_full pc5:$HOME/tb_data/pc5/pcm_full pc6:$HOME/tb_data/pc6/pcm_full"
for x in lab:labpc pc3:saxam@pc3 pc4:saxam@pc4 pc6:saxam@pc6; do m=${x%%:*}; h=${x#*:}
  for src in $SRC; do o=${src%%:*}; dir=${src#*:}
    [ $o = $m ] && continue                         # its own runs are in ~/of_runs/pcm_full/runs
    rsh $h "mkdir -p ~/tb_data/$o/pcm_full"
    (cd "$dir" && ls -d */DONE | cut -d/ -f1) | sed 's|$|/DONE|; p; s|DONE$|case.json|; p; s|case.json$|qc.json|; p; s|qc.json$|thermbench.h5|' \
      | ionice -c3 nice -n 10 rsync -a --ignore-missing-args --files-from=- "$dir/" $h:tb_data/$o/pcm_full/ || die "PCM data $o -> $m"
  done
  echo "  $m: staged"
done
bash "$ML/stage_ml.sh" code || die "code staging"
bash "$ML/pc5_data.sh" "$MAN" || die "pc5 data via GitHub"
for h in labpc:thermbench_ml saxam@pc3:thermbench_ml saxam@pc4:thermbench_ml saxam@pc6:thermbench_ml pc5:thermalbench/thermbench_ml; do scp -q "$MAN" $h/ || die "manifest to ${h%%:*}"; done
echo "manifest md5 $(md5sum "$MAN" | cut -c1-12) on all machines"

say "5. start PCM training on the seven GPU workers"
cd "$ML" && setsid nohup bash run_final_pcm.sh laptop > ~/run_final_pcm_laptop.out 2>&1 < /dev/null &
for w in labpc:lab saxam@pc3:pc3 saxam@pc4:pc4 saxam@pc6:pc6 pc5:pc5a pc5:pc5b; do
  D=thermbench_ml; [ ${w%%:*} = pc5 ] && D=thermalbench/thermbench_ml
  timeout 30 ssh -o BatchMode=yes ${w%%:*} "cd ~/$D && setsid nohup bash run_final_pcm.sh ${w##*:} > ~/run_final_pcm_${w##*:}.out 2>&1 < /dev/null &" < /dev/null; echo "started ${w##*:}"
done
sleep 120
for w in labpc:thermbench_ml/results_pcm saxam@pc3:thermbench_ml/results_pcm saxam@pc4:thermbench_ml/results_pcm saxam@pc6:thermbench_ml/results_pcm pc5:thermalbench/thermbench_ml/results_pcm_pc5a pc5:thermalbench/thermbench_ml/results_pcm_pc5b; do
  echo "$w: $(rsh ${w%%:*} "tail -2 ~/${w##*:}/run_final_pcm.log")"; done
echo "laptop: $(tail -2 "$ML/results_pcm/run_final_pcm.log")"
say "PCM freeze done, training running"
