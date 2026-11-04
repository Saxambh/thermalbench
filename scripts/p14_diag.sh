#!/bin/bash
C=~/of_runs/pilot_h5mm/P14_lam
L=$C/log.solver
grep -n "^Time = " $L | tail -3
grep "Courant Number" $L | tail -3
grep "^deltaT" $L | tail -3
echo "-- last 6 steps, h residual and p_rgh iterations"
awk '/^Time = /{t=$3} /Solving for h,/{h=$8} /Solving for p_rgh/{p=$15} /^ExecutionTime/{print t, h, p}' $L | tail -8
echo "-- h residual history (every 2000th step)"
awk '/^Time = /{t=$3} /Solving for h,/{print t, $8}' $L | awk 'NR%2000==0' | tail -15
echo "-- meanT tail"; tail -3 $C/postProcessing/meanT/0/volFieldValue.dat
grep -c "^Time = " $L
python3 -c "import json;d=json.load(open('$C/case.json'));print({k:d[k] for k in list(d)[:30]})"
