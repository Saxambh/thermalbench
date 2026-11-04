#!/bin/bash
unset LD_LIBRARY_PATH
ssh labpc 'bash -s' <<'EOF'
cd ~/of_runs/convergence
for n in lam_L1 lam_L2 lam_L3 tur_L1 tur_L2 tur_L3; do
  t=$(grep "^Time =" $n/log.solver 2>/dev/null | tail -1)
  f=$(grep -ci fatal $n/log.solver 2>/dev/null)
  d=$(cat $n.done.txt 2>/dev/null)
  echo "$n | $t | fatal=$f | $d"
done
ls ALL_DONE 2>/dev/null
uptime; free -g | head -2
EOF
