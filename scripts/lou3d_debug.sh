#!/bin/bash
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
C=~/of_runs/lou3d/test; cd $C
rm -rf processor* 0.* [1-9]* postProcessing log.solver
foamDictionary system/controlDict -entry writeControl -set timeStep > /dev/null
foamDictionary system/controlDict -entry writeInterval -set 1 > /dev/null
foamDictionary system/controlDict -entry endTime -set 0.0006 > /dev/null
foamDictionary system/controlDict -entry writeFormat -set ascii > /dev/null
nice -n 5 buoyantPimpleFoam > log.debug 2>&1; echo "exit $?"
grep -m3 -A4 "FOAM FATAL\|Floating" log.debug
python3 - <<'PY'
import os, re, numpy as np
c = os.path.expanduser("~/of_runs/lou3d/test")
# cell centres
os.system(f"cd {c} && postProcess -func writeCellCentres -time 0 > /dev/null 2>&1")
def vec(p):
    s = open(p).read(); m = re.search(r"internalField\s+nonuniform\s+List<vector>\s*\d+\s*\((.*?)\n\)\s*;", s, re.S)
    return np.array(re.findall(r"\(([^ ]+) ([^ ]+) ([^)]+)\)", m.group(1)), float)
def sca(p):
    s = open(p).read(); m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*\d+\s*\((.*?)\n\)\s*;", s, re.S)
    return np.array(m.group(1).split(), float) if m else None
C = vec(f"{c}/0/C")
ts = sorted([d for d in os.listdir(c) if re.fullmatch(r"[0-9.e-]+", d) and d != "0"], key=float)
for t in ts:
    U = vec(f"{c}/{t}/U"); m = np.linalg.norm(U, axis=1); i = m.argmax()
    T = sca(f"{c}/{t}/T")
    print(f"t={t}: |U|max {m.max():.3f} at {C[i]*1000} mm, U={U[i]}, T range {T.min():.2f}..{T.max():.2f}" if T is not None else f"t={t} |U|max {m.max():.3f} at {C[i]*1000}")
PY
