import re, os, numpy as np
b = os.path.expanduser("~/of_runs/p14_bctest")
for v in ("ctrl", "fix"):
    L = open(f"{b}/{v}/log.solver").read()
    t = re.findall(r"\nTime = ([\d.e+-]+)", L)
    print(f"{v}: last t={t[-1] if t else '?'}, FATAL={'FOAM FATAL' in L}, End={'\nEnd' in L}")
    for d in sorted([d for d in os.listdir(f'{b}/{v}') if re.fullmatch(r'[\d.]+', d)], key=float):
        s = open(f"{b}/{v}/{d}/U").read()
        m = re.search(r"internalField\s+nonuniform\s+List<vector>\s*\d+\s*\((.*?)\n\)\s*;", s, re.S)
        U = np.array([x.split()[:2] for x in re.findall(r"\(([^()]*)\)", m.group(1))], float)
        mag = np.hypot(U[:,0], U[:,1]); i = mag.argmax()
        print(f"   t={d:>5} |U|max {mag.max():.3f} m/s at x={(i%200+.5)*.005:.3f} y={(i//200+.5)*.005:.3f}")
    o = np.loadtxt(f"{b}/{v}/postProcessing/outletT/1625/surfaceFieldValue.dat", comments="#")
    print("   outlet T at", [f"{o[k,0]:.0f}s:{o[k,1]-273.15:.1f}C" for k in np.linspace(0, len(o)-1, 6).astype(int)])
