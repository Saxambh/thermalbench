#!/bin/bash
# Wake Claude when: laptop pilot finishes, any FATAL appears on either machine, or after MAXMIN minutes.
MAXMIN=${1:-120}
for i in $(seq 1 $((MAXMIN/5))); do
  n=$(pgrep -fc buoyantPimpleFoam)
  lf=$(grep -l "FOAM FATAL" ~/of_runs/pilot_v2/*/log.solver 2>/dev/null | wc -l)
  rf=$(ssh -o ConnectTimeout=20 labpc 'grep -l "FOAM FATAL" ~/of_runs/fine128_h3mm/*/log.solver 2>/dev/null | wc -l' 2>/dev/null)
  if [ "$n" = 0 ] || [ "$lf" != 0 ] || [ "${rf:-0}" != 0 ]; then echo "trigger: laptop solvers=$n laptopFATAL=$lf labFATAL=$rf"; exit 0; fi
  sleep 300
done
echo "timeout: laptop solvers=$n laptopFATAL=$lf labFATAL=$rf"
