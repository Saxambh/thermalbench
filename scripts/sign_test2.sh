#!/bin/bash
# Mirrored, quantitative sign test of buoyancyTurbSource (k equation).
# Closed tank at rest, linear T (stable: hot on top; unstable: hot at bottom), k = 1e-4, omega = 1.
# Measures the initial rate dk/dt (domain mean, first 0.25 s) with and without the source and
# compares the difference with the analytic buoyancy production Gb at t = 0.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
B=~/of_runs/sign_test2; rm -rf $B; mkdir -p $B
run() { local n=$1 prof=$2; shift 2
  python3 $S/make_tank_case.py $B/$n --h 0.01 --uin 0 --end 0.5 --write 0.25 --turb kOmegaSST "$@" > /dev/null
  python3 $S/sign_test2.py $B/$n $prof
  (cd $B/$n && blockMesh > log.blockMesh 2>&1 && setExprFields > log.setExprFields 2>&1 \
     && $(foamDictionary -entry application -value system/controlDict) > log.solver 2>&1 || echo "$n FAILED") &
}
for prof in stable unstable; do
  run bous_none_$prof $prof
  run bous_bts_$prof $prof --buoy
  run real_none_$prof $prof --props real
  run real_bts_$prof $prof --props real --buoy
done
wait
python3 - $B <<'PY'
import sys, re, numpy as np
sys.path.insert(0, "/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench")
import make_tank_case as gen
b = sys.argv[1]
def mean(c, f, t):
    s = open(f"{b}/{c}/{t}/{f}").read()
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s+\d+\s*\((.*?)\)\s*;", s, re.S)
    return np.mean(np.array(m.group(1).split(), float)) if m else float(re.search(r"internalField\s+uniform\s+(\S+);", s).group(1))
rate = lambda c: (mean(c, "k", "0.25") - 1e-4) / 0.25
nut, Prt, g = 1e-4 / 1.0, 0.85, -9.81          # nut = k/omega at t = 0
y = (np.arange(100) + 0.5) * 0.01
print(f"{'case':10} {'profile':9} {'measured d(dk/dt)':>18} {'correct Gb':>12}  verdict")
for prof, sgn in (("stable", 1), ("unstable", -1)):
    T = (293.15 + 40 * y) if sgn > 0 else (333.15 - 40 * y)
    Gb_bous = 3.5e-4 * nut / Prt * (sgn * 40) * g                     # beta*alphat*(gradT . g)
    rho = gen.poly(gen.RHO_C, T)
    Gb_real = np.mean(-(nut / Prt) * np.gradient(rho, y) * g / rho)  # -(nut/Prt)(grad rho . g)/rho
    for kind, Gb in (("bous", Gb_bous), ("real", Gb_real)):
        d = rate(f"{kind}_bts_{prof}") - rate(f"{kind}_none_{prof}")
        verdict = "matches +Gb" if np.sign(d) == np.sign(Gb) and 0.5 < d / Gb < 2 else \
                  "OPPOSITE SIGN" if np.sign(d) != np.sign(Gb) else "same sign, magnitude off"
        print(f"{kind:10} {prof:9} {d:18.3e} {Gb:12.3e}  {verdict} (ratio {d / Gb:+.2f})")
PY
