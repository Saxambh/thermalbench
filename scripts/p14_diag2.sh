#!/bin/bash
C=~/of_runs/pilot_h5mm/P14_lam
L=$C/log.solver
grep -E "maxCo|maxDeltaT|adjustTimeStep" $C/system/controlDict
sed -n '/PIMPLE/,/}/p' $C/system/fvSolution
echo "-- max Co over last ~60 steps"
grep "Courant Number" $L | tail -60 | awk '{print $6}' | tr '\n' ' '; echo
echo "-- max Co, sampled through run (every 5000th)"
grep "Courant Number" $L | awk 'NR%5000==0{printf "%s ", $6}'; echo
echo "-- dt sampled"
grep "^deltaT" $L | awk 'NR%5000==0{printf "%s ", $3}'; echo
echo "-- p_rgh iterations, sampled"
awk '/Solving for p_rgh/{n++; if(n%10000==0) printf "%s ", $15}' $L; echo
