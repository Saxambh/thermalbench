#!/bin/bash
# Thursday's tank freeze in one command, run in WSL on the laptop (the hub). Stops at the first problem.
#   bash freeze_all.sh --dry    rehearsal: steps 0-4 with a scratch manifest; copies data, starts nothing
#   bash freeze_all.sh          the real freeze: steps 0-6, then distributed training on the four GPUs
# 2026-11-04: pc5 (2 GPUs, workers pc5a/pc5b) added to steps 5 and 6.
# Steps: 0 all tank lists finished, no tank solver running   1 QC every finished run on its machine
#        2 gather lab + pc3 runs to the laptop                3 freeze_manifest.py (design exclusion rule)
#        4 checks: coverage, loader, duplicates, QC, splits   5 stage code + data + manifest to lab, pc3, pc4
#        6 start run_final.sh <worker> on laptop, pc3, lab, pc4, pc5 (x2) (check_data.py runs first on each)
# Written 2026-11-04 (Saxam). Log: ~/freeze_all.log. Merge afterwards: python merge_results.py results_workers/*
unset LD_LIBRARY_PATH
DRY=$([ "$1" = --dry ] && echo 1)
ML="$(dirname "$(readlink -f "$0")")"
R="$(dirname "$ML")"
PY=~/venvs/tbml-gpu/bin/python
MAN="$ML/manifest_full_h5mm.json"; [ -n "$DRY" ] && MAN=/tmp/manifest_freeze_dry.json
exec > >(tee -a ~/freeze_all.log) 2>&1
say() { echo "=== $* ($(date -u +%H:%M) UTC, $(TZ=Asia/Kathmandu date +%H:%M) Nepal)"; }
die() { echo "STOP: $*"; exit 1; }
rsh() { ssh -o BatchMode=yes -o ConnectTimeout=20 "$@" < /dev/null; }
say "freeze_all ${DRY:+DRY RUN }start"
[ -z "$DRY" ] && [ -f "$MAN" ] && die "$MAN already exists (frozen before?); move it away first"

