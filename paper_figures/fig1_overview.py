"""Fig. 1: overview of ThermalStorageBench. (a) Tank family: 2D tank, height 1 m, width W; port type A (side-wall
slots) and type B (lid and bottom slots), slot height s, port offset; charging shown (hot in at the top,
out at the bottom; discharging reverses the flow and the temperatures). (b) PCM family: 2D cell, height
100 mm, width W, heated wall with 0 to 5 conducting fins; side heating, 45 degree tilt, heated from below.
(c) The out-of-distribution splits: what each one holds out of training.
Geometry ranges from the dataset cards (DATASET_CARD_tank_draft.md, DATASET_CARD_pcm_draft.md); splits from
splits.py and pcm_splits.py. Schematic, not to scale."""
import numpy as np
from matplotlib.patches import Rectangle, FancyArrowPatch, Polygon
from style import plt, ARCH, INK, INK2, GRID, MM, save

HOT, COLD, WALL = "#c8423a", "#2f6db3", INK2
fig = plt.figure(figsize=(190 * MM, 88 * MM))
ax1 = fig.add_axes([0.0, 0.05, 0.30, 0.88]); ax2 = fig.add_axes([0.30, 0.05, 0.30, 0.88]); ax3 = fig.add_axes([0.61, 0.05, 0.39, 0.88])
for a in (ax1, ax2, ax3):
    a.set_axis_off(); a.set_aspect("equal")


def arrow(a, x0, y0, x1, y1, col):
    a.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=7, color=col, lw=1.1))


# (a) tank, two port types side by side
for x0, typ in ((0.15, "A"), (1.25, "B")):
    W, H = 0.8, 1.6
    a = ax1
    a.add_patch(Rectangle((x0, 0.2), W, H, fill=False, ec=WALL, lw=1.2))
    a.add_patch(Rectangle((x0, 0.2 + 0.55 * H), W, 0.45 * H, color=HOT, alpha=0.25, lw=0))
    a.add_patch(Rectangle((x0, 0.2), W, 0.55 * H, color=COLD, alpha=0.18, lw=0))
    if typ == "A":
        arrow(a, x0 - 0.22, 0.2 + 0.85 * H, x0 + 0.02, 0.2 + 0.85 * H, HOT)
        arrow(a, x0 + W - 0.02, 0.2 + 0.15 * H, x0 + W + 0.22, 0.2 + 0.15 * H, COLD)
        a.text(x0 + W / 2, 0.05, "type A: side-wall slots", ha="center", fontsize=6.3, color=INK)
    else:
        arrow(a, x0 + 0.2, 0.2 + H + 0.25, x0 + 0.2, 0.2 + H - 0.02, HOT)
        arrow(a, x0 + W - 0.2, 0.22, x0 + W - 0.2, -0.03, COLD)
        a.text(x0 + W / 2, -0.17, "type B: lid and bottom slots", ha="center", fontsize=6.3, color=INK)
a.annotate("", (0.15, 1.9), (0.95, 1.9), arrowprops=dict(arrowstyle="<->", color=INK2, lw=0.7))
a.text(0.55, 1.93, "W 0.25 to 1.0 m", ha="center", va="bottom", fontsize=6.3, color=INK2)
a.annotate("", (2.2, 0.2), (2.2, 1.8), arrowprops=dict(arrowstyle="<->", color=INK2, lw=0.7))
a.text(2.25, 1.0, "H = 1 m", va="center", fontsize=6.3, color=INK2, rotation=90)
a.text(0.0, 2.45, "(a) Stratified water tank (sensible)", fontsize=8, color=INK)
a.text(0.0, 2.27, "1,212 runs; real water properties;", fontsize=6.3, color=INK2)
a.text(0.0, 2.13, "laminar and k-ω SST", fontsize=6.3, color=INK2)
a.set_xlim(-0.1, 2.5); a.set_ylim(-0.3, 2.6)

