#!/bin/bash
# 3D Lou validation on the lab PC, lower baffle refined like the upper one (mesh sensitivity of the laptop 'sst' run).
# Restartable: regenerates only if not yet decomposed.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=~/thermbench/scripts
C=~/of_runs/lou3d/sst_finelow
NP=${NP:-8}
if [ ! -d $C/processor0 ]; then
  rm -rf $C; mkdir -p ~/of_runs/lou3d
  python3 $S/make_lou3d.py $C --turb kOmegaSST --end 750 --fine-lower > $C.gen.log 2>&1 || exit 1
  cat > $C/system/decomposeParDict <<D
FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains $NP;
method          scotch;
D
  (cd $C && decomposePar > log.decomposePar 2>&1) || exit 1
fi
cd $C && nice -n 3 mpirun -np $NP buoyantPimpleFoam -parallel >> log.solver 2>&1
echo "$(date) exit $?" >> log.solver
