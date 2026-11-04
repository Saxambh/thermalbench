# pvbatch: annotated geometry figure of the 3D Lou (2023) validation case -> JPEG
# Usage: pvbatch geometry_figure.py <viz_dir> <out.jpg>
import json
import math
import os
import sys

import numpy as np
from paraview.simple import *

V, OUTJPG = sys.argv[1], sys.argv[2]
F = os.path.join(V, "lou3d", "lou3d.foam")
W2, H = 0.097, 0.390
YB = [0.0, 0.033, 0.039, 0.351, 0.357, 0.390]
R_HOLE, R_PORT = 8.05e-3, 5e-3
EIGHTH = [(0, 0), (34.3, 0), (72.8, 0), (24.25, 24.25), (48.5, 48.5), (72.76, 72.76),
          (58.55, 24.25), (82.8, 48.5)]


def all_holes():
    pts = set()
    for x, z in EIGHTH:
        for a, b in ((x, z), (z, x)):
            for sa in (1, -1):
                for sb in (1, -1):
                    pts.add((round(sa * a, 3), round(sb * b, 3)))
    return sorted(pts)


HOLES = all_holes()
assert len(HOLES) == 37

# ---------------- 3D render ----------------
def part(regions):
    r = OpenFOAMReader(FileName=F)
    r.MeshRegions = regions
    return r


def full(src):
    return Reflect(Input=Reflect(Input=src, Plane="X Min", CopyInput=1), Plane="Z Min", CopyInput=1)


v = CreateRenderView()
v.ViewSize = [1300, 1700]
v.OrientationAxesVisibility = 0
v.Background = [1, 1, 1]
try:
    v.UseColorPaletteForBackground = 0
except AttributeError:
    pass


def show(src, color, rep="Surface", opacity=1.0, lw=1.0):
    d = Show(src, v)
    d.SetRepresentationType(rep)
    d.ColorArrayName = ["POINTS", ""]
    d.AmbientColor = d.DiffuseColor = color
    d.Opacity = opacity
    d.LineWidth = lw
    return d


walls = full(part(["patch/walls"]))
show(walls, [0.55, 0.68, 0.85], opacity=0.10)
show(walls, [0.2, 0.25, 0.35], "Feature Edges", lw=2)
show(full(part(["patch/baffle"])), [0.93, 0.62, 0.12])
show(full(part(["patch/inlet"])), [0.85, 0.15, 0.1])
show(full(part(["patch/outlet"])), [0.1, 0.3, 0.85])
q = Box(XLength=W2, YLength=H, ZLength=W2, Center=[W2 / 2, H / 2, W2 / 2])
show(q, [0.1, 0.6, 0.3], "Outline", lw=3)
v.CameraPosition = [0.50, 0.66, 0.70]
v.CameraFocalPoint = [0, 0.19, 0]
v.CameraViewUp = [0, 1, 0]
v.CameraViewAngle = 22
ResetCamera(v)
GetActiveCamera().Zoom(1.25)
Render(v)
png3d = os.path.join(V, "png", "_geom3d.png")
SaveScreenshot(png3d, v, ImageResolution=v.ViewSize)

ren = v.GetRenderer()
Wpx, Hpx = v.ViewSize


def px(p):
    ren.SetWorldPoint(p[0], p[1], p[2], 1.0)
    ren.WorldToDisplay()
    x, y, _ = ren.GetDisplayPoint()
    return x, Hpx - y            # image coordinates (origin top-left)


A = {
    "inlet": px((0, H, 0)),
    "outlet": px((0, 0, 0)),
    "up_baffle": px((W2, 0.357, -0.03)),
    "lo_baffle": px((W2, 0.039, -0.03)),
    "up_manifold": px((-W2, 0.372, W2)),
    "lo_manifold": px((-W2, 0.016, W2)),
    "storage": px((-W2, 0.20, W2)),
    "quarter": px((W2, 0.30, W2)),
    "wall": px((W2, 0.24, -W2)),
}

# ---------------- matplotlib figure ----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

RED, BLUE, ORANGE, GREEN, GREY = "#c62828", "#1f4fbf", "#e69a1f", "#1b8a4a", "#334"
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
fig = plt.figure(figsize=(26, 16), dpi=100)
fig.suptitle("ThermalStorageBench 3D validation case: Lou et al. (2023) stratified tank with perforated baffles",
             fontsize=22, fontweight="bold", y=0.985)

