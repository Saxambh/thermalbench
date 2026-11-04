#!/bin/bash
# Standalone reproduction case for the buoyancyTurbSource sign report.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
W=~/of_runs/bugcase; rm -rf $W; mkdir -p $W; cd $W
python3 $S/make_tank_case.py base --h 0.01 --uin 0 --end 0.5 --write 0.25 --turb kOmegaSST --buoy > /dev/null
python3 $S/sign_test2.py base stable
C=buoyancyTurbSourceSign
mkdir $C && cp -r base/0 base/constant base/system $C/
rm -f $C/case.json; sed -i '/^functions/,$d' $C/system/controlDict; echo "functions {}" >> $C/system/controlDict
cat > $C/Allrun <<'A'
#!/bin/sh
# buoyantBoussinesqPimpleFoam, closed box at rest (inlet velocity 0), linear stable T profile 20->60 C,
# uniform k = 1e-4, omega = 1. Compares the initial domain-mean dk/dt with and without buoyancyTurbSource.
# Analytic buoyancy production at t = 0: Gb = beta*nut/Prt*(grad T . g) = 3.5e-4*1e-4/0.85*(40*-9.81) = -1.62e-5 m2/s3
cd "${0%/*}" || exit 1
. ${WM_PROJECT_DIR:?}/bin/tools/RunFunctions
runApplication blockMesh
for v in without with; do
    rm -rf $v && mkdir $v && cp -r 0 constant system $v/
    [ $v = without ] && rm -f $v/constant/fvOptions
    (cd $v && setExprFields > log.setExprFields 2>&1 && buoyantBoussinesqPimpleFoam > log.solver 2>&1)
done
for v in without with; do
    foamDictionary -entry internalField $v/0.25/k -value | tr -d '()' | awk -v v=$v 'NR>2 && NF==1 {s+=$1; n++} END {printf "%-8s mean dk/dt over 0.25 s: %+.3e m2/s3\n", v, (s/n-1e-4)/0.25}'
done
echo "difference (with - without) should be about Gb = -1.62e-5 (stable stratification damps k)"
A
chmod +x $C/Allrun
cp -r base/constant/polyMesh $C/constant/ 2>/dev/null; rm -rf $C/constant/polyMesh
(cd $C && ./Allrun > /dev/null 2>&1; ./Allrun 2>/dev/null | tail -3)
(cd $C && rm -rf with without log.* constant/polyMesh)
tar czf "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/buoyancyTurbSourceSign_case.tgz" $C
ls -la "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/buoyancyTurbSourceSign_case.tgz"; ls $C $C/constant
