#!/usr/bin/env python3
"""Jet penetration length h_j(t) from the 3D Lou case, compared with Lou et al. (2023) Fig. 5.

Definition (Lou Sec. 2.7): distance from the top inlet port to the point on the centreline
where the downward vertical velocity first turns upward, below the upper baffle. Lou's PIV
value at time t averages 50 images over 12.5 s, so the centreline profile here is averaged
over [t - 6.25, t + 6.25] s before the sign change is located.
  h_j = 39 mm (manifold 33 + baffle 6) + depth below the baffle face (y = 0.351 m)
Usage: lou3d_hj.py <case> [<case> ...]
"""
import glob
import os
import sys

import numpy as np

# Lou Fig. 5, read off the figure (mm); checked against the stated CFD-PIV gaps at 50 and 650 s
T_EXP = np.arange(50, 701, 50)
PIV1 = [99, 110, 123, 129, 134, 143, 160, 167, 175, 179, 181, 186, 198, np.nan]
PIV2 = [117, 119, 135, 138, 142, 152, 160, 165, 169, 175, 181, 192, 204, 211]
LOU_CFD = [74, 85, 92, 100, 108, 116, 125, 133, 142, 150, 158, 168, 176, 185]
Y_BAFFLE, OFFSET_MM = 0.351, 39.0


def profiles(case):
    """{time: (y, Uy)} from the 'axis' sets function object."""
    out = {}
    for d in glob.glob(os.path.join(case, "postProcessing", "axis", "*")):
        # raw sets write T and U together: columns y T Ux Uy Uz
        f = os.path.join(d, "centreline_T_U.xy")
        if os.path.exists(f):
            a = np.loadtxt(f)
            out[float(os.path.basename(d))] = (a[:, 0], a[:, 3])
    return dict(sorted(out.items()))


def hj_at(prof, t, half=6.25):
    ts = [s for s in prof if t - half <= s <= t + half]
    if not ts:
        return np.nan
    y = prof[ts[0]][0]
    uy = np.mean([prof[s][1] for s in ts], axis=0)
    below = y < Y_BAFFLE
    y, uy = y[below][::-1], uy[below][::-1]            # top (baffle) downwards
    for i in range(1, len(y)):
        if uy[i - 1] < 0 <= uy[i]:                       # downward flow turns upward
            yc = y[i - 1] + (y[i] - y[i - 1]) * (-uy[i - 1]) / (uy[i] - uy[i - 1])
            return OFFSET_MM + (Y_BAFFLE - yc) * 1000
    return np.nan


def main():
    piv = np.nanmean([PIV1, PIV2], axis=0)
    print(f"{'t (s)':>6} {'PIV mean':>9} {'Lou CFD':>8} " + " ".join(f"{os.path.basename(c.rstrip('/')):>10}" for c in sys.argv[1:]))
    res = {c: [] for c in sys.argv[1:]}
    profs = {c: profiles(c) for c in sys.argv[1:]}
    for k, t in enumerate(T_EXP):
        row = f"{t:6.0f} {piv[k]:9.1f} {LOU_CFD[k]:8.0f} "
        for c in sys.argv[1:]:
            h = hj_at(profs[c], t)
            res[c].append(h)
            row += f"{h:10.1f} "
        print(row)
    for c, h in res.items():
        h = np.array(h)
        ok = np.isfinite(h)
        if ok.any():
            e = h[ok] - piv[ok]
            print(f"{os.path.basename(c.rstrip('/'))}: vs PIV mean, bias {e.mean():+.1f} mm, "
                  f"RMS {np.sqrt((e ** 2).mean()):.1f} mm over {ok.sum()} times "
                  f"(Lou's own CFD: bias {np.mean(np.array(LOU_CFD)[ok] - piv[ok]):+.1f} mm)")


if __name__ == "__main__":
    main()
