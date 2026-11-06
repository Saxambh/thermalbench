"""ThermalStorageBench scoring. All functions take predicted and true temperature fields in theta form
(theta = (T - Tc)/(Th - Tc)), shape [n, ny, nx] on the run's native grid (unpadded).

Headline metrics, averaged over the scored snapshots of each test run, then over runs:
  rmse_theta   field RMS error in theta
  rmse_K       the same in kelvin (theta error times the run's Th - Tc)
  y_mid_err_m  error in thermocline height (row-averaged profile crosses theta = 0.5)
  energy_err   error in stored energy as a fraction of the tank's full capacity
               (|mean theta pred - mean theta true|, constant rho*cp; 0.01 = 1 % of a
               full charge). Not divided by the current stored energy, which goes to ~0
               at the end of a discharge. The CFD's real-property energy is in the h5 metrics
  profile_rmse RMS error of the row-averaged (1D) profile in theta: what a 1D tank
               model would be judged on
  T_out_err_K  error in outlet temperature (mean of the cells next to the outlet port),
               in kelvin: what a system simulation takes from the tank
  r2_field     coefficient of determination of the theta field within the run
               (1 - SSE / SS about the run's mean over all scored snapshots and cells)
For pooled statistics across runs (analysis/r2_report.py), each run also returns, per scored
snapshot, the true and predicted stored-energy fraction, thermocline height and outlet theta,
and the field sums needed for a pooled R2 (keys starting with '_'; lists are not averaged).
Reference: two CFD solutions of the same case that differ only in solver settings drifted
apart by about 0.65 K RMS within 60 s, and by 1 to 2 K over a few minutes, in early tests
(sensitivity of the buoyant jet to small changes). This is a measured sensitivity of the CFD
solution, not a numerical-noise floor. The 2026-11-06 verification found much smaller
sensitivity for production settings in the cases tested (see verification_criteria_2026-11-06.md).
y_mid, energy and profile errors are less affected than pointwise field errors.
"""
import numpy as np


def y_mid(theta, h):
    """Height (m) where the row-averaged profile first crosses 0.5, scanning down from the top."""
    prof = theta.mean(axis=-1)                       # [n, ny]
    y = (np.arange(prof.shape[-1]) + 0.5) * h
    out = np.full(prof.shape[0], np.nan)
    for n, p in enumerate(prof):
        d = p - 0.5
        for j in range(len(p) - 1, 0, -1):
            if d[j - 1] == 0:
                out[n] = y[j - 1]
                break
            if d[j - 1] * d[j] < 0:
                out[n] = y[j - 1] + (y[j] - y[j - 1]) * d[j - 1] / (d[j - 1] - d[j])
                break
    return out


def score(pred, true, dT, h, outlet=None):
    """Metrics for one run. pred, true: [n, ny, nx] theta; outlet: [ny, nx] map of the
    cells next to the outlet (data.port_maps), or None. Returns dict of floats."""
    pred = np.asarray(pred, float)
    true = np.asarray(true, float)
    err = pred - true
    t_out = float("nan")
    if outlet is not None and outlet.sum() > 0:
        w = outlet / outlet.sum()
        t_out = float(np.abs(((pred - true) * w).sum(axis=(1, 2))).mean() * dT)
    rmse = np.sqrt((err ** 2).mean(axis=(1, 2)))
    e_t, e_p = true.mean(axis=(1, 2)), pred.mean(axis=(1, 2))   # fraction of full capacity
    ym_t, ym_p = y_mid(true, h), y_mid(pred, h)
    both = np.isfinite(ym_t) & np.isfinite(ym_p)
    sst = float(((true - true.mean()) ** 2).sum())
    sse = float((err ** 2).sum())
    if outlet is not None and outlet.sum() > 0:
        w = outlet / outlet.sum()
        out_t, out_p = (true * w).sum(axis=(1, 2)), (pred * w).sum(axis=(1, 2))
    else:
        out_t = out_p = np.full(len(true), np.nan)
    return {
        "rmse_theta": float(rmse.mean()),
        "rmse_K": float(rmse.mean() * dT),
        "max_abs_K": float(np.abs(err).max() * dT),
        "y_mid_err_m": float(np.abs(ym_p - ym_t)[both].mean()) if both.any() else float("nan"),
        "y_mid_missing": float((np.isfinite(ym_t) != np.isfinite(ym_p)).mean()),
        "energy_err": float(np.abs(e_p - e_t).mean()),
        "profile_rmse": float(np.sqrt(((pred.mean(-1) - true.mean(-1)) ** 2).mean())),
        "T_out_err_K": t_out,
        "r2_field": 1.0 - sse / sst if sst > 0 else float("nan"),
        "_sse": sse, "_n": int(err.size), "_sum": float(true.sum()), "_sumsq": float((true ** 2).sum()),
        "_e_true": e_t.tolist(), "_e_pred": e_p.tolist(),
        "_ymid_true": ym_t.tolist(), "_ymid_pred": ym_p.tolist(),
        "_out_true": out_t.tolist(), "_out_pred": out_p.tolist(),
    }


def aggregate(per_run):
    """Mean of each metric over runs (NaN-aware), plus the number of runs."""
    keys = [k for k, v in per_run[0].items() if isinstance(v, float) and not k.startswith("_")]
    out = {k: float(np.nanmean([r[k] for r in per_run])) for k in keys}
    out["n_runs"] = len(per_run)
    return out
