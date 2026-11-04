#!/bin/bash
C=~/of_runs/pilot_h5mm/P14_lam
for f in U T p_rgh p; do echo "== $f"; sed -n '/^boundaryField/,$p' $C/0/$f | sed -n '/outlet/,/}/p'; done
echo "== outletT tail"; tail -4 $C/postProcessing/outletT/0/surfaceFieldValue.dat
echo "== outletT around 1700-1830"; awk '$1>1700 && $1<1830 && NR%400==0' $C/postProcessing/outletT/0/surfaceFieldValue.dat | head -20
