#!/bin/bash
# Live on-screen status of the ThermBench simulations on pc4 (refreshes every 20 s).
# Run in pc4's Ubuntu window: bash ~/thermbench/scripts/pc4_screen.sh   (Ctrl+C closes the view only)
P=~/of_runs/pcm_full/runs; PL=~/thermbench/pcm_full_pc4.csv
while true; do
  pt=$( [ -f $PL ] && tail -n +2 $PL | wc -l || echo 0); pd=$(ls $P/*/DONE 2>/dev/null | wc -l)
  pct=$(( pt > 0 ? 100 * pd / pt : 0 ))
  bar=$(printf '%*s' $((pct / 2)) '' | tr ' ' '#'); pad=$(printf '%*s' $((50 - pct / 2)) '' | tr ' ' '.')
  clear
  printf '\e[1;41;97m'
  echo "                                                                              "
  echo "   PLEASE DO NOT CLOSE THIS WINDOW, SHUT DOWN, RESTART OR LET THIS PC SLEEP   "
  echo "                                                                              "
  printf '\e[0m\e[1;33m\n'
  echo "   Research simulations are running on this PC (Saxam Bhattarai: melting of"
  echo "   phase-change materials for thermal energy storage, OpenFOAM CFD)."
  echo "   Expected to finish around Thursday 5 November."
  echo "   Minimising this window is fine. Closing it or a power cut stops the work."
  echo "   If the power went off: please open Ubuntu again and tell Saxam. Thank you!"
  printf '\e[0m\n'
  echo "   $(date '+%a %d %b %H:%M:%S')     CPU load: $(cut -d' ' -f1 /proc/loadavg)     simulations running now: $(pgrep -c buoyantPimple)"
  echo
  echo "   Finished: $pd of $pt cases   [$bar$pad] $pct%"
  echo
  echo "   Last finished:"
  grep " ok " $P/batch.log 2>/dev/null | tail -n 3 | cut -d'|' -f1 | sed 's/^/     /'
  grep -E "FAIL" $P/batch.log 2>/dev/null | tail -n 2 | sed 's/^/     problem: /'
  sleep 20
done
