#!/bin/bash
# Hourly quality check of finished runs, at low priority. Usage: qc_loop.sh <qc_runs.py> <batch_dir>...
QC=$1; shift
while true; do
  for b in "$@"; do [ -d "$b" ] && nice -n 15 python3 "$QC" "$b" > "$b/qc_last.txt" 2>&1; done
  sleep 3600
done
