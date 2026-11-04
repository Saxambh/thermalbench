#!/bin/bash
# Is the start-up temperature overshoot (P10: +3.6 K at t=8 s) caused by the dp/dt term in the energy equation?
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
B=~/of_runs/nouter_test; rm -rf $B; mkdir -p $B
ARGS=$(python3 - <<'PY'
import csv, shlex, sys
sys.path.insert(0, "/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench")
import make_design
r = [r for r in csv.DictReader(open("/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/design_v2_pilot.csv")) if r["run_id"] == "P10_lam"][0]
a = make_design.args_for(r)
# drop the tstar/nsnap end control; run 20 s, write every 1 s
out, skip = [], 0
for i, x in enumerate(a):
    if skip: skip -= 1; continue
    if x in ("--tstar", "--nsnap", "--end", "--write"): skip = 1; continue
    out.append(x)
print(" ".join(shlex.quote(x) for x in out + ["--end", "20", "--write", "1"]))
PY
)
for v in n1 n2 n3; do
  eval python3 $S/make_tank_case.py $B/$v $ARGS > /dev/null
  [ $v != n1 ] && sed -i "s/nOuterCorrectors 1;/nOuterCorrectors ${v#n};/" $B/$v/system/fvSolution
  (cd $B/$v && blockMesh > log.blockMesh 2>&1 && buoyantPimpleFoam > log.solver 2>&1) &
done
wait
grep -h nOuter $B/*/system/fvSolution
python3 - $B <<'PY'
import sys, os, re, numpy as np
b = sys.argv[1]
for v in ("n1", "n2", "n3"):
    L = open(f"{b}/{v}/log.solver").read()
    print(v, "FATAL" if "FOAM FATAL" in L else "ok", end=": ")
    out = []
    for d in sorted([d for d in os.listdir(f"{b}/{v}") if re.fullmatch(r"[\d.]+", d) and d != "0"], key=float):
        s = open(f"{b}/{v}/{d}/T").read()
        T = np.array(re.search(r"List<scalar>\s*\d+\s*\((.*?)\n\)", s, re.S).group(1).split(), float)
        out.append(f"{d}s:{T.max()-273.15:.2f}/{T.min()-273.15:.2f}")
    print(" ".join(out))
PY
