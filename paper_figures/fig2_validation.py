"""Fig. 2: validation against experiments.
(a) Lou et al. 2023 jet penetration h_j(t): two PIV tests, their Fluent CFD, our 3D SST run
    (validation_Lou2023_case_data.md, tables "Measurement" and "Result").
(b) Lou et al. 2023 outlet temperature T*(t*): our run (verification_data/lou_outlet_2026-11-07/ours_outletT_*.dat)
    and the experiment reconstructed from Fig. 15a Ri_bulk with constant beta and with beta at the mean of
    inlet and outlet temperature (same equations as compare.py and beta_sens.py).
(c) Kamkari & Shokouhmand 2014 liquid fraction at 70 C, plain wall, 1 and 3 fins: experiment (Fig. 6) and
    the model at the frozen dataset settings (validation_Kamkari2014_fins.md, "Final comparison").
(d) Vogel & Thess 2019: liquid fraction, experiment (Fig. 11), their 2D model B-2D (Fig. 7) and our run
    with the final solver set-up (validation_Vogel2019_pcm.md).
"""
import glob, json, os
import numpy as np
from scipy.optimize import brentq
from matplotlib.lines import Line2D
from style import plt, ARCH, INK, INK2, GRID, MM, ROOT, save

LOU = os.path.join(ROOT, "verification_data", "lou_outlet_2026-11-07")
OURS = ARCH["fno"]          # our CFD in blue throughout
EXP, OTHER = INK, ARCH["base"]

# (a) data, from validation_Lou2023_case_data.md
t_hj = np.arange(50, 701, 50)
piv1 = [99, 110, 123, 129, 134, 143, 160, 167, 175, 179, 181, 186, 198, np.nan]
piv2 = [117, 119, 135, 138, 142, 152, 160, 165, 169, 175, 181, 192, 204, 211]
lou_cfd = [74, 85, 92, 100, 108, 116, 125, 133, 142, 150, 158, 168, 176, 185]
ours_hj = [105.8, 113.7, 120.5, 128.5, 138.1, 146.3, 156.1, 165.5, 173.8, 183.7, 193.1, 202.0, 211.5, 222.5]

# (b) data
T_REF, TC, TH = 14.1e-3 / (1.0e-3 / 60), 293.15, 333.15
d = json.load(open(os.path.join(LOU, "fig15_333K_initial.json")))
ri = np.array(d["Ri"])
ri0 = ri[(ri[:, 0] >= 0.2) & (ri[:, 0] <= 0.6), 1].mean()
lou_t, lou_const = ri[:, 0], 1 - ri[:, 1] / ri0
Tc_, Td = np.array([20, 25, 30, 35, 40, 45, 50, 55, 60.]), np.array([2.07, 2.57, 3.03, 3.45, 3.85, 4.22, 4.58, 4.91, 5.23])
beta = lambda T: np.interp(T, Tc_, Td)


def tstar_beta_mean(ratio):
    g = lambda To: beta((60 + To) / 2) * (60 - To) / (beta((60 + 20) / 2) * 40) - ratio   # as beta_sens.py: f(20)
    To = brentq(g, 19.99, 60) if g(19.99) * g(60) < 0 else 20
    return (To - 20) / 40


lou_bmean = np.array([tstar_beta_mean(1 - T) for T in lou_const])
o = np.vstack([np.loadtxt(f, comments="#") for f in sorted(glob.glob(os.path.join(LOU, "ours_outletT_*.dat")))])
o = o[np.argsort(o[:, 0])]
o_t, o_T = o[:, 0] / T_REF, (o[:, 1] - TC) / (TH - TC)

# (c) Kamkari, frozen settings
tk = np.array([10, 20, 30, 40, 50, 60, 80, 100, 120, 140, 160])
KAM = {"plain wall": ([0.06, 0.12, 0.18, 0.25, 0.32, 0.40, 0.55, 0.68, 0.80, 0.89, 0.95],
                      [0.09, 0.15, 0.22, 0.30, 0.37, 0.44, 0.58, 0.69, 0.79, 0.87, 0.93]),
       "1 fin": ([0.09, 0.18, 0.27, 0.35, 0.45, 0.56, 0.73, 0.83, 0.89, 0.95, 1.0],
                 [0.14, 0.25, 0.36, 0.47, 0.57, 0.67, 0.77, 0.85, 0.91, 0.96, np.nan]),
       "3 fins": ([0.17, 0.35, 0.49, 0.61, 0.71, 0.79, 0.91, 0.97, 1.0, np.nan, np.nan],
                  [0.24, 0.43, 0.60, 0.71, 0.81, 0.86, 0.93, 0.97, np.nan, np.nan, np.nan])}

