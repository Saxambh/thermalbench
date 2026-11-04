#!/bin/bash
# Restart P14 from t=1625 (before the outlet blow-up) with two outlet treatments, GAMG in both:
#  ctrl: current BCs (uniform fixed p_rgh, backflow T = 70 C)
#  fix : p_rgh fixedMean (profile follows interior stratification), T zeroGradient
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SRC=~/of_runs/pilot_h5mm/P14_lam
B=~/of_runs/p14_bctest; rm -rf $B; mkdir -p $B
for v in ctrl fix; do
  mkdir -p $B/$v; cp -r $SRC/constant $SRC/system $SRC/1625 $B/$v/
  python3 - $B/$v $v <<'PY'
import sys, re
c, v = sys.argv[1:]
fs = f"{c}/system/fvSolution"; s = open(fs).read()
s = re.sub(r"p_rgh\n    \{.*?\n    \}", "p_rgh\n    {\n        solver          GAMG;\n        smoother        GaussSeidel;\n        tolerance       1e-8;\n        relTol          0.01;\n    }", s, count=1, flags=re.S)
open(fs, "w").write(s)
cd = f"{c}/system/controlDict"; s = open(cd).read()
s = re.sub(r"startFrom\s+[^;]+;", "startFrom       latestTime;", s)
s = re.sub(r"endTime\s+[^;]+;", "endTime         2150;", s)
s = re.sub(r"writeInterval\s+[^;]+;", "writeInterval   25;", s)
open(cd, "w").write(s)
if v == "fix":
    for f, new in (("p_rgh", "type            fixedMean;\n        meanValue       100000.0;\n        value           uniform 100000.0;"),
                   ("T", "type            zeroGradient;")):
        p = f"{c}/1625/{f}"; s = open(p).read()
        s2 = re.sub(r"(outlet\s*\{)[^}]*\}", lambda m: m.group(1) + "\n        " + new + "\n    }", s, count=1)
        assert s2 != s; open(p, "w").write(s2)
PY
  (cd $B/$v && S=$SECONDS && buoyantPimpleFoam > log.solver 2>&1; echo "$v exit=$? wall=$((SECONDS-S))s" > $B/$v.done) &
done
wait
cat $B/*.done
python3 - $B <<'PY'
import sys, re, os, numpy as np
b = sys.argv[1]
for v in ("ctrl", "fix"):
    L = open(f"{b}/{v}/log.solver").read()
    t = re.findall(r"\nTime = ([\d.e+-]+)", L)
    co = [float(x) for x in re.findall(r"Courant Number mean: \S+ max: (\S+)", L)]
    print(f"{v}: reached t={t[-1] if t else '?'}, max Co last 1000 steps {max(co[-1000:]):.2f}, FATAL={'FOAM FATAL' in L}")
    for d in sorted([d for d in os.listdir(f'{b}/{v}') if re.fullmatch(r'[\d.]+', d) and d != '1625'], key=float):
        s = open(f"{b}/{v}/{d}/U").read()
        m = re.search(r"List<vector>\s*\d+\s*\((.*?)\n\)\s*;", s, re.S)
        U = np.array(re.findall(r"\(([^ ]+) ([^ ]+) [^)]+\)", m.group(1)), float)
        print(f"   t={d:>5} |U|max {np.hypot(U[:,0],U[:,1]).max():.3f} m/s")
PY