# (b) PCM cell with fins, and the three orientations
a = ax2
x0, W, H = 0.3, 0.6, 1.6
a.add_patch(Rectangle((x0, 0.2), W, H, fill=False, ec=WALL, lw=1.2))
melt = Polygon([[x0, 0.2], [x0, 0.2 + H], [x0 + 0.45, 0.2 + H], [x0 + 0.2, 0.2 + 0.2]], color=HOT, alpha=0.25, lw=0)
a.add_patch(melt)
a.add_patch(Rectangle((x0, 0.2), W, H, color=COLD, alpha=0.12, lw=0))
a.plot([x0, x0], [0.2, 0.2 + H], color=HOT, lw=3)
for y in (0.6, 1.0, 1.4):
    a.plot([x0, x0 + 0.25], [y, y], color=INK2, lw=1.6)
a.text(x0 - 0.06, 1.0, "heated wall", rotation=90, va="center", ha="right", fontsize=6.3, color=HOT)
a.text(x0 + 0.27, 1.0, "fin", fontsize=6, color=INK2, va="bottom")
a.text(x0 + W / 2, 0.05, "0 to 5 conducting fins", ha="center", fontsize=6.3, color=INK)
a.annotate("", (x0, 1.9), (x0 + W, 1.9), arrowprops=dict(arrowstyle="<->", color=INK2, lw=0.7))
a.text(x0 + W / 2, 1.93, "W 20 to 60 mm", ha="center", va="bottom", fontsize=6.3, color=INK2)
# orientation icons
for i, (ang, lab) in enumerate(((0, "side heating"), (45, "tilted 45°"), (90, "heated from below"))):
    cx, cy = 1.3, 1.45 - 0.55 * i
    w, h = 0.16, 0.36
    pts = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]])
    th = np.deg2rad(ang); R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    p = pts @ R.T + [cx, cy]
    a.add_patch(Polygon(p, fill=False, ec=WALL, lw=1.0))
    a.plot([p[0, 0], p[3, 0]], [p[0, 1], p[3, 1]], color=HOT, lw=2.2)
    a.text(cx + 0.26, cy, lab.replace("heated from below", "heated from\nbelow"), va="center", fontsize=6.3, color=INK)
a.text(0.0, 2.45, "(b) PCM melting cell (latent)", fontsize=8, color=INK)
a.text(0.0, 2.27, "500 runs; n-octadecane", fontsize=6.3, color=INK2)
a.text(0.0, 2.13, "and lauric acid", fontsize=6.3, color=INK2)
a.set_xlim(-0.1, 2.6); a.set_ylim(-0.3, 2.6)

# (c) splits
a = ax3; a.set_aspect("auto"); a.set_xlim(0, 1); a.set_ylim(0, 1)
a.text(0.0, 0.965, "(c) Test splits: what is held out of training", fontsize=8, color=INK)
rows = [("Tank", None), ("random", "10 % of design points"), ("unseen width", "W outside 0.33 to 0.93 m"),
        ("discharge", "all discharging runs (trained on charging)"), ("faster inflow", "Re above the design 90th percentile (SST)"),
        ("PCM", None), ("random", "10 % of cases"), ("held-out fins", "4 and 5 fins (trained on 0 to 3)"),
        ("stronger heating", "superheat above the 90th percentile"), ("unseen tilt", "45° and heated from below"),
        ("material transfer", "lauric acid, trained on n-octadecane"), ("(reverse)", "n-octadecane, trained on lauric acid")]
y = 0.88
for k, v in rows:
    if v is None:
        y -= 0.015
        a.text(0.0, y, k, fontsize=7, color=INK, weight="bold"); y -= 0.07
        continue
    a.text(0.03, y, k, fontsize=6.4, color=INK)
    a.text(0.36, y, v, fontsize=6.4, color=INK2)
    y -= 0.068
a.text(0.0, 0.0, "Splits are by design point; laminar and SST twins never straddle train and test.", fontsize=6, color=INK2)
save(fig, "fig1_overview")
