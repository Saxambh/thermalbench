#!/bin/bash
ssh labpc 'bash -s' <<'R'
cd ~/of_runs/fine128_h3mm
for d in */; do
  d=${d%/}; [ -f $d/log.solver ] || continue
  st=$( [ -f $d/DONE ] && echo done || (grep -q "FOAM FATAL" $d/log.solver && echo FAILED || echo running) )
  python3 - $d $st <<'PY'
import json, sys, re, subprocess
d, st = sys.argv[1:]
j = json.load(open(f"{d}/case.json"))
tail = subprocess.run(["tail", "-c", "3000000", f"{d}/log.solver"], capture_output=True, text=True).stdout
dts = [float(x) for x in re.findall(r"\ndeltaT = (\S+)", tail)]
co = [float(x) for x in re.findall(r"Courant Number mean: \S+ max: (\S+)", tail)]
u = j["u_in_m_s"]; h = j["mesh_h_m"]
umax = (0.5*h/min(dts[-200:])) if dts else float("nan")
print(f"{d:14} {st:8} {j['mode']:9} {j['inlet_type']} u_in={u:.4f}  implied |U|max~{umax:.3f} m/s ({umax/u:5.1f}x u_in)  maxCo(last) {max(co[-200:]) if co else 0:.2f}")
PY
done
R
