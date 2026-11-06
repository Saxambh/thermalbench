import numpy as np, sys, glob
f = glob.glob(sys.argv[1] + "/postProcessing/*/*/volFieldValue.dat")
f = [x for x in f if "liquid" in x.lower() or "alpha" in open(x).read(400)][0] if len(f) > 1 else f[0]
a = np.array([[float(v) for v in l.split()[:2]] for l in open(f) if l.strip() and not l.startswith("#")])
t, lf = a[:, 0] / 60, a[:, 1]
tm = [10, 20, 30, 40, 50, 60, 80, 100, 120, 140, 160, 180]; ex = [0.06, 0.12, 0.18, 0.25, 0.32, 0.40, 0.55, 0.68, 0.80, 0.89, 0.95, 0.98]
m = np.interp(tm, t, lf); d = m - np.array(ex)
print("file", f.split("postProcessing/")[1])
print("t(min)  exp   model  diff"); [print(f"{x:5.0f}  {e:.2f}  {y:.3f}  {z:+.3f}") for x, e, y, z in zip(tm, ex, m, d)]
full = t[np.argmax(lf >= 0.995)] if (lf >= 0.995).any() else float("nan")
print(f"mean abs dev {np.mean(np.abs(d)):.3f}, mean {np.mean(d):+.3f}, largest {d[np.abs(d).argmax()]:+.3f} at {tm[np.abs(d).argmax()]} min; full melt (0.995) {full:.0f} min vs exp ~195")
