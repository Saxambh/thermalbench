#!/bin/bash
# Vogel & Thess (2019) B-2D validation: 3.5 h of melting at 0.5 mm (dt 0.1), 0.25 mm (dt 0.1)
# and 0.5 mm (dt 0.05). Detached; restart-safe only from scratch.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
cd ~/of_runs/pcm
run() {   # name h maxdt nprocs
  local c=$1
  rm -rf $c && python3 $S/make_pcm_case.py $c --h $2 --maxdt $3 --end 12600 --write 300 > /dev/null
  cd $c && blockMesh > log.blockMesh 2>&1
  if [ $4 -gt 1 ]; then
    printf 'FoamFile\n{\n version 2.0;\n format ascii;\n class dictionary;\n object decomposeParDict;\n}\nnumberOfSubdomains %d;\nmethod scotch;\n' $4 > system/decomposeParDict
    decomposePar > log.decompose 2>&1
    nice -n 5 mpirun -np $4 buoyantPimpleFoam -parallel > log.solver 2>&1
    reconstructPar -latestTime > log.reconstruct 2>&1
  else
    nice -n 5 buoyantPimpleFoam > log.solver 2>&1
  fi
  echo "$c finished $(date -u '+%F %H:%M') UTC" >> ../validate.log
  cd ..
}
echo "started $(date -u '+%F %H:%M') UTC" >> validate.log
run vogel_h05 0.0005 0.1 1 &
run vogel_h025 0.00025 0.1 4 &
run vogel_h05_dt05 0.0005 0.05 2 &
wait
