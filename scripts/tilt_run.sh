#!/bin/bash
# Kamkari, Shokouhmand & Bruno (2014) inclination validation on the laptop: unfinned lauric acid,
# 50 x 120 mm, Tw 70 C, T0 25 C, tilt 45 and 90 (paper's theta 45 and 0). The vertical case is
# kamkari_70_n0 on pc3. 0.5 mm cells, 200 min, one core each.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
S=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
cd ~/of_runs/pcm
run() {   # name tilt
  rm -rf $1 && python3 $S/make_pcm_case.py $1 --material lauric --W 0.05 --H 0.12 --right wall --top wall \
      --tw 70 --t0 25 --h 0.0005 --tilt $2 --end 12000 --write 300 > $1.gen.log
  (cd $1 && blockMesh > log.blockMesh 2>&1 && nice -n 5 buoyantPimpleFoam > log.solver 2>&1)
  echo "$1 finished $(date -u '+%F %H:%M') UTC" >> tilt.log
}
echo "started $(date -u '+%F %H:%M') UTC" >> tilt.log
run kamkari_70_tilt45 45 &
run kamkari_70_tilt90 90 &
wait