say "0. tank lists finished, no tank solver running"
python3 "$ML/freeze_lists.py" > /tmp/fz_laptop.json || die "lists on laptop"
for h in labpc:lab saxam@pc3:pc3; do
  # not rsh: it redirects stdin from /dev/null, and the script must arrive on stdin
  ssh -o BatchMode=yes -o ConnectTimeout=20 ${h%%:*} python3 - < "$ML/freeze_lists.py" > /tmp/fz_${h##*:}.json || die "lists on ${h##*:} (unreachable?)"
  [ -s /tmp/fz_${h##*:}.json ] || die "empty run list from ${h##*:}"
done
left=$(python3 -c "import json; a=sum((json.load(open(f'/tmp/fz_{m}.json')) for m in ('laptop','lab','pc3')), []); print(sum(1 for r in a if not (r['done'] and r['h5'])))")
running=$(for h in "" labpc saxam@pc3; do c='for d in /proc/[0-9]*; do [[ "$(tr "\0" " " < $d/cmdline 2>/dev/null)" == buoyantPimpleFoam* ]] && [[ "$(readlink $d/cwd)" == */full_h5mm* ]] && echo x; done | wc -l'
  if [ -z "$h" ]; then bash -c "$c"; else rsh $h "$c"; fi; done | awk '{s+=$1} END{print s+0}')
echo "tank runs not finished: $left; tank solvers running: $running"
if [ "$left" != 0 ] || [ "$running" != 0 ]; then [ -n "$DRY" ] && echo "(dry run: carrying on)" || die "tank runs still going"; fi

say "1. QC on every machine (qc_runs.py writes qc.json once per run)"
QCL="$R/scripts/qc_runs.py"
for d in ~/of_runs/full_h5mm ~/of_runs/full_h5mm_x; do [ -d $d ] && nice python3 "$QCL" $d | grep -E "^QC|FAIL" | sed "s/^/laptop /"; done; true
for h in labpc saxam@pc3; do
  # '; true': a missing folder (pc3 has no full_h5mm_x) must not count as a failure
  rsh $h 'for d in ~/of_runs/full_h5mm ~/of_runs/full_h5mm_x; do [ -d $d ] && nice python3 ~/thermbench/scripts/qc_runs.py $d | grep -E "^QC|FAIL"; done; true' | sed "s/^/$h /"
  [ ${PIPESTATUS[0]} = 0 ] || die "QC on $h (unreachable?)"
done

say "2. gather lab + pc3 runs to the laptop"
nice -n 10 ionice -c3 bash "$ML/gather.sh" || die "gather"

say "3. manifest -> $MAN"
cd "$ML" && $PY freeze_manifest.py --out "$MAN" | tee /tmp/fz_manifest.txt || die "freeze_manifest"
grep -q "no QC verdict" /tmp/fz_manifest.txt && { [ -n "$DRY" ] && echo "(dry run: carrying on)" || { rm -f "$MAN"; die "runs without QC verdict"; }; }

say "4. checks"
cd "$ML" && $PY freeze_check.py "$MAN" /tmp/fz_laptop.json /tmp/fz_lab.json /tmp/fz_pc3.json || { [ -z "$DRY" ] && rm -f "$MAN"; die "checks failed"; }
python3 - "$MAN" <<'PY' || { [ -n "$DRY" ] && echo "(dry run: carrying on)" || { rm -f "$MAN"; die "split too small"; }; }
import json, sys
sys.path.insert(0, "."); from data import DEFAULT_ROOTS, index; from splits import SPLITS, split_runs
runs = index(DEFAULT_ROOTS, manifest=sys.argv[1])
small = [s for s in SPLITS if len(split_runs(runs, s)["test"]) < 50]
print("test sets under 50 runs:", small or "none"); sys.exit(1 if small else 0)
PY
[ -n "$DRY" ] && { say "DRY RUN done: nothing staged or started (manifest $MAN, md5 $(md5sum $MAN | cut -c1-12))"; exit 0; }

say "5. stage code + data to lab, pc3, pc4, pc5; copy the manifest"
bash "$ML/stage_ml.sh" code data || die "staging"
nice -n 10 $PY "$ML/make_slim.py" "$MAN" || die "slim copies for pc5"
rsync -a ~/tb_slim/ pc5:tb_data/ || die "slim copies to pc5"
# pc5 runs from its git clone (~/thermalbench/thermbench_ml), the others from ~/thermbench_ml
for h in labpc:thermbench_ml saxam@pc3:thermbench_ml saxam@pc4:thermbench_ml pc5:thermalbench/thermbench_ml; do scp -q "$MAN" $h/ || die "manifest to ${h%%:*}"; done
echo "manifest md5 $(md5sum "$MAN" | cut -c1-12) on all machines"

say "6. start training on the six GPUs (pc5 has two)"
cd "$ML" && setsid nohup bash run_final.sh laptop > ~/run_final_laptop.out 2>&1 < /dev/null &
for w in labpc:lab saxam@pc3:pc3 saxam@pc4:pc4 pc5:pc5a pc5:pc5b; do
  D=thermbench_ml; [ ${w%%:*} = pc5 ] && D=thermalbench/thermbench_ml
  # a backgrounded remote job can keep the ssh channel open: cap the call, then check the log below
  timeout 30 ssh -o BatchMode=yes ${w%%:*} "cd ~/$D && setsid nohup bash run_final.sh ${w##*:} > ~/run_final_${w##*:}.out 2>&1 < /dev/null &" < /dev/null; echo "started ${w##*:}"
done
sleep 120
for w in labpc:thermbench_ml/results saxam@pc3:thermbench_ml/results saxam@pc4:thermbench_ml/results pc5:thermalbench/thermbench_ml/results_pc5a pc5:thermalbench/thermbench_ml/results_pc5b; do echo "$w: $(rsh ${w%%:*} "tail -2 ~/${w##*:}/run_final.log")"; done
echo "laptop: $(tail -2 "$ML/results/run_final.log")"
say "freeze done, training running (results in each machine's thermbench_ml/results/)"
