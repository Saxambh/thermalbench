#!/bin/bash
# Continue a tank verification run (tank_verify.sh) from its latest complete time on <np> cores, on the
# machine it was moved to (2026-11-06, Saxam: "use the fastest pc for this runs, i need the result asap").
# The case folder arrives with all its time directories, postProcessing and log.solver. As pcm_continue.sh:
#  - an incomplete newest time directory is removed; later times from a failed continuation are discarded
#  - function objects open new postProcessing/<fo>/<t_restart>/ folders on restart; export_case.py reads
#    the 0/ folder only, so the rows are merged back into it (rows before t_restart kept)
#  - the solver log is appended to log.solver; the finish is that of tank_verify.sh (export, end-time
#    check, raw times deleted, DONE, batch.log line)
# Parallel decomposition changes round-off and the linear-solver partitioning only; its effect is measured
# separately (T0408_lam p2 serial vs 4 cores).
#   tank_continue.sh <case_dir> <np>      log: <case>/log.continue, line in <case>/../batch.log
unset LD_LIBRARY_PATH
C=$(readlink -f "$1"); NP=${2:-4}
SCR=$(dirname "$(readlink -f "$0")")
set --
source /usr/lib/openfoam/openfoam2606/etc/bashrc
cd "$(dirname "$C")" || exit 1
LOG=$PWD/batch.log; c=$(basename "$C")
exec >> "$C/log.continue" 2>&1
echo "$(date -u '+%F %H:%M') continue $c on $(hostname), $NP cores"
t0=$(date +%s)
cd "$C" || exit 1
complete() { local f; for f in T U p_rgh phi; do
  [ -s "$1/$f" ] && tail -c 200 "$1/$f" | grep -q '^// \*\*\*' || return 1; done; }
times() { ls | grep -E '^[0-9][0-9.e+-]*$' | sort -g; }
last=$(times | tail -1)
complete "$last" || { echo "newest time $last incomplete, removed"; rm -rf "$last"; last=$(times | tail -1); }
complete "$last" || { echo "$c CONTINUE_FAIL no complete time" >> $LOG; exit 1; }
[ "$last" = 0 ] && { echo "$c CONTINUE_FAIL nothing to continue from" >> $LOG; exit 1; }
echo "restart from t = $last"
rm -rf dynamicCode processor*
python3 - "$last" <<'PY'
import os, re, shutil, sys
tl = float(sys.argv[1]); num = re.compile(r"^[0-9][0-9.e+-]*$")
for fo in os.listdir("postProcessing"):
    subs = sorted((s for s in os.listdir(f"postProcessing/{fo}") if num.match(s)), key=float)
    if fo == "profile": continue      # sampled sets: one folder per write time, not a restart folder
    for s in subs[1:]:
        if float(s) >= tl - 1e-9:
            shutil.rmtree(f"postProcessing/{fo}/{s}"); print("removed postProcessing", fo, s)
PY
foamDictionary system/controlDict -entry startFrom -set latestTime > /dev/null
cat > system/decomposeParDict <<EOF
FoamFile { format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains $NP;
method scotch;
EOF
ok=1
decomposePar -latestTime > log.decomposePar.cont 2>&1 \
  && nice -n 5 mpirun -np $NP buoyantPimpleFoam -parallel > log.solver.cont 2>&1 \
  && reconstructPar -newTimes > log.reconstructPar.cont 2>&1 || ok=0
[ $ok = 0 ] && { echo "$c SOLVER_FAIL (continued) $(grep -m1 -A3 FATAL log.solver.cont | tr '\n' ' ' | cut -c1-200)" >> $LOG; exit 1; }
rm -rf processor*
{ echo; echo "// ===== continued on $(hostname) from t = $last, $NP cores ====="; cat log.solver.cont; } >> log.solver && rm log.solver.cont
python3 - <<'PY'
import os, re
num = re.compile(r"^[0-9][0-9.e+-]*$")
for fo in sorted(os.listdir("postProcessing")):
    d = os.path.join("postProcessing", fo)
    subs = sorted((s for s in os.listdir(d) if num.match(s)), key=float)
    if fo == "profile": continue      # sampled sets: one folder per write time, not a restart folder
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
python3 $SCR/export_case.py "$C" > $C/log.export 2>&1 || { echo "$c EXPORT_FAIL (continued)" >> $LOG; exit 2; }
chk=$(python3 - $c <<'P'
import json, sys
m = json.load(open(f"{sys.argv[1]}/metrics.json")); s = m["snapshots"]; e = m["case"]["end_time_s"]
print("ok" if len(s) >= 2 and abs(s[-1]["t_s"] - e) < 1e-3 * e else f"incomplete {len(s)} snaps, last {s[-1]['t_s']} of {e}")
P
)
[ "$chk" = ok ] || { echo "$c EXPORT_INCOMPLETE $chk" >> $LOG; exit 2; }
find $c -mindepth 1 -maxdepth 1 -type d -regex '.*/[0-9][0-9.e+-]*' ! -name 0 -exec rm -rf {} +
gzip -f $c/log.solver
rm -rf $c/dynamicCode
touch $c/DONE
echo "$c ok (continued on $(hostname) from t = $last on $NP cores) wall $(( $(date +%s) - t0 )) s" >> $LOG
echo "$(date -u '+%F %H:%M') done"
