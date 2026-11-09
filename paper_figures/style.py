"""Shared style for the paper figures (ThermalStorageBench, Journal of Energy Storage).

Architecture colours: dataviz default categorical slots 1 to 3 in fixed order, validated on the light
surface (validate_palette.js, 9 November 2026: all checks pass; aqua is 2.74:1 against the surface, so every
series is also direct-labelled or carries a marker shape). Baselines are neutral grey.
Plain variants use filled markers and hybrid variants hollow ones, so variant identity never relies on
colour alone. Journal sizes: single column 90 mm, double column 190 mm. Vector PDF and 600 dpi PNG.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
ARCH = {"fno": "#2a78d6", "unet": "#eb6834", "transolver": "#1baf7a", "base": "#8a8984"}
NAME = {"fno": "FNO", "unet": "U-Net", "transolver": "Transolver"}
MM = 1 / 25.4
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "figure.facecolor": SURF, "axes.facecolor": SURF,
    "savefig.facecolor": SURF, "pdf.fonttype": 42, "legend.frameon": False})
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ML = os.path.join(ROOT, "thermbench_ml")
OUT = os.path.join(HERE, "out")


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=600, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.join(OUT, name + ".png"))
