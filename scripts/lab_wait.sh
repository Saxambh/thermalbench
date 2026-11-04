#!/bin/bash
# Wait (up to 7 h) until the lab convergence batch writes ALL_DONE, then print status.
unset LD_LIBRARY_PATH
for i in $(seq 1 84); do
  ssh -o ConnectTimeout=20 labpc 'test -f ~/of_runs/convergence/ALL_DONE' && break
  sleep 300
done
bash /mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench/lab_status.sh
