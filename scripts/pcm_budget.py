"""Melting-time and cost estimate for PCM cases (budgeting only).

Energy to melt a W x H slab, delivered by laminar natural convection on the heated wall:
    t_melt = rho W (L + cp (Tm - T0) + cp (Tw - Tm)/2) / (c k (Tw - Tm) / H * Ra_H^0.25)
             * (1 + N)^-0.5 (fins, Kamkari correlation exponent) * f_tilt (0.62 at 45, 0.46 at 90)
c is calibrated on our two validated runs: Vogel (octadecane, one side of the symmetric 50 mm
box, 10 K) and Kamkari plain (lauric, 50 x 120 mm, 26.5 K).
Cost: wall seconds per simulated second, measured on the lab Kamkari runs (24k cells, 0.5 mm,
busy machine), scaled with cell count and with 1/maxDeltaT if the step is at its cap.
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_pcm_case import props

G = 9.81


def t_est(mat, sh, sub, W, H, N=0, tilt=0, c=1.0, tmelt_C=None):
    """sh = Tw - Tm, sub = Tm - T0, with Tm the model's reference melting temperature
    (tmelt_C, e.g. the midpoint of a melting range; default the material's Tmelt)."""
    Tm = props(mat, 300.0, tmelt_C)["Tmelt_K"]
    p = props(mat, Tm + sh, tmelt_C)
    nu, a = p["mu"] / p["rho"], p["k"] / (p["rho"] * p["cp"])
    Ra = G * p["beta"] * sh * H ** 3 / (nu * a)
    E = p["rho"] * W * (p["L"] + p["cp"] * (sub + sh / 2))
    q = c * p["k"] * sh / H * Ra ** 0.25
    f_tilt = {0: 1.0, 45: 0.62, 90: 0.46}[tilt]
    return E / q * (1 + N) ** -0.5 * f_tilt, Ra


# calibration: measured t(0.99) of our runs
# (lauric relative to the range midpoint 45.85 C, as in the design: Tw 70 C, T0 25 C)
cal = [("octadecane", 10.0, 1.0, 0.025, 0.1, 3.3 * 3600, None),    # Vogel V1 (f 0.97 at 3 h, 1.0 at 3.5 h)
       ("lauric", 24.15, 20.85, 0.05, 0.12, 180 * 60, 45.85)]     # Kamkari plain, experiment ~185, range ~180
cs = [t_est(m, sh, sub, W, H, tmelt_C=tm)[0] / t for m, sh, sub, W, H, t, tm in cal]
print("calibration c:", " ".join(f"{c:.3f}" for c in cs))
C = math.exp(sum(math.log(c) for c in cs) / len(cs))
# check against the other validated cases
for name, args, t in [("Kamkari 1 fin", ("lauric", 24.15, 20.85, 0.05, 0.12, 1, 0), 155 * 60),
                      ("Kamkari 3 fins", ("lauric", 24.15, 20.85, 0.05, 0.12, 3, 0), 125 * 60),
                      ("Kamkari 45", ("lauric", 24.15, 20.85, 0.05, 0.12, 0, 45), 122 * 60),
                      ("Kamkari 90", ("lauric", 24.15, 20.85, 0.05, 0.12, 0, 90), 92 * 60)]:
    print(f"check {name}: estimate {t_est(*args, c=C, tmelt_C=45.85)[0] / 60:.0f} min vs {t / 60:.0f}")

WALL_PER_SIM = 5.8 / 24000      # s wall per simulated s per cell (lab, 0.5 mm, maxDeltaT 0.1)


def cost(mat, sh, sub, W, H=0.1, N=0, tilt=0, h=0.0005, maxdt=0.1):
    t, Ra = t_est(mat, sh, sub, W, H, N, tilt, C)
    cells = (W / h) * (H / h)
    hrs = t * cells * WALL_PER_SIM * (0.1 / maxdt) / 3600
    return t, Ra, cells, hrs


if __name__ == "__main__":
    print(f"\nH = 100 mm, 0.5 mm mesh, maxDeltaT 0.1 s (core-hours at the lab's measured speed)")
    print(f"{'material':10s} {'SH':>4s} {'sub':>4s} {'W mm':>5s} {'N':>2s} {'tilt':>4s} {'Ra':>8s} {'t_melt h':>8s} {'core-h':>7s}")
    for mat in ("octadecane", "lauric"):
        for sh, sub, W, N, tilt in [(5, 20, 0.1, 0, 0), (5, 0.5, 0.1, 0, 0), (5, 0.5, 0.02, 0, 0),
                                    (17.5, 10, 0.06, 0, 0), (30, 20, 0.1, 0, 0), (30, 0.5, 0.02, 0, 0),
                                    (5, 20, 0.1, 5, 0), (30, 0.5, 0.02, 5, 90)]:
            t, Ra, cells, hrs = cost(mat, sh, sub, W, N=N, tilt=tilt)
            print(f"{mat:10s} {sh:4g} {sub:4g} {W * 1000:5.0f} {N:2d} {tilt:4d} {Ra:8.2e} {t / 3600:8.1f} {hrs:7.0f}")