# (a) 3D view
axA = fig.add_axes([0.005, 0.03, 0.33, 0.91])
img = plt.imread(png3d)
axA.imshow(img)
axA.set_xlim(-420, Wpx)          # white margin on the left for the labels
axA.set_ylim(Hpx, 0)
axA.set_axis_off()
axA.set_title("(a) 3D view of the full tank (walls see-through)", fontsize=16, loc="left")


def callout(ax, key, text, dx, dy, color=GREY, ha="left"):
    x, y = A[key]
    ax.annotate(text, xy=(x, y), xytext=(x + dx, y + dy), fontsize=12.5, color=color, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6),
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, lw=1.2, alpha=0.95))


callout(axA, "inlet", "INLET  Ø10 mm, top centre\nhot water 60 °C, 1 L/min", 120, -110, RED)
callout(axA, "up_baffle", "Upper perforated baffle\n6 mm thick, 37 holes", 70, -60, "#a5650a")
callout(axA, "lo_baffle", "Lower perforated baffle\n(same as upper)", 60, 60, "#a5650a")
callout(axA, "outlet", "OUTLET  Ø10 mm, bottom centre", 90, 90, BLUE)
callout(axA, "up_manifold", "Upper manifold\n(33 mm gap)", -40, -120, GREY, "right")
callout(axA, "storage", "Storage region\n312 mm tall\nstarts full of 20 °C water", -40, 0, GREY, "right")
callout(axA, "lo_manifold", "Lower manifold (33 mm)", -40, 90, GREY, "right")
callout(axA, "quarter", "Green box = the quarter\nactually simulated\n(rest is mirror image)", 90, 40, GREEN)

# (b) side section, to scale (cut through the tank centre)
axB = fig.add_axes([0.37, 0.06, 0.25, 0.86])
mm = lambda v_: v_ * 1000
axB.add_patch(Rectangle((-97, 0), 194, 390, fc="#dbe9f7", ec="k", lw=2.5))
for (y0, y1) in ((33, 39), (351, 357)):
    gaps = sorted(xc for xc, zc in HOLES if abs(zc) < R_HOLE * 1000)
    edges = [-97] + sum([[g - 8.05, g + 8.05] for g in gaps], []) + [97]
    for a_, b_ in zip(edges[::2], edges[1::2]):
        axB.add_patch(Rectangle((a_, y0), b_ - a_, y1 - y0, fc=ORANGE, ec="#8a5a0a", lw=1))
# ports
axB.add_patch(Rectangle((-5, 390), 10, 22, fc=RED, ec="k"))
axB.add_patch(Rectangle((-5, -22), 10, 22, fc=BLUE, ec="k"))
axB.annotate("", xy=(0, 386), xytext=(0, 432), arrowprops=dict(arrowstyle="-|>", color=RED, lw=3))
axB.annotate("", xy=(0, -44), xytext=(0, -4), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=3))
axB.text(9, 425, "inlet 60 °C\n0.21 m/s", color=RED, fontsize=12, va="center")
axB.text(9, -36, "outlet", color=BLUE, fontsize=12, va="center")
# jet + h_j
axB.add_patch(FancyArrowPatch((0, 388), (0, 278), arrowstyle="-|>", mutation_scale=25, color=RED, lw=4, alpha=0.75))
axB.annotate("", xy=(-45, 390), xytext=(-45, 276), arrowprops=dict(arrowstyle="<->", color="k", lw=1.6,
                                                                      shrinkA=0, shrinkB=0))
axB.plot([-50, 0], [276, 276], "k--", lw=1)
axB.text(-106, 300, "jet penetration\ndepth  h_j\n(measured from\nthe lid; compared\nwith PIV)", ha="right",
         va="center", fontsize=12)
axB.annotate("", xy=(-47, 330), xytext=(-104, 305), arrowprops=dict(arrowstyle="-", color="0.4", lw=1))
# dimensions on the right
xd = 112
for y0, y1, lab, yt in ((0, 33, "33 mm  lower manifold", 14), (33, 39, "6 mm  baffle", 46),
                        (39, 351, "312 mm  storage region", 195),
                        (351, 357, "6 mm  baffle", 344), (357, 390, "33 mm  upper manifold", 376)):
    axB.annotate("", xy=(xd, y0), xytext=(xd, y1), arrowprops=dict(arrowstyle="<->", lw=1.2, shrinkA=0, shrinkB=0))
    axB.plot([97, xd + 3], [y0, y0], color="0.6", lw=0.6)
    axB.text(xd + 6, yt, lab, va="center", fontsize=11.5)
