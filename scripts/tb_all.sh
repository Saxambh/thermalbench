#!/bin/bash
# Live view of the ThermalStorageBench batch on all three PCs (laptop, lab, pc3). Refreshes every 60 s.
# Run in a laptop Ubuntu window:  bash "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/scripts/tb_all.sh"
# Ctrl+C closes the view only; the simulations are not affected.
unset LD_LIBRARY_PATH
D="$(dirname "$(readlink -f "$0")")"
R="$(dirname "$D")"
while true; do
  out="$(
    echo "  ThermalStorageBench batch, all PCs        $(date '+%a %d %b %H:%M:%S')"
    echo
    echo "  LAPTOP  $(bash "$D/tb_one.sh" "$R/design_v2_full_laptop_n2.csv" 2>/dev/null)"
    echo
    echo "  LAB     $(ssh -o BatchMode=yes -o ConnectTimeout=10 labpc 'bash -s -- ~/thermbench/design_v2_full_lab_n2.csv' < "$D/tb_one.sh" 2>/dev/null || echo 'not reachable')"
    echo
    echo "  PC3     $(ssh -o BatchMode=yes -o ConnectTimeout=10 saxam@pc3 'bash -s -- ~/thermbench/design_v2_full_pc3_n2.csv' < "$D/tb_one.sh" 2>/dev/null || echo 'not reachable')"
  )"
  clear
  echo "$out"
  echo
  echo "  (refreshes every 60 s; Ctrl+C closes this view only)"
  sleep 60
done
