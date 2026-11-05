"""Interpolation baselines in parameter space (added 2026-11-04 after the novelty check: Yavuz 2026,
SSRN 10.2139/ssrn.7044626, argues neural-operator claims need a direct interpolation baseline).

A prediction is a weighted sum of whole training fields at the matching normalised time; only the
weights differ between methods. X are the standardised parameter vectors of the training runs
(tank 13, PCM 12 parameters).
  nn   nearest neighbour (k = 1)
  idw  inverse-distance weighting, w ~ 1/d^2 over the k = 8 nearest runs
  rbf  thin-plate-spline radial basis function interpolation with a linear polynomial tail
       (scipy RBFInterpolator) over the k = 40 nearest runs: the weights are its cardinal
       functions at the query, computed in the principal directions the neighbours span (constant
       or linearly dependent parameters carry no extra information and would make the polynomial
       part singular). Weights can be negative and, outside the training data, extrapolate: that
       is the method, not a bug.
Delaunay (barycentric) interpolation, used with 3 parameters by Yavuz, is not offered: in 12-13
dimensions the triangulation is impractical, and it is undefined outside the convex hull of the
training runs, which is where the out-of-distribution test runs lie.
"""
import warnings

import numpy as np

FALLBACKS = 0      # rbf queries that had to use the nearest run (should stay 0)


def weights(X, q, method, k=None):
    """(indices, weights) of the training runs that make the prediction for query q."""
    d = np.linalg.norm(X - q, axis=1)
    order = np.argsort(d)
    if method == "nn":
        return order[:1], np.ones(1)
    if method == "idw":
        near = order[: k or 8]
        if d[near[0]] < 1e-12:
            return near[:1], np.ones(1)
        w = 1.0 / d[near] ** 2
        return near, w / w.sum()
    if method == "rbf":
        # Fixed 2026-11-05: parameters that are exact linear combinations of others (PCM: Pr and Ste
        # follow from material and superheat; some tank neighbourhoods likewise) made the linear tail
        # singular, and the old code then fell back to the nearest run without saying so (every PCM
        # test run, 3-8 % of tank test runs). The neighbours are now expressed in the principal
        # directions they actually span (an isometry on the neighbours; the query keeps its
        # component in that subspace). Any remaining fallback is counted in FALLBACKS and warned.
        global FALLBACKS
        from scipy.interpolate import RBFInterpolator
        near = order[: min(k or 40, len(X))]
        P = X[near]
        c = P.mean(0)
        _, s, vt = np.linalg.svd(P - c, full_matrices=False)
        r = int((s > 1e-6 * s[0]).sum()) if s.size and s[0] > 0 else 0
        if r == 0 or len(near) <= r + 1:
            FALLBACKS += 1
            warnings.warn("rbf: neighbourhood spans too few directions, nearest run used")
            return near[:1], np.ones(1)
        Z, zq = (P - c) @ vt[:r].T, (q - c) @ vt[:r].T
        try:
            f = RBFInterpolator(Z, np.eye(len(near)), kernel="thin_plate_spline", degree=1, smoothing=1e-8)
            w = f(zq[None, :])[0]
        except np.linalg.LinAlgError:
            FALLBACKS += 1
            warnings.warn("rbf: degenerate neighbourhood, nearest run used")
            return near[:1], np.ones(1)
        return near, w
    raise ValueError(method)