axB.plot([97, xd + 3], [390, 390], color="0.6", lw=0.6)
axB.annotate("", xy=(-97, -60), xytext=(97, -60), arrowprops=dict(arrowstyle="<->", lw=1.4))
axB.text(0, -70, "194 mm (inside width)", ha="center", va="top", fontsize=12)
axB.text(-104, 140, "390 mm inside height", rotation=90, ha="right", va="center", fontsize=12)
axB.axvline(0, color=GREEN, ls=(0, (6, 4)), lw=1.6, ymin=0.08, ymax=0.9)
axB.text(3, 200, "symmetry\nplane", color=GREEN, fontsize=11, va="center")
axB.text(0, 160, "holes cut by this section\nshow as gaps in the baffles", ha="center", fontsize=10.5, color="#8a5a0a",
         bbox=dict(fc="white", ec="none", alpha=0.7))
axB.set_xlim(-215, 230)
axB.set_ylim(-95, 450)
axB.set_aspect("equal")
axB.set_axis_off()
axB.set_title("(b) Side section through the centre, to scale (mm)", fontsize=16, loc="left")

# (c) baffle top view
axC = fig.add_axes([0.675, 0.47, 0.31, 0.46])
axC.add_patch(Rectangle((-97, -97), 194, 194, fc=ORANGE, ec="k", lw=2))
axC.add_patch(Rectangle((0, 0), 97, 97, fc="none", ec=GREEN, lw=3.5, hatch="//", alpha=0.6))
for xc, zc in HOLES:
    axC.add_patch(Circle((xc, zc), 8.05, fc="white", ec="#8a5a0a", lw=1))
axC.add_patch(Circle((0, 0), 5, fc="none", ec=RED, lw=2, ls="--"))
axC.axhline(0, color=GREEN, ls=(0, (6, 4)), lw=1.5)
axC.axvline(0, color=GREEN, ls=(0, (6, 4)), lw=1.5)
axC.text(100, 50, "simulated\nquarter", color=GREEN, fontsize=12.5, va="center", fontweight="bold")
axC.text(100, -50, "37 holes, Ø16.1 mm\nopen area 20 %\n(red dashed: inlet\nport above, Ø10 mm)", fontsize=12, va="center")
axC.set_xlim(-105, 175)
axC.set_ylim(-105, 105)
axC.set_aspect("equal")
axC.set_xlabel("x (mm)")
axC.set_ylabel("z (mm)")
axC.set_title("(c) Each baffle seen from above", fontsize=16, loc="left")

# (d) model summary
axD = fig.add_axes([0.655, 0.03, 0.33, 0.40])
axD.set_axis_off()
axD.set_title("(d) What is simulated", fontsize=16, loc="left")
txt = (
    "Experiment: Lou et al. 2023, J. Energy Storage 71:108017\n"
    "  Tank starts at 20 °C; 60 °C water enters at the top for 750 s.\n"
    "  The hot jet falls through the upper baffle; PIV measured how\n"
    "  deep it reaches (h_j) every 50 s.\n\n"
    "Why a quarter: the tank is symmetric about two vertical planes,\n"
    "  so only one quarter is meshed (symmetry boundaries on the cuts).\n\n"
    "Mesh (230k cells): 3.2 mm in the bulk, 1.6 mm around the upper\n"
    "  baffle and the jet column, 0.8 mm at the two ports. Holes are\n"
    "  built from cells (stepped edges), sized so the open area is\n"
    "  exactly 20 %. Second run (lab PC, 327k): lower baffle at 1.6 mm.\n\n"
    "Boundaries: inlet 0.2126 m/s at 60 °C (= 1 L/min);\n"
    "  outlet fixed pressure; walls and baffles no-slip, no heat loss.\n\n"
    "Physics: real water properties, buoyantPimpleFoam (OpenFOAM v2606),\n"
    "  k-omega SST turbulence with the correctly signed buoyancy term."
)
axD.text(0.0, 0.97, txt, va="top", ha="left", fontsize=13.2, family="DejaVu Sans", linespacing=1.35,
         transform=axD.transAxes)

fig.savefig(OUTJPG, dpi=100, pil_kwargs={"quality": 92})
print("wrote", OUTJPG, json.dumps({k: [round(a, 1), round(b, 1)] for k, (a, b) in A.items()}))
