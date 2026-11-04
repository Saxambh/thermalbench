#!/bin/bash
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
B=~/of_runs/flux_test; rm -rf $B; mkdir -p $B
python3 $S/make_tank_case.py $B/c --props real --mode discharge --uin 0.05 --end 20 --write 5 > /dev/null || { echo GEN FAILED; exit 1; }
cd $B/c && blockMesh > log.blockMesh 2>&1 && buoyantPimpleFoam > log.solver 2>&1
grep -c "FOAM FATAL\|FOAM Warning" log.solver
ls postProcessing
tail -2 postProcessing/outletFlux/0/surfaceFieldValue.dat postProcessing/outletHflux/0/surfaceFieldValue.dat
python3 $S/export_case.py $B/c && python3 -c "
import h5py; f=h5py.File('$B/c/thermbench.h5'); print([k for k in f['series']])"
