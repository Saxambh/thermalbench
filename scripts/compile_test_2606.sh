#!/bin/bash
# Short smoke test on v2606: does the coded k-buoyancy source compile and run?
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
C=~/of_runs/v2606_smoke/sst_buoyk
rm -rf $C
python3 $SRC/make_tank_case.py $C --uin 0.1 --end 2 --write 1 --turb kOmegaSST --buoyk
cd $C
blockMesh > log.blockMesh 2>&1 || { echo blockMesh FAILED; tail log.blockMesh; exit 1; }
buoyantBoussinesqPimpleFoam > log.solver 2>&1
echo "rc=$?"
grep -i -m3 -B2 -A12 "error\|fatal" log.solver
grep -m3 -i "kBuoyancy\|codedSource\|Selecting finite volume" log.solver
tail -5 log.solver
