"""Melt-front diagnostics shared by the PCM comparisons (2026-11-07).
front_x: per snapshot and row, distance (m) from the heated wall (column 0) to the first cell where the
liquid fraction drops below 0.5 (linear interpolation between cells); NaN where the row is all solid or all
liquid. front_metrics: mean |front difference| (mm) over rows and snapshots where both are defined, and
the share of the squared temperature error that lies in the mushy/front band (cells with 0.02 < alpha < 0.98
in either run, widened by one cell) against the band's share of the PCM area."""
import numpy as np
def front_x(alpha, h):
    n, ny, nx = alpha.shape; out = np.full((n, ny), np.nan)
    below = alpha < 0.5
    for t in range(n):
        for j in range(ny):
            row = alpha[t, j]; k = np.argmax(below[t, j])
            if not below[t, j].any() or k == 0: continue
            a0, a1 = row[k - 1], row[k]; w = (a0 - 0.5) / (a0 - a1) if a0 != a1 else 0.0
            out[t, j] = (k - 0.5 + w) * h
    return out
def front_metrics(alpha_a, alpha_b, T_a, T_b, h, mask=None):
    fa, fb = front_x(alpha_a, h), front_x(alpha_b, h); ok = np.isfinite(fa) & np.isfinite(fb)
    band = ((alpha_a > 0.02) & (alpha_a < 0.98)) | ((alpha_b > 0.02) & (alpha_b < 0.98))
    wide = band.copy(); wide[:, 1:, :] |= band[:, :-1, :]; wide[:, :-1, :] |= band[:, 1:, :]; wide[:, :, 1:] |= band[:, :, :-1]; wide[:, :, :-1] |= band[:, :, 1:]
    if mask is not None: wide &= mask[None]; area = mask[None] & np.ones_like(wide)
    else: area = np.ones_like(wide)
    e2 = (T_a - T_b) ** 2
    return dict(front_mean_abs_mm=float(1000 * np.mean(np.abs(fa[ok] - fb[ok]))) if ok.any() else None,
                front_p95_abs_mm=float(1000 * np.percentile(np.abs(fa[ok] - fb[ok]), 95)) if ok.any() else None,
                error_share_in_front_band=float(e2[wide].sum() / max(e2[area].sum(), 1e-30)),
                front_band_area_share=float(wide.sum() / max(area.sum(), 1)))
