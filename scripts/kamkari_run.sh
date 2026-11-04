#!/bin/bash
# Kamkari & Shokouhmand (2014) fin validation on pc3: lauric acid, 50 x 120 mm, Tw 70 C,
# T0 25 C, 0 / 1 / 3 fins (4 mm x 25 mm, isothermal), 0.5 mm cells, 200 min. One core each.
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
G=~/thermbench/scripts/make_pcm_case.py
mkdir -p ~/of_runs/pcm && cd ~/of_runs/pcm
run() {   # name nfins
  rm -rf $1 && python3 $G $1 --material lauric --W 0.05 --H 0.12 --right wall --top wall \
      --tw 70 --t0 25 --h 0.0005 --nfins $2 --fin-len 0.025 --fin-t 0.004 --end 12000 --write 300 > $1.gen.log
  (cd $1 && blockMesh > log.blockMesh 2>&1 && nice -n 5 buoyantPimpleFoam > log.solver 2>&1)
  echo "$1 finished $(date -u '+%F %H:%M') UTC" >> kamkari.log
}
echo "started $(date -u '+%F %H:%M') UTC" >> kamkari.log
run kamkari_70_n0 0 &
run kamkari_70_n1 1 &
run kamkari_70_n3 3 &
wait
