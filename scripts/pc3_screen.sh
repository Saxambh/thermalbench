#!/bin/bash
# Live on-screen status of the ThermBench simulations on pc3 (refreshes every 20 s; Ctrl+C closes the view only).
# Phase 1: tank CFD (~/of_runs/full_h5mm). Phase 2 (from about 4 Nov): PCM melting CFD (~/of_runs/pcm_full/runs).
T=~/of_runs/full_h5mm; TL=~/thermbench/design_v2_full_pc3_n2.csv
P=~/of_runs/pcm_full/runs; PL=~/thermbench/pcm_full_pc3.csv
bar() { local p=$1; printf '[%s%s] %3d%%' "$(printf '%*s' $((p / 2)) '' | tr ' ' '#')" "$(printf '%*s' $((50 - p / 2)) '' | tr ' ' '.')" $p; }
while true; do
  tt=$( [ -f $TL ] && tail -n +2 $TL | wc -l || echo 0); td=$(ls $T/*/DONE 2>/dev/null | wc -l)
  pt=$( [ -f $PL ] && tail -n +2 $PL | wc -l || echo 0); pd=$(ls $P/*/DONE 2>/dev/null | wc -l)
  clear
  printf '\e[1;33m'
  echo "  ============================================================================"
  echo "   PLEASE DO NOT SHUT DOWN, RESTART OR LET THIS PC SLEEP"
  echo "   Saxam's research simulations are running here (thermal storage CFD,"
  echo "   OpenFOAM). Now in two parts; expected to finish around 8 November."
  echo "   Closing this window is OK, the simulations keep running in the background."
  echo "   Thank you!"
  echo "  ============================================================================"
  printf '\e[0m\n'
  echo "   $(date '+%a %d %b %H:%M:%S')     CPU load: $(cut -d' ' -f1 /proc/loadavg)   simulations running now: $(pgrep -c buoyantPimple)"
  echo
  echo "   Part 1, water tank:      $td of $tt   $(bar $(( tt > 0 ? 100 * td / tt : 0 )))"
  echo "   Part 2, melting (PCM):   $pd of $pt   $(bar $(( pt > 0 ? 100 * pd / pt : 0 )))"
  echo
  echo "   Last finished:"
  { tail -n 2 $T/batch_status.csv 2>/dev/null | cut -d, -f1,2,5; tail -n 2 $P/batch.log 2>/dev/null | cut -c1-70; } | sed 's/^/     /'
  sleep 20
done
