#!/bin/bash
# Wait (up to 1 h) for the finest laminar convergence run, then compare all levels.
unset LD_LIBRARY_PATH
for i in $(seq 1 30); do
  ssh -o ConnectTimeout=20 labpc 'test -f ~/of_runs/convergence/lam_L3.done.txt' && break
  sleep 120
done
ssh labpc 'cat ~/of_runs/convergence/*.done.txt; python3 ~/thermbench/scripts/compare_convergence.py'
