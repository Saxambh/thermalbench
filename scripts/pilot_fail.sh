#!/bin/bash
B=~/of_runs/pilot_h5mm
grep -v ",ok," $B/batch_status.csv | head
for d in $B/*/; do [ -f $d/DONE ] || { echo "== $d"; ls $d; tail -n 25 $d/log.solver 2>/dev/null; }; done
