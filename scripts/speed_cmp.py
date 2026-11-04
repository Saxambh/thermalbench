# Per-run speed vs the cost model fitted on laptop runs: ratio > 1 means slower than the laptop would be.
import os, re, json, glob, subprocess, numpy as np
c = np.array([3.129, 0.523, 1.329, 0.255])
O = os.path.expanduser("~/of_runs/full_h5mm")
for d in sorted(glob.glob(f"{O}/*/log.solver")):
    case = os.path.dirname(d)
    if os.path.exists(f"{case}/DONE"): continue
    tail = subprocess.run(["tail", "-c", "20000", d], capture_output=True, text=True).stdout
    t = re.findall(r"\nTime = (\S+)", tail); ex = re.findall(r"ExecutionTime = (\S+) s", tail)
    if not t or not ex: continue
    j = json.load(open(f"{case}/case.json"))
    pred = np.exp(c @ [1, np.log(j["u_in_m_s"]), np.log(j["W_m"]), j["turbulence"] != "laminar"])
    act = float(ex[-1]) / float(t[-1])
    print(f"{j['case']:10} u_in {j['u_in_m_s']:.4f} W {j['W_m']:.2f} cells {j['nx']*j['ny']:6d}  "
          f"wall/sim-s {act:6.2f}  model {pred:6.2f}  ratio {act/pred:5.2f}")
