#!/bin/bash
ssh labpc 'bash -s' <<'R'
pkill -u saxam -f run_batch.py
pkill -u saxam -f buoyantPimpleFoam
sleep 5
echo "batch drivers left: $(pgrep -u saxam -fc run_batch.py)"
echo "solvers left: $(pgrep -u saxam -fc buoyantPimpleFoam)"
uptime
R
