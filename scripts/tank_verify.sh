#!/bin/bash
# Stage 1A tank numerical verification (2026-11-06, Saxam: "start 1a"). Plan and pass/fail rule fixed before
# any result: results_note_2026-11-06_stage0_verification.md and the 2026-11-06 assessment of the reviewer's
# recommendations. One run of one dataset design with one change; the frozen dataset is not touched.
#   p2    production settings again (current generator; checks reproducibility, baseline for the others)
#   n4    PIMPLE nOuterCorrectors 4 instead of 2
#   co25  maxCo 0.25 instead of 0.5
#   rep   production settings with the inlet velocity x (1 + 1e-4): noise floor of the unsteady flow
#   h25   production settings on a 2.5 mm mesh (h / 2; 2026-11-06 mesh check, Saxam: "lets do mesh check first")
#   h10   production settings on a 10 mm mesh (2 h; only designs whose geometry sits on a 10 mm grid)
# Serial, as the dataset runs. Raw time directories are deleted after a verified export (as run_batch.py).
#   tank_verify.sh <run_id> <variant> <design.csv> <out_dir>     log line: <out_dir>/batch.log
# design.csv MUST be design_v2_full.csv, the list the dataset was built from (geometry on a 10 mm grid).
# design_h5mm_full.csv differs in 613 port offsets and 184 widths (found 2026-11-06 on T0243).
# TV_NP=<n> runs the solver in parallel on n cores.
unset LD_LIBRARY_PATH
RID=$1; V=$2; CSV=$(readlink -f "$3"); OUT=$(readlink -f "$4")
SCR=$(dirname "$(readlink -f "$0")")
set --
source /usr/lib/openfoam/openfoam2606/etc/bashrc
mkdir -p "$OUT"; cd "$OUT" || exit 1
LOG=$OUT/batch.log; C=${RID}_$V
[ -f $C/DONE ] && { echo "$C done already"; exit 0; }
rm -rf $C
ARGS=$(python3 - "$CSV" "$RID" "$V" <<'P'
import csv, sys, shlex
csvf, rid, v = sys.argv[1:]
r = next(x for x in csv.DictReader(open(csvf)) if x["run_id"] == rid)
u = float(r["u_in"]) * (1 + 1e-4 if v == "rep" else 1)
r["h"] = {"h25": "0.0025", "h10": "0.01"}.get(v, r["h"])
a = ["--props", "real", "--h", r["h"], "--uin", repr(u), "--tin", r["T_in"], "--t0", r["T_0"], "--W", r["W"],
     "--H", r["H"], "--s", r["s"], "--off", r["off"], "--inlet-type", r["inlet_type"], "--mode", r["mode"],
     "--tstar", r["tstar"], "--nsnap", "120"]          # as make_design.args_for
if r["yi"] != "": a += ["--yi", r["yi"]]
if r["turb"] != "laminar": a += ["--turb", "kOmegaSST", "--buoy"]
print(" ".join(shlex.quote(x) for x in a))
P
) || { echo "$C NO_DESIGN_ROW" >> $LOG; exit 1; }
t0=$(date +%s)
eval python3 $SCR/make_tank_case.py $C $ARGS > $C.gen.log 2>&1 || { echo "$C GEN_FAIL" >> $LOG; exit 1; }
cd $C
case $V in
  n4)   foamDictionary system/fvSolution -entry PIMPLE/nOuterCorrectors -set 4 > /dev/null ;;
  co25) foamDictionary system/controlDict -entry maxCo -set 0.25 > /dev/null ;;
  p2|rep|h25|h10) ;;
  *) echo "unknown variant $V"; exit 1 ;;
esac
# check what the run will use (foamDictionary -expand prints the whole file in v2606, read it with awk)
get() { foamDictionary -expand system/$1 2>/dev/null | awk -v k="$2" '$1==k{sub(/;$/,"",$2); print $2; exit}'; }
nO=$(get fvSolution nOuterCorrectors); co=$(get controlDict maxCo)
want_n=2; want_c=0.5; [ $V = n4 ] && want_n=4; [ $V = co25 ] && want_c=0.25
[ "$nO" = $want_n ] && [ "$co" = $want_c ] || { cd ..; echo "$C SETUP_FAIL nOuter=$nO maxCo=$co" >> $LOG; exit 1; }
echo "$(date -u '+%F %H:%M') $C on $(hostname): nOuterCorrectors $nO, maxCo $co; generator args: $ARGS" > VERIFY_NOTE.txt
ok=1
if [ "${TV_NP:-1}" -gt 1 ]; then   # optional parallel run (2026-11-06 speed-up; round-off only)
  printf 'FoamFile { format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains %s;
method scotch;
' $TV_NP > system/decomposeParDict
  blockMesh > log.blockMesh 2>&1 && decomposePar > log.decomposePar 2>&1     && nice -n 5 mpirun -np $TV_NP buoyantPimpleFoam -parallel > log.solver 2>&1 && reconstructPar > log.reconstructPar 2>&1 || ok=0
  rm -rf processor*
else
  blockMesh > log.blockMesh 2>&1 && nice -n 5 buoyantPimpleFoam > log.solver 2>&1 || ok=0
fi
[ $ok = 1 ] && python3 $SCR/export_case.py "$OUT/$C" > log.export 2>&1 || ok=0
cd ..
[ $ok = 0 ] && { echo "$C FAIL $(grep -m1 -A2 FATAL $C/log.solver | tr '\n' ' ' | cut -c1-150)" >> $LOG; exit 1; }
chk=$(python3 - $C <<'P'
import json, sys
m = json.load(open(f"{sys.argv[1]}/metrics.json")); s = m["snapshots"]; e = m["case"]["end_time_s"]
print("ok" if len(s) >= 2 and abs(s[-1]["t_s"] - e) < 1e-3 * e else f"incomplete {len(s)} snaps, last {s[-1]['t_s']} of {e}")
P
)
[ "$chk" = ok ] || { echo "$C EXPORT_INCOMPLETE $chk" >> $LOG; exit 2; }
find $C -mindepth 1 -maxdepth 1 -type d -regex '.*/[0-9][0-9.e+-]*' ! -name 0 -exec rm -rf {} +
gzip -f $C/log.solver
touch $C/DONE
echo "$C ok wall $(( $(date +%s) - t0 )) s (nOuter $nO, maxCo $co)" >> $LOG
