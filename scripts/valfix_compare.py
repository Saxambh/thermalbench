#!/usr/bin/env python3
"""Compare the PCM validation re-runs with the final solver set-up (pcm_validate_fix.sh, pc4,
2026-11-04/05) against the papers' curves, as tabulated in validation_Vogel2019_pcm.md and
validation_Kamkari2014_fins.md (digitised by eye, +-0.02).
  python3 valfix_compare.py [dir]     dir default ~/tb_data/pc4/pcm_valfix (postProcessing copied)
Prints liquid fraction at the tabulated times, mean / largest deviation, and the full-melt time
t(0.995) (Kamkari's "end" times are full melt)."""
import glob, json, os, sys
import numpy as np

D = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/tb_data/pc4/pcm_valfix")

REF = {   # name: (time unit s, times, reference f_l, label, end time of the reference (min) or None)
    "vogel_fix": (3600, [0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
                  [0.16, 0.27, 0.47, 0.66, 0.80, 0.90, 0.965, 1.00], "Vogel B-2D (Fig. 7), hours", None),
    "vogel_fix:exp": (3600, [0.167, 0.333, 0.5, 0.667, 0.833, 1.0, 1.167, 1.333, 1.5, 1.667, 1.833, 2.0,
                             2.167, 2.333, 2.5, 2.667, 2.833, 3.0, 3.167],
                      [0.03, 0.155, 0.25, 0.34, 0.425, 0.505, 0.58, 0.65, 0.71, 0.765, 0.81, 0.85, 0.885,
                       0.91, 0.94, 0.96, 0.975, 0.985, 0.99], "Vogel experiment (Fig. 11), hours", None),
    "kam_n0": (60, [10, 20, 30, 40, 50, 60, 80, 100, 120, 140, 160, 180],
               [0.06, 0.12, 0.18, 0.25, 0.32, 0.40, 0.55, 0.68, 0.80, 0.89, 0.95, 0.98], "Kamkari plain wall (Fig. 6), min", 195),
    "kam_n1": (60, [10, 20, 30, 40, 50, 60, 80, 100, 120, 140, 160],
               [0.09, 0.18, 0.27, 0.35, 0.45, 0.56, 0.73, 0.83, 0.89, 0.95, 1.0], "Kamkari 1 fin (Fig. 6), min", 160),
    "kam_n3": (60, [10, 20, 30, 40, 50, 60, 80, 100, 120],
               [0.17, 0.35, 0.49, 0.61, 0.71, 0.79, 0.91, 0.97, 1.0], "Kamkari 3 fins (Fig. 6), min", 125),
    "kam_t45": (60, [20, 40, 60, 80, 100, 120], [0.17, 0.35, 0.52, 0.68, 0.83, 0.98],
                "Kamkari theta 45 (incl. Fig. 11), min", 122),
    "kam_t90": (60, [20, 40, 60, 80], [0.20, 0.42, 0.63, 0.85], "Kamkari from below (incl. Fig. 11), min", 92),
}


def series(case):
    f = sorted(glob.glob(f"{D}/{case}/postProcessing/liquidFraction/*/*.dat"))
    rows = []
    for fn in f:
        for l in open(fn):
            if l.strip() and not l.startswith("#"):
                p = l.split()
                rows.append((float(p[0]), float(p[1])))
    a = np.array(sorted(rows))
    return a[:, 0], a[:, 1]


out = {}
for key, (unit, ts, ref, label, end) in REF.items():
    case = key.split(":")[0]
    if not os.path.isdir(f"{D}/{case}"):
        continue
    t, lf = series(case)
    tmax = t[-1] / unit
    have = [i for i, x in enumerate(ts) if x <= tmax + 1e-9]
    m = np.interp(np.array(ts)[have] * unit, t, lf)
    r = np.array(ref)[have]
    dev = m - r
    full = np.nonzero(lf >= 0.995)[0]
    tfull = t[full[0]] / 60 if full.size else None
    print(f"\n{key}: {label}; simulated to {tmax:.3g}, final f_l {lf[-1]:.3f}"
          + (f", full melt (0.995) at {tfull:.0f} min" if tfull else ", not fully melted yet"))
    print("  t    " + " ".join(f"{x:6g}" for x in np.array(ts)[have]))
    print("  ref  " + " ".join(f"{x:6.3f}" for x in r))
    print("  run  " + " ".join(f"{x:6.3f}" for x in m))
    print(f"  mean |dev| {np.abs(dev).mean():.3f}, mean dev {dev.mean():+.3f}, largest {dev[np.argmax(np.abs(dev))]:+.3f} "
          f"at {np.array(ts)[have][np.argmax(np.abs(dev))]:g}"
          + (f"; full melt {tfull:.0f} vs ~{end} min ({100 * (tfull / end - 1):+.0f} %)" if tfull and end else ""))
    out[key] = {"times": [float(x) for x in np.array(ts)[have]], "ref": [float(x) for x in r], "run": [round(float(x), 4) for x in m],
                "mean_abs_dev": float(np.abs(dev).mean()), "mean_dev": float(dev.mean()),
                "t_full_min": None if tfull is None else float(tfull), "complete": bool(full.size)}
json.dump(out, open(f"{D}/valfix_compare.json", "w"), indent=1)
