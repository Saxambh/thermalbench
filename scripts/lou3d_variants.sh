#!/bin/bash
# Which ingredient makes the 3D start-up blow up at the outlet? 6 steps per variant, serial.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
B=~/of_runs/lou3d/var; rm -rf $B; mkdir -p $B
T0=~/of_runs/lou3d/test
mk() { local n=$1; mkdir -p $B/$n; cp -r $T0/0 $T0/constant $T0/system $B/$n/; rm -rf $B/$n/processor*
  foamDictionary $B/$n/system/controlDict -entry endTime -set 0.0008 > /dev/null
  foamDictionary $B/$n/system/controlDict -entry writeInterval -set 100 > /dev/null; }
mk base
mk laminar; echo "simulationType laminar;" > $B/laminar/constant/turbulenceProperties.tmp
python3 - $B/laminar <<'PY'
import sys, re
c = sys.argv[1]; p = f"{c}/constant/turbulenceProperties"
s = open(p).read(); s = s[:s.index("simulationType")] + "simulationType  laminar;\n"; open(p, "w").write(s)
import os; os.remove(f"{c}/constant/fvOptions")
PY
mk nodpdt; sed -i 's/^thermoType/dpdt            no;\n\nthermoType/' $B/nodpdt/constant/thermophysicalProperties
mk euler; sed -i 's/default         backward;/default         Euler;/' $B/euler/system/fvSchemes
mk lowco; foamDictionary $B/lowco/system/controlDict -entry maxCo -set 0.3 > /dev/null; foamDictionary $B/lowco/system/controlDict -entry deltaT -set 1e-5 > /dev/null
for n in base laminar nodpdt euler lowco; do (cd $B/$n && nice -n 5 buoyantPimpleFoam > log 2>&1) & done; wait
for n in base laminar nodpdt euler lowco; do
  echo "$n: steps $(grep -c '^Time = ' $B/$n/log)  last $(grep '^Time = ' $B/$n/log | tail -1)  Co $(grep 'Courant' $B/$n/log | tail -1 | awk '{print $NF}')  $(grep -q 'FOAM FATAL' $B/$n/log && echo FATAL)"
done
