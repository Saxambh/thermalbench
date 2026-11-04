#!/bin/bash
# Live view of every running ThermalStorageBench simulation on all four machines (laptop, lab, pc3, pc4).
# Run in an Ubuntu (WSL) window on the laptop:
#   bash "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/scripts/tb_monitor.sh"
# Refreshes every 60 s. Ctrl+C closes the view only; nothing is started or stopped.
R="$(dirname "$(readlink -f "$0")")/tb_runs.py"
T=$(mktemp -d)
trap 'rm -rf $T' EXIT
while true; do
  python3 "$R" > $T/laptop 2>/dev/null &
  for h in labpc:lab saxam@pc3:pc3 saxam@pc4:pc4; do
    ( timeout 40 ssh -o BatchMode=yes -o ConnectTimeout=15 ${h%%:*} python3 - < "$R" > $T/${h##*:} 2>/dev/null || echo "OFF|${h##*:}" > $T/${h##*:} ) &
  done
  wait
  clear
  python3 - $T <<'PY'
import os, sys
T = sys.argv[1]; lines = []
for m in ("laptop", "lab", "pc3", "pc4"):
    try: lines += [l.rstrip("\n").split("|") for l in open(f"{T}/{m}") if "|" in l]
    except OSError: lines.append(["OFF", m])
import time
print(f" ThermalStorageBench runs, all machines   {time.strftime('%a %d %b %H:%M:%S')} (local)   refresh 60 s, Ctrl+C to close\n")
for m in ("laptop", "lab", "pc3", "pc4"):
    off = any(l[0] == "OFF" and l[1] == m for l in lines)
    h = [l for l in lines if l[0] == "HOST" and l[1] == m]
    runs = sorted([l for l in lines if l[0] == "RUN" and l[1] == m], key=lambda l: (l[2], -float(l[5])))
    done = ", ".join(f"{l[2]} {l[3]} done" for l in lines if l[0] == "DONE" and l[1] == m)
    head = "NOT REACHABLE" if off else f"load {h[0][2]} / {h[0][3]} threads, {len(runs)} running" if h else ""
    print(f"\033[1;36m== {m.upper():6s} {head}\033[0m   {done}")
    for l in runs:
        _, _, kind, name, np_, frac, el, eta, info = l
        f = float(frac); bar = "#" * int(f * 20) + "." * (20 - int(f * 20))
        cores = f" x{np_}" if int(np_) > 1 else ""
        print(f"   {kind:4s} {name:28.28s}{cores:4s} [{bar}] {100 * f:5.1f} %  {info:30s} running {float(el):5.1f} h"
              f"  left {('~' + eta + ' h') if eta else '   ?'}")
    print()
PY
  sleep 60
done
