#!/bin/bash
# ThermalStorageBench progress on both machines (laptop + lab PC).
# Live view, refreshing every 30 s:  tbstat -w   (Ctrl+C to leave)
unset LD_LIBRARY_PATH
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ "$1" = "-w" ]; then exec watch -n 30 -t "bash '$HERE/tbstat.sh'"; fi
python3 "$HERE/tbstat.py"
echo
ssh -o ConnectTimeout=8 -o BatchMode=yes labpc 'python3 -' < "$HERE/tbstat.py" 2>/dev/null \
  || echo "=== lab PC not reachable (Ubuntu window closed, PC asleep, or offline)"
