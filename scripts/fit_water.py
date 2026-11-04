#!/usr/bin/env python3
"""Fit polynomial water properties in T [K] for OpenFOAM (icoPolynomial, hPolynomial,
polynomial transport), 10 to 80 C at 1 atm. Reference values: IAPWS-95 / IAPWS 2008
viscosity / IAPWS 2011 conductivity, as tabulated in standard property tables."""
import numpy as np

TC = np.array([10, 20, 30, 40, 50, 60, 70, 80], float)
rho = np.array([999.70, 998.21, 995.65, 992.22, 988.03, 983.20, 977.76, 971.79])
mu = np.array([1.3059, 1.0016, 0.7972, 0.6527, 0.5465, 0.4660, 0.4035, 0.3540]) * 1e-3
cp = np.array([4192, 4184, 4180, 4179, 4181, 4185, 4190, 4196], float)
kap = np.array([0.5800, 0.5984, 0.6154, 0.6305, 0.6435, 0.6543, 0.6631, 0.6700])
TK = TC + 273.15


def fit(y, deg, name):
    # Fit in centred variable for conditioning, then expand to powers of T [K].
    x0 = 318.15
    c = np.polyfit(TK - x0, y, deg)                  # highest power first
    p = np.poly1d(c)
    q = p(np.poly1d([1.0, -x0]))                     # substitute (T - x0)
    coeffs = q.coeffs[::-1]                          # a0 + a1 T + a2 T^2 ...
    err = np.max(np.abs(np.polyval(coeffs[::-1], TK) - y) / np.abs(y)) * 100
    out = list(coeffs) + [0.0] * (8 - len(coeffs))
    print(f"// {name}: degree {deg}, max rel. error {err:.3f} % over 10-80 C")
    return "(" + " ".join(f"{v:.10e}" for v in out) + ")"


print("rhoCoeffs<8>", fit(rho, 3, "rho") + ";")
print("CpCoeffs<8>", fit(cp, 3, "Cp") + ";")
print("muCoeffs<8>", fit(mu, 4, "mu") + ";")
print("kappaCoeffs<8>", fit(kap, 3, "kappa") + ";")
# Thermal expansion coefficient for reference
beta = -np.gradient(rho, TK) / rho
print("// beta [1/K] at", list(TC.astype(int)), [f"{b:.2e}" for b in beta])
