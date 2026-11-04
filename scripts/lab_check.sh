#!/bin/bash
# Copy the generator to the lab PC and run the 5 s laminar check case there.
unset LD_LIBRARY_PATH
SRC=/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench
ssh labpc 'mkdir -p ~/thermbench/scripts ~/of_runs'
scp -q $SRC/make_tank_case.py $SRC/profile_summary.py labpc:thermbench/scripts/
ssh labpc 'bash -s' <<'EOF'
unset LD_LIBRARY_PATH
source /usr/lib/openfoam/openfoam2606/etc/bashrc
C=~/of_runs/check_lam5
rm -rf $C
python3 ~/thermbench/scripts/make_tank_case.py $C --h 0.005 --uin 0.02 --end 5 --write 5
cd $C && blockMesh > log.blockMesh 2>&1
S=$(date +%s); buoyantBoussinesqPimpleFoam > log.solver 2>&1; echo "rc=$? wall=$(( $(date +%s)-S ))s steps=$(grep -c '^Time =' log.solver)"
echo "lab meanT at 5 s: $(tail -1 postProcessing/meanT/0/volFieldValue.dat)"
md5sum 5/T
EOF
