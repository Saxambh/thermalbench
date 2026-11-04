"""Interpolation baselines in parameter space (added 2026-11-04 after the novelty check: Yavuz 2026,
SSRN 10.2139/ssrn.7044626, argues neural-operator claims need a direct interpolation baseline).

A prediction is a weighted sum of whole training fields at the matching normalised time; only the
weights differ between methods. X are the standardised parameter vectors of the training runs
(tank 13, PCM 12 parameters).
  nn   nearest neighbour (k = 1)
  idw  inverse-distance weighting, w ~ 1/d^2 over the k = 8 nearest runs
  rbf  thin-plate-spline radial basis function interpolation with a linear polynomial tail
       (scipy RBFInterpolator) over the k = 40 nearest runs: the weights are its cardinal
       functions at the query. Parameters constant among those runs are dropped (no information,
       and they would make the polynomial part singular). Weights can be negative and, outside
       the training data, extrapolate: that is the method, not a bug.
Delaunay (barycentric) interpolation, used with 3 parameters by Yavuz, is not offered: in 12-13
dimensions the triangulation is impractical, and it is undefined outside the convex hull of the
training runs, which is where the out-of-distribution test runs lie.
"""
import numpy as np


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
        from scipy.interpolate import RBFInterpolator
        near = order[: min(k or 40, len(X))]
        P = X[near]
        keep = P.std(0) > 1e-9
        if keep.sum() == 0 or len(near) <= keep.sum() + 1:
            return near[:1], np.ones(1)
        P, qq = P[:, keep], q[keep]
        try:
            f = RBFInterpolator(P, np.eye(len(near)), kernel="thin_plate_spline", degree=1, smoothing=1e-8)
            w = f(qq[None, :])[0]
        except np.linalg.LinAlgError:          # degenerate neighbourhood: fall back to the nearest run
            return near[:1], np.ones(1)
        return near, w
    raise ValueError(method)
