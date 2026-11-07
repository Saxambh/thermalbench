"""ThermalStorageBench PCM scoring. Predictions and truth are theta = (T - T0)/(Tw - T0) and liquid
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
Melt time (melt_time, separate from score; changed 2026-11-07 after the independent review):
  t90_reached    1 if the prediction reaches 90 % melted within the fixed horizon, else 0
  t90_err        |t90 pred - t90 true| / t90 true, CONDITIONAL on t90_reached (NaN otherwise)
The prediction is queried on a grid fixed by the inputs only, tau = t / t_ref from 0 to TAU_H
(pcm_data.t_ref, a priori), never on the CFD file's times: those end at the true full melt,
which leaked the true duration into the scored window, and a prediction that had not reached 0.9
by then was dropped (NaN under nanmean), so the slowest wrong predictions disappeared. aggregate
reports t90_reach_rate over ALL runs and t90_err over the runs that reached it.
TAU_H = 3.0 was fixed before any PCM evaluation: the true 90 % point lies at tau 0.42 to 1.44 and
the runs end at tau 0.87 to 1.97 (158 accepted runs, 2026-11-07), so it leaves about a factor 2.
"""
import numpy as np

TAU_H = 3.0     # melt-time horizon in units of t_ref (fixed, see above)
N_Q = 601       # query points from tau 0 to TAU_H (step 0.005)


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
    return {
        "rmse_K": float(rmse.mean() * dT),
        "alpha_rmse": float(a_rmse.mean()),
        "liquid_iou": float(np.nanmean(iou)) if np.isfinite(iou).any() else float("nan"),
        "melt_frac_err": float(np.abs(fp - ft).mean()),
        "energy_err": float(np.abs(ep - et).mean()),
    }


def melt_time(t_q, f_pred_q, t_true, f_true, level=0.9):
    """t_q, f_pred_q: predicted melted fraction on the fixed query grid; t_true, f_true: the CFD
    series (always reaches 0.995). Returns t90_reached and the conditional relative t90 error."""
    tp, tt = _t_cross(np.asarray(t_q), np.asarray(f_pred_q), level), _t_cross(np.asarray(t_true), np.asarray(f_true), level)
    if not np.isfinite(tt):
        raise ValueError("CFD series never reaches the level: not an eligible run")
    ok = bool(np.isfinite(tp))
    return {"t90_reached": float(ok), "t90_err": float(abs(tp - tt) / tt) if ok else float("nan")}


def aggregate(per_run):
    keys = [k for k, v in per_run[0].items() if isinstance(v, float)]
    out = {k: float(np.nanmean([r[k] for r in per_run])) if any(np.isfinite(r[k]) for r in per_run)
           else float("nan") for k in keys}
    out["n_runs"] = len(per_run)
    return out
