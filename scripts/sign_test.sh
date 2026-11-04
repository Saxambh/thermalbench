#!/bin/bash
# Decisive sign test for buoyancy terms in the k equation.
# Closed tank, stable stratification, uniform initial turbulence, no inflow.
# Physics: buoyancy must make k decay FASTER than without buoyancy.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
B=~/of_runs/sign_test; mkdir -p $B
run() {  # name, args
  local n=$1; shift
  rm -rf $B/$n
  python3 $SRC/make_tank_case.py $B/$n --h 0.01 --uin 0 --end 20 --write 5 --turb kOmegaSST "$@" > /dev/null
  python3 $SRC/sign_test.py $B/$n
  cd $B/$n
  blockMesh > log.blockMesh 2>&1
  setExprFields > log.setExprFields 2>&1 || { echo "$n setExprFields FAILED"; tail -5 log.setExprFields; return; }
  local app=$(foamDictionary -entry application -value system/controlDict)
  $app > log.solver 2>&1 || { echo "$n solver FAILED"; grep -m1 -A6 "FOAM FATAL" log.solver; return; }
  python3 - "$B/$n" <<'EOF'
import sys, re, os
c = sys.argv[1]
def mean(field, t):
    s = open(f"{c}/{t}/{field}").read()
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;", s, re.S)
    if m:
        v = [float(x) for x in m.group(2).split()]
        return sum(v) / len(v)
    return float(re.search(r"internalField\s+uniform\s+([0-9.eE+-]+)", s).group(1))
name = os.path.basename(c)
k = [mean("k", t) for t in ("5", "10", "20")]
T0 = mean("T", "0"); T20 = mean("T", "20")
print(f"{name:22s} mean k at 5/10/20 s: {k[0]:.3e} {k[1]:.3e} {k[2]:.3e}   mean T 0->20 s: {T0:.4f} -> {T20:.4f}")
EOF
}
run none_bous
run bts_bous --buoy
run fix_bous --buoyk
run none_real --props real
run bts_real --props real --buoy
