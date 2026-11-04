#!/bin/bash
# Tests for make_tank_case.py v2 (all variants, short runs).
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
B=~/of_runs/gen_tests; rm -rf $B; mkdir -p $B
one() {  # name, args
  local n=$1; shift
  python3 $SRC/make_tank_case.py $B/$n "$@" || { echo "$n GENERATOR FAILED"; return; }
  cd $B/$n
  blockMesh > log.blockMesh 2>&1 || { echo "$n blockMesh FAILED"; tail -8 log.blockMesh; return; }
  checkMesh > log.checkMesh 2>&1; grep -q "Mesh OK" log.checkMesh || { echo "$n checkMesh NOT OK"; grep -i "fail\|\*\*\*" log.checkMesh | head; }
  local app=$(foamDictionary -entry application -value system/controlDict)
  $app > log.solver 2>&1 || { echo "$n solver FAILED"; grep -m1 -A8 "FOAM FATAL" log.solver; return; }
  local last=$(foamListTimes -latestTime 2>/dev/null | tail -1)
  echo "  $n OK  steps=$(grep -c '^Time =' log.solver) last=$last  meanT=$(tail -1 postProcessing/meanT/0/volFieldValue.dat | awk '{print $2}')  outletT=$(tail -1 postProcessing/outletT/0/surfaceFieldValue.dat | awk '{print $2}')"
}
echo "== 1 regression (default case, Boussinesq, 5 s)"
one regress --uin 0.02 --end 5 --write 5
echo "  md5 $(md5sum $B/regress/5/T | cut -c1-32)  expected 7d3b88af04eff35753ea8737fa6ac3ba"
echo "== 2 type A discharge, real, laminar (cold 20 C into hot 60 C at the bottom)"
one A_dis --props real --mode discharge --tin 20 --t0 60 --uin 0.02 --end 20 --write 10
echo "== 3 type B charge, real, SST + buoyancy, narrow tank"
one B_chg --props real --inlet-type B --W 0.3 --s 0.02 --uin 0.1 --turb kOmegaSST --buoy --end 5 --write 5
echo "== 4 pre-stratified start (interface at 0.6 H), type A charge, real, t* end"
one A_pre --props real --yi 0.6 --uin 0.05 --tstar 0.02 --nsnap 2
echo "== 5 type B discharge, real, laminar"
one B_dis --props real --inlet-type B --mode discharge --tin 20 --t0 60 --uin 0.02 --end 10 --write 10
echo "== 6 cell ordering: generator centres vs OpenFOAM centres (case 3, multi-block)"
cd $B/B_chg && postProcess -func writeCellCentres -time 0 > log.cc 2>&1
python3 - $B/B_chg $SRC <<'EOF'
import sys, re, json
sys.path.insert(0, sys.argv[2])
import make_tank_case as m
c = sys.argv[1]; j = json.load(open(f"{c}/case.json"))
s = open(f"{c}/0/C").read()
body = re.search(r"internalField\s+nonuniform\s+List<vector>\s+\d+\s*\((.*?)\)\s*;", s, re.S).group(1)
of = [tuple(map(float, t.split()[:2])) for t in re.findall(r"\(([^()]*)\)", body)]
gen = m.cell_centres(j["mesh_h_m"], j["x_breaks"], j["y_breaks"])
err = max(abs(a[0]-b[0]) + abs(a[1]-b[1]) for a, b in zip(of, gen))
print(f"  cells: OpenFOAM {len(of)}, generator {len(gen)}, max centre mismatch {err:.2e} m")
EOF
echo "== 7 initial profile of case 4 (T at a few heights on the centreline)"
python3 - $B/A_pre <<'EOF'
import re, sys
c = sys.argv[1]
s = open(f"{c}/0/T").read()
v = [float(x) for x in re.search(r"List<scalar>\s*\d+\s*\((.*?)\)", s, re.S).group(1).split()]
nx = 100  # W 0.5 / h 0.005, single column of blocks
for y in (0.1, 0.5, 0.58, 0.6, 0.62, 0.7, 0.95):
    row = int(y / 0.005); print(f"  y={y:.2f} m  T={v[row*nx + nx//2] - 273.15:.2f} C")
EOF
cat $B/B_chg/case.json | head -40
