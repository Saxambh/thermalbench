#!/bin/bash
# wait until the coarse test has run ~12 min of solver time, then report
L=~/of_runs/lou3d/test/log.solver
until [ -f $L ] && [ $(( $(date +%s) - $(stat -c %Y ~/of_runs/lou3d/test/log.decomposePar 2>/dev/null || date +%s) )) -gt 720 ]; do sleep 20; done
grep -E 'cells|ratio|u_in|radius' ~/of_runs/lou3d/test/case.json
grep -E 'Max non-orth|Mesh OK' ~/of_runs/lou3d/test/log.checkMesh
grep '^Time = ' $L | tail -1; grep -c '^Time = ' $L
grep Courant $L | tail -1; grep '^deltaT' $L | tail -1; grep ExecutionTime $L | tail -1
grep -c 'FOAM FATAL' $L
tail -1 ~/of_runs/lou3d/test/postProcessing/meanT/0/volFieldValue.dat
