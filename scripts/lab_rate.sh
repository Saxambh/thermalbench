#!/bin/bash
unset LD_LIBRARY_PATH
ssh labpc 'bash -s' <<'EOF'
cd ~/of_runs/convergence
for n in lam_L1 lam_L2 lam_L3 tur_L1 tur_L2 tur_L3; do
  a=$(grep -c "^Time =" $n/log.solver); sleep 0; echo "$n $a"
done > /tmp/r1
sleep 30
for n in lam_L1 lam_L2 lam_L3 tur_L1 tur_L2 tur_L3; do
  b=$(grep -c "^Time =" $n/log.solver)
  a=$(grep "^$n " /tmp/r1 | cut -d" " -f2)
  dt=$(grep "^deltaT" $n/log.solver | tail -1)
  t=$(grep "^Time =" $n/log.solver | tail -1)
  echo "$n steps/s=$(( (b-a)/30 )) total_steps=$b $dt $t"
done
lscpu | grep -E "^Thread|^Core|^Socket|^CPU\(s\)"
EOF