# (d) Vogel
tv_exp = np.array([0.167, 0.333, 0.5, 0.667, 0.833, 1.0, 1.167, 1.333, 1.5, 1.667, 1.833, 2.0, 2.167, 2.333, 2.5, 2.667, 2.833, 3.0, 3.167])
fv_exp = [0.03, 0.155, 0.25, 0.34, 0.425, 0.505, 0.58, 0.65, 0.71, 0.765, 0.81, 0.85, 0.885, 0.91, 0.94, 0.96, 0.975, 0.985, 0.99]
tv = [0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
fv_b2d = [0.16, 0.27, 0.47, 0.66, 0.80, 0.90, 0.965]
fv_ours = [0.154, 0.259, 0.475, 0.665, 0.814, 0.915, 0.974]

fig, ax = plt.subplots(2, 2, figsize=(190 * MM, 130 * MM))
a = ax[0, 0]
a.plot(t_hj, piv1, "o", ms=3.5, mfc="white", mec=EXP, mew=0.9, ls="", label="PIV, test 1")
a.plot(t_hj, piv2, "s", ms=3.2, mfc="white", mec=EXP, mew=0.9, ls="", label="PIV, test 2")
a.plot(t_hj, lou_cfd, color=OTHER, lw=1.4, ls=(0, (4, 2)), label="Lou et al. CFD")
a.plot(t_hj, ours_hj, color=OURS, lw=1.8, label="this work, 3D SST")
a.set_xlabel("Time (s)"); a.set_ylabel("Jet penetration h$_j$ (mm)")
a.set_title("(a) Tank jet, Lou et al. (2023)", loc="left"); a.legend(fontsize=6.5, loc="lower right")

a = ax[0, 1]
a.plot(lou_t, lou_const, "o", ms=2.2, color=EXP, ls="", label="experiment, constant β")
a.plot(lou_t, lou_bmean, "o", ms=2.2, mfc="white", mec=EXP, mew=0.6, ls="", label="experiment, β at mean T")
a.plot(o_t, o_T, color=OURS, lw=1.8, label="this work, 3D SST")
a.set_xlim(0.4, 1.55); a.set_ylim(-0.03, 1.02)
a.set_xlabel("Dimensionless time t* = t Q / V"); a.set_ylabel("Outlet temperature T*")
a.set_title("(b) Tank outlet, Lou et al. (2023)", loc="left"); a.legend(fontsize=6.5, loc="upper left")

a = ax[1, 0]
hk = []
for (lab, (e, m)), ls, mk in zip(KAM.items(), ("-", (0, (4, 2)), (0, (1, 1.5))), ("o", "s", "^")):
    a.plot(tk, e, mk, ms=3.4, mfc="white", mec=EXP, mew=0.9, ls="")
    a.plot(tk, m, color=OURS, lw=1.6, ls=ls)
    hk.append(Line2D([], [], color=OURS, lw=1.6, ls=ls, marker=mk, mfc="white", mec=EXP, ms=3.6, label=lab))
a.set_xlabel("Time (min)"); a.set_ylabel("Liquid fraction")
a.set_xlim(0, 180); a.set_ylim(0, 1.05)
a.set_title("(c) PCM with fins, Kamkari & Shokouhmand (2014)", loc="left")
a.legend(handles=hk, fontsize=6.5, loc="lower right", title="markers: experiment, lines: this work", title_fontsize=6.5)

a = ax[1, 1]
a.plot(tv_exp, fv_exp, "o", ms=3.2, mfc="white", mec=EXP, mew=0.9, ls="", label="experiment")
a.plot(tv, fv_b2d, color=OTHER, lw=1.4, ls=(0, (4, 2)), label="Vogel & Thess 2D model")
a.plot(tv, fv_ours, color=OURS, lw=1.8, label="this work")
a.set_xlabel("Time (h)"); a.set_ylabel("Liquid fraction"); a.set_ylim(0, 1.05)
a.set_title("(d) PCM plain wall, Vogel & Thess (2019)", loc="left"); a.legend(fontsize=6.5, loc="lower right")
for a in ax.flat:
    a.grid(color=GRID, lw=0.5); a.set_axisbelow(True)
fig.tight_layout(h_pad=2.0, w_pad=2.5)
save(fig, "fig2_validation")
