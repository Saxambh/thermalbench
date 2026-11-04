#!/bin/bash
unset LD_LIBRARY_PATH
ssh labpc 'bash -s' <<'EOF'
cd ~/of_runs/fine128_h3mm
for c in T0009_lam T0061_lam T0065_lam T0033_lam T0025_lam; do
  python3 - $c <<'PY'
import json, sys, re
c = sys.argv[1]; m = json.load(open(f"{c}/case.json"))
txt = open(f"{c}/log.solver").read()[-200000:]
dts = [float(x) for x in re.findall(r"^deltaT = ([0-9.eE+-]+)", txt, re.M)][-200:]
co = [float(x) for x in re.findall(r"Courant Number mean: [0-9.eE+-]+ max: ([0-9.eE+-]+)", txt)][-200:]
it = [int(x) for x in re.findall(r"Solving for p_rgh.*No Iterations (\d+)", txt)][-200:]
cl = re.findall(r"ClockTime = ([0-9.]+)", txt)
print(f"{c}: u={m['u_in_m_s']:.4f} s={m['slot_m']} W={m['W_m']} type={m['inlet_type']} {m['mode']} "
      f"Re={m['Re_in']:.0f} Ri={m['Ri_H']:.0f} end={m['end_time_s']:.0f}s cells={m['nx']*m['ny']}")
print(f"   last dt {dts[-1]:.4g}  mean dt(last200) {sum(dts)/len(dts):.4g}  maxCo {max(co):.3f}  "
      f"p_rgh iters (mean) {sum(it)/len(it):.0f}  clock {cl[-1]} s")
PY
done
EOF
