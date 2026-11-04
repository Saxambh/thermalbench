#!/bin/bash
# Full 3D validation run (Lou 2023, uniform baffles), 8 cores on the laptop, 0-750 s.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
C=~/of_runs/lou3d/sst
NP=${NP:-8}
if [ ! -d $C/processor0 ]; then
  rm -rf $C; python3 $S/make_lou3d.py $C --turb kOmegaSST --end 750 > $C.gen.log 2>&1 || exit 1
  cat > $C/system/decomposeParDict <<D
FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains $NP;
method          scotch;
D
  (cd $C && decomposePar > log.decomposePar 2>&1) || exit 1
fi
cd $C && nice -n 3 mpirun -np $NP buoyantPimpleFoam -parallel >> log.solver 2>&1
echo "$(date) exit $?" >> log.solver
