#!/bin/bash
ssh labpc 'bash -s' <<'X'
setsid nohup bash ~/thermbench/scripts/qc_loop.sh ~/thermbench/scripts/qc_runs.py ~/of_runs/full_h5mm > /dev/null 2>&1 < /dev/null &
sleep 30
ps -eo pid,args | grep "[q]c_loop"
ls -la ~/of_runs/full_h5mm/qc_last.txt
X
