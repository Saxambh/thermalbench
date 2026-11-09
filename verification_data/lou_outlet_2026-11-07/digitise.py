"""Digitise Lou et al. (2023) Fig. 15a (initial baffle) and 15b: the Th = 333.15 K curve (MATLAB yellow).
Axis calibration from the plot frame (long dark lines); axis limits sit on the frame:
(a) t* 0..1.5, Ri 0..2.0; (b) t* 0..1.5, sigma 0..1.0."""
import json, sys
import numpy as np
from PIL import Image

img = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
H, W, _ = img.shape


def frame(x0, x1, y0, y1):
    """Plot-frame pixel box inside a search window: rows/columns that are mostly dark."""
    sub = img[y0:y1, x0:x1]
    dark = sub.sum(2) < 200
    rows = np.where(dark.mean(1) > 0.6)[0] + y0
    cols = np.where(dark.mean(0) > 0.6)[0] + x0
    return cols.min(), cols.max(), rows.min(), rows.max()


def yellow(sub):
    # MATLAB default yellow (237, 177, 32); tight colour distance excludes the orange-red star edges
    d = np.sqrt(((sub - np.array([237, 177, 32])) ** 2).sum(-1))
    return d < 55


def extract(box, ylim, legend, start):
    L, R, T, B = box
    out = []
    for x in range(L + 6, R - 5):
        ys = np.where(yellow(img[T + 3:B - 2, x:x + 1])[:, 0])[0] + T + 3
        ts = (x - L) / (R - L) * 1.5
        vals = ylim * (B - ys) / (B - T)
        lx0, lx1, ly0, ly1 = legend
        keep = ~((ts >= lx0) & (ts <= lx1) & (vals >= ly0) & (vals <= ly1))
        vals = np.sort(vals[keep])
        if not len(vals):
            continue
        # clusters of adjacent pixels; follow the cluster nearest the previous point (start on the plateau)
        groups = np.split(vals, np.where(np.diff(vals) > 3 * ylim / (B - T))[0] + 1)
        cent = np.array([g.mean() for g in groups])
        prev = out[-1][1] if out else start
        j = int(np.argmin(abs(cent - prev)))
        if out and abs(cent[j] - prev) > 0.08 * ylim:   # jump: not the curve in this column
            continue
        out.append((ts, float(cent[j])))
    return out


# window guesses (fractions of the full image): left column, panel (a) top quarter, panel (b) second quarter
boxA = frame(int(0.05 * W), int(0.5 * W), 0, int(0.33 * H))
boxB = frame(int(0.05 * W), int(0.5 * W), int(0.34 * H), int(0.66 * H))
print("frames", boxA, boxB)
a = extract(boxA, 2.0, (0.03, 0.55, 0.05, 0.80), 1.25)
b = extract(boxB, 1.0, (0.03, 0.75, 0.62, 0.98), 0.0)
json.dump({"frameA": [int(v) for v in boxA], "frameB": [int(v) for v in boxB], "Ri": a, "sigma": b},
          open("fig15_333K_initial.json", "w"))
for name, cur in (("Ri", a), ("sigma", b)):
    c = np.array(cur)
    print(name, len(c), "points")
    for t in (0.1, 0.3, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.3, 1.4, 1.48):
        i = np.argmin(abs(c[:, 0] - t))
        print(f"  t* {c[i, 0]:.3f}  {c[i, 1]:.3f}")
