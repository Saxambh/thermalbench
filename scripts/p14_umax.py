import re, os, sys, numpy as np
sys.path.insert(0, "/mnt/c/Users/Saxam/AppData/Local/Temp/claude/C--Users-Saxam/9b6c9561-2c28-4e96-aceb-94a1b7f26d31/scratchpad/thermbench")
C = os.path.expanduser("~/of_runs/pilot_h5mm/P14_lam")
times = sorted([d for d in os.listdir(C) if re.fullmatch(r"[\d.]+", d) and d != "0"], key=float)
def vec(p):
    s = open(p).read()
    m = re.search(r"internalField\s+nonuniform\s+List<vector>\s*\d+\s*\((.*?)\n\)\s*;", s, re.S)
    return np.array(re.findall(r"\(([^)]*)\)", m.group(1)), dtype=object)
def sca(p):
    s = open(p).read()
    m = re.search(r"List<scalar>\s*\d+\s*\((.*?)\n\)", s, re.S)
    return np.array(m.group(1).split(), float)
nx = ny = 200; h = 0.005
for t in times[::8] + times[-3:]:
    U = np.array([list(map(float, v.split())) for v in vec(f"{C}/{t}/U")])
    m = np.hypot(U[:,0], U[:,1]); i = m.argmax()
    T = sca(f"{C}/{t}/T")
    print(f"t={t:>6}  |U|max {m.max():.3f} m/s at x={(i%nx+.5)*h:.3f} y={(i//nx+.5)*h:.3f}  "
          f"|U|99.9% {np.quantile(m,.999):.4f}  T range {T.min()-273.15:.1f}..{T.max()-273.15:.1f} C")
