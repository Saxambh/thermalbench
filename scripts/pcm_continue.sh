#!/bin/bash
# Continue a PCM case that was moved mid-run from another machine (2026-11-05, Saxam: move the four
# slowest pc3 cases P0310 P0416 P0330 P0240 to the lab). The case folder arrives with all its time
# directories, postProcessing and log.solver; this script carries on from the latest complete time
# on <np> cores, then finishes exactly as pcm_batch.sh's one() does (export, slim, DONE, batch.log).
#   pcm_continue.sh <case_dir> <np>        (on the machine that continues it; log <case>/log.continue)
# Details:
#  - an incomplete newest time directory (solver paused mid-write) is removed before the restart
#  - restarting makes function objects open new postProcessing/<fo>/<t_restart>/ folders, while
#    export_pcm_case.py reads one .dat per function object: the series are merged back into the
#    first folder (rows before t_restart kept from the original, the rest from the continuation)
#  - the solver log is appended to log.solver, so the case keeps one log
unset LD_LIBRARY_PATH
C=$(readlink -f "$1"); NP=${2:-2}
SCR=$(dirname "$(readlink -f "$0")")
set --
source /usr/lib/openfoam/openfoam2606/etc/bashrc
cd "$(dirname "$C")" || exit 1
LOG=$PWD/batch.log; c=$(basename "$C")
exec >> "$C/log.continue" 2>&1
echo "$(date -u '+%F %H:%M') continue $c on $(hostname), $NP cores"
t0=$(date +%s)
cd "$C" || exit 1
complete() {   # every field file of a time directory ends with the OpenFOAM footer
  local f; for f in T U p_rgh "melting:alpha1" phi; do
    [ -s "$1/$f" ] && tail -c 200 "$1/$f" | grep -q '^// \*\*\*' || return 1; done
}
times() { ls | grep -E '^[0-9][0-9.e+-]*$' | sort -g; }
last=$(times | tail -1)
complete "$last" || { echo "newest time $last incomplete, removed"; rm -rf "$last"; last=$(times | tail -1); }
complete "$last" || { echo "$c CONTINUE_FAIL no complete time" >> $LOG; exit 1; }
echo "restart from t = $last"
rm -rf dynamicCode processor* log.solver.cont
# discard anything a failed earlier continuation wrote after the restart time
for d in $(times); do awk "BEGIN{exit !($d > $last)}" && { echo "removed later time $d"; rm -rf "$d"; }; done
python3 - "$last" <<'PY'
import os, re, shutil, sys
tl = float(sys.argv[1]); num = re.compile(r"^[0-9][0-9.e+-]*$")
for fo in os.listdir("postProcessing"):
    subs = sorted((s for s in os.listdir(f"postProcessing/{fo}") if num.match(s)), key=float)
    for s in subs[1:]:
        if float(s) >= tl - 1e-9:
            shutil.rmtree(f"postProcessing/{fo}/{s}"); print("removed postProcessing", fo, s)
PY
# Restart fix (found 2026-11-05 on P0310): the coded melt-range source creates melting:alpha1 on
# the first step with READ_IF_PRESENT at time().timeName(), which is then already the NEW time, so
# a restart starts from alpha = 0 (all melt lost, latent heat absorbed twice). Read it from the
# restart time instead. Fresh runs are unaffected (there is no alpha file to read at t = 0).
grep -rl 'IOobject("melting:alpha1", mesh_.time().timeName(), mesh_,' constant system 2>/dev/null \
  | xargs -r sed -i 's/IOobject("melting:alpha1", mesh_.time().timeName(), mesh_,/IOobject("melting:alpha1", mesh_.time().timeName(mesh_.time().startTime().value()), mesh_,/'
grep -rq 'timeName(mesh_.time().startTime().value())' constant system \
  || grep -rq 'solidificationMeltingSource' constant system \
  || { echo "$c CONTINUE_FAIL alpha restart patch not applied" >> $LOG; exit 1; }
foamDictionary system/controlDict -entry startFrom -set latestTime > /dev/null
cat > system/decomposeParDict <<EOF
FoamFile { format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains $NP;
method scotch;
EOF
ok=1
if [ "$NP" -gt 1 ]; then
  decomposePar -latestTime > log.decomposePar.cont 2>&1 \
    && nice -n 5 mpirun -np $NP buoyantPimpleFoam -parallel > log.solver.cont 2>&1 \
    && reconstructPar -newTimes > log.reconstructPar.cont 2>&1 || ok=0
else
  nice -n 5 buoyantPimpleFoam > log.solver.cont 2>&1 || ok=0
fi
if [ $ok = 0 ]; then echo "$c SOLVER_FAIL (continued) $(grep -m1 -A3 FATAL log.solver.cont | tr '\n' ' ' | cut -c1-200)" >> $LOG; exit 1; fi
rm -rf processor*
[ -f log.solver.gz ] && gunzip -f log.solver.gz
{ echo; echo "// ===== continued on $(hostname) from t = $last, $NP cores ====="; cat log.solver.cont; } >> log.solver && rm log.solver.cont
python3 - <<'PY'
import os, re
num = re.compile(r"^[0-9][0-9.e+-]*$")
for fo in sorted(os.listdir("postProcessing")):
    d = os.path.join("postProcessing", fo)
    subs = sorted((s for s in os.listdir(d) if num.match(s)), key=float)
    for s in subs[1:]:
        ts = float(s)
        for f in os.listdir(os.path.join(d, s)):
            base, new = os.path.join(d, subs[0], f), os.path.join(d, s, f)
            old = open(base).read().splitlines() if os.path.exists(base) else []
            keep = [l for l in old if l.startswith("#") or not l.strip() or float(l.split()[0]) < ts - 1e-9]
            add = [l for l in open(new).read().splitlines() if l.strip() and not l.startswith("#")]
            open(base, "w").write("\n".join(keep + add) + "\n")
            print(f"merged {fo}/{s}/{f}: {len(old)} + {len(add)} -> {len(keep) + len(add)} lines")
        os.system(f"rm -rf '{os.path.join(d, s)}'")
PY
cd ..
wall=$(( $(date +%s) - t0 ))
f=$(ls $c/postProcessing/liquidFraction/*/volFieldValue.dat | head -1)
lf=$(awk '!/^#/{x=$2; t=$1} END{printf "%.4f at %.0f s", x, t}' $f)
# exit 2 = solved but not exported (pcm_batch.sh then keeps the case instead of starting over)
python3 $SCR/export_pcm_case.py $c > $c/export.log 2>&1 || { echo "$c EXPORT_FAIL" >> $LOG; exit 2; }
find $c -mindepth 1 -maxdepth 1 -type d -regex '.*/[0-9][0-9.e+-]*' ! -name 0 -exec rm -rf {} +
gzip -f $c/log.solver
rm -rf $c/dynamicCode
touch $c/DONE
echo "$c ok (continued here from t = $last on $NP cores) wall ${wall} s, liquid fraction $lf | $(tail -1 $c/export.log)" >> $LOG
echo "$(date -u '+%F %H:%M') done"
