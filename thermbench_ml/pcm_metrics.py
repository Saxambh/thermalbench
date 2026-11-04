"""ThermBench PCM scoring. Predictions and truth are theta = (T - T0)/(Tw - T0) and liquid
fraction alpha, each [n, ny, nx] on the run's native grid, at the run's snapshot times.

Per run (averaged over the scored snapshots), then averaged over runs:
  rmse_K         temperature RMS error over the whole box (PCM and fins), kelvin
  alpha_rmse     liquid-fraction RMS error over the PCM cells
  liquid_iou     intersection over union of the melted region (alpha > 0.5); 1 = exact
                 melt shape. Snapshots where neither has melted are skipped
  melt_frac_err  error in the overall melted fraction (mean alpha over the PCM)
  energy_err     error in stored energy as a fraction of a full charge
                 rho A (cp (Tw - T0) + L): e = (S theta + alpha) / (S + 1) per cell, with
                 S = cp (Tw - T0) / L (constant-property model, as the CFD)
  t90_err        relative error in the time at which 90 % has melted (interpolated between
                 snapshots); NaN when either never reaches 0.9 in the scored window
"""
import numpy as np


def _t_cross(t, f, level=0.9):
    i = np.nonzero(f >= level)[0]
    if not i.size:
        return np.nan
    i = i[0]
    if i == 0:
        return t[0]
    return t[i - 1] + (t[i] - t[i - 1]) * (level - f[i - 1]) / (f[i] - f[i - 1])


def score(pred_th, pred_a, true_th, true_a, pcm, dT, S, t):
    """pcm [ny, nx] 1 = PCM cell; dT = Tw - T0 (K); S = cp (Tw - T0) / L; t [n] times (s)."""
    pt, pa = np.asarray(pred_th, float), np.clip(np.asarray(pred_a, float), 0, 1)
    tt, ta = np.asarray(true_th, float), np.asarray(true_a, float)
    w = pcm > 0
    rmse = np.sqrt(((pt - tt) ** 2).mean(axis=(1, 2)))
    a_rmse = np.sqrt(((pa - ta)[:, w] ** 2).mean(axis=1))
    lp, lt = pa[:, w] > 0.5, ta[:, w] > 0.5
    union = (lp | lt).sum(1)
    inter = (lp & lt).sum(1)
    iou = np.where(union > 0, inter / np.maximum(union, 1), np.nan)
    fp, ft = pa[:, w].mean(1), ta[:, w].mean(1)
    ep = ((S * pt + pa)[:, w]).mean(1) / (S + 1)
    et = ((S * tt + ta)[:, w]).mean(1) / (S + 1)
    t90p, t90t = _t_cross(t, fp), _t_cross(t, ft)
    return {
        "rmse_K": float(rmse.mean() * dT),
        "alpha_rmse": float(a_rmse.mean()),
        "liquid_iou": float(np.nanmean(iou)) if np.isfinite(iou).any() else float("nan"),
        "melt_frac_err": float(np.abs(fp - ft).mean()),
        "energy_err": float(np.abs(ep - et).mean()),
        "t90_err": float(abs(t90p - t90t) / t90t) if np.isfinite(t90p) and np.isfinite(t90t) else float("nan"),
    }


def aggregate(per_run):
    keys = [k for k, v in per_run[0].items() if isinstance(v, float)]
    out = {k: float(np.nanmean([r[k] for r in per_run])) if any(np.isfinite(r[k]) for r in per_run)
           else float("nan") for k in keys}
    out["n_runs"] = len(per_run)
    return out
