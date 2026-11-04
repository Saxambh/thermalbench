#!/bin/bash
# Status of the 3D Lou validation run
C=${1:-~/of_runs/lou3d/sst}
cd "$C" || exit 1
echo "date: $(date -u)"
echo "ranks running: $(ps -eo cmd | grep -c '[b]uoyantPimpleFoam -parallel')"
echo "batch solvers: $(ps -eo cmd | grep '[b]uoyantPimpleFoam' | grep -vc parallel)"
L=$(ls -t log* 2>/dev/null | head -1)
echo "log: $L ($(stat -c %y "$L" | cut -c1-19))"
grep -E '^Time = ' "$L" | tail -1
grep -E 'Courant Number' "$L" | tail -1
grep -E '^deltaT' "$L" | tail -1
grep -E 'ExecutionTime' "$L" | tail -1
grep -ciE 'fatal|nan|error' "$L" | sed 's/^/fatal|nan|error lines: /'
tail -3 "$L"
# speed: sim time and wall time 30 steps ago vs now
python3 - "$L" <<'EOF'
import re, sys
t, w = [], []
for line in open(sys.argv[1]):
    if line.startswith('Time = '): t.append(float(line.split()[2]))
    m = re.search(r'ClockTime = ([\d.]+)', line)
    if m: w.append(float(m.group(1)))
n = min(len(t), len(w))
k = min(200, n - 1)
if k >= 20:
    dt_sim = t[n-1] - t[n-1-k]; dt_wall = max(w[n-1] - w[n-1-k], 1e-9)
    rate = dt_sim / dt_wall
    print(f"steps {n}, sim {t[n-1]:.2f} s, wall {w[n-1]/3600:.2f} h")
    print(f"recent rate {rate*3600:.2f} sim-s per wall-h; {dt_wall/k:.2f} s/step")
    print(f"ETA to 750 s: {(750 - t[n-1]) / rate / 3600:.1f} h ({(750 - t[n-1]) / rate / 86400:.2f} days)")
EOF
echo "axis profiles: $(ls postProcessing/axis 2>/dev/null | wc -l), last $(ls postProcessing/axis 2>/dev/null | sort -g | tail -1)"
for f in postProcessing/outletT/*/*.dat postProcessing/meanT/*/*.dat; do [ -f "$f" ] && echo "$f: $(tail -1 "$f")"; done
