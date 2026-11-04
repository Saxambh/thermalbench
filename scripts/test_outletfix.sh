#!/bin/bash
# Quick smoke test of the fixed outlet across the generator's variants (5 mm, 3 s simulated).
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
B=~/of_runs/outletfix_smoke; rm -rf $B; mkdir -p $B
run() { n=$1; shift
  python3 $S/make_tank_case.py $B/$n --end 3 --write 1.5 "$@" > $B/$n.gen 2>&1 || { echo "$n generator FAILED"; return; }
  (cd $B/$n && blockMesh > log.blockMesh 2>&1 && buoyantPimpleFoam > log.solver 2>&1)
  if grep -q "^End" $B/$n/log.solver; then
    echo "$n ok  outlet p_rgh: $(grep -A1 'outlet' $B/$n/0/p_rgh | grep type | awk '{print $2}') $(python3 $S/export_case.py $B/$n > $B/$n.exp 2>&1 && echo export-ok || echo export-FAILED)"
  else echo "$n FAILED"; tail -n 5 $B/$n/log.solver; fi
}
run real_lam_A_dis --props real --mode discharge --inlet-type A
run real_sst_B_dis --props real --mode discharge --inlet-type B --uin 0.2 --turb kOmegaSST --buoy
run real_lam_B_chg_strat --props real --inlet-type B --yi 0.5
run bous_lam_A --props boussinesq
