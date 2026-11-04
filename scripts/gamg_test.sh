#!/bin/bash
# PCG vs GAMG for p_rgh: same answer? how much faster? Real properties, 3.33 mm mesh,
# a slow-inflow wide tank like the slow fine cases (T0009-type), 60 s of simulated time.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
B=~/of_runs/gamg_test; rm -rf $B; mkdir -p $B
ARGS="--props real --h 0.0033333333333 --uin 0.0056 --tin 60 --t0 20 --W 0.92 --s 0.05 --end 60 --write 30"
for v in pcg gamg; do
  python3 $SRC/make_tank_case.py $B/$v $ARGS > /dev/null
  if [ $v = gamg ]; then
    python3 - $B/$v/system/fvSolution <<'EOF'
import sys, re
p = sys.argv[1]; s = open(p).read()
s = re.sub(r"p_rgh\n    \{.*?\n    \}", """p_rgh
    {
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       1e-8;
        relTol          0.01;
    }""", s, count=1, flags=re.S)
open(p, "w").write(s)
EOF
  fi
  (cd $B/$v && blockMesh > log.blockMesh 2>&1 && S=$SECONDS && buoyantPimpleFoam > log.solver 2>&1; echo "$v wall=$((SECONDS-S))s" > $B/$v.done) &
done
wait
cat $B/pcg.done $B/gamg.done
python3 - $B <<'EOF'
import sys, re, numpy as np
b = sys.argv[1]
def f(v, t, name="T"):
    s = open(f"{b}/{v}/{t}/{name}").read()
    return np.array(re.search(r"List<scalar>\s*\d+\s*\((.*?)\n\)", s, re.S).group(1).split(), float)
for t in ("30", "60"):
    a, g = f("pcg", t), f("gamg", t)
    print(f"t={t} s: T max|diff| {np.abs(a-g).max():.2e} K, RMS {np.sqrt(np.mean((a-g)**2)):.2e} K, "
          f"mean T pcg {a.mean():.5f} gamg {g.mean():.5f}")
for v in ("pcg", "gamg"):
    txt = open(f"{b}/{v}/log.solver").read()
    it = [int(x) for x in re.findall(r"Solving for p_rgh.*No Iterations (\d+)", txt)]
    print(f"{v}: steps {txt.count(chr(10)+'Time = ')}, mean p_rgh iterations {np.mean(it):.0f}")
EOF
