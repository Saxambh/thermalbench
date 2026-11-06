"""Tank verification comparisons (2026-11-06). Each pair: test run vs reference run, same design.
Fields are compared on the coarser of the two grids (finer one block-averaged by the integer ratio) at the
reference snapshot times (test fields interpolated linearly in time), t > 0 only.
  field_rms_pct     RMS over all cells and snapshots, % of dT = |T_in - T_0|
  mean_field_pct    RMS of the time-averaged field difference (less sensitive to phase drift), % of dT
  max_abs_K         largest local difference
  E_pct             max |E_test - E_ref| / max |E_ref - E_ref(0)|, %   (stored energy)
  Tout_rms_pct      outlet temperature series, RMS difference, % of dT
  ymid_mm           mean |y_mid difference| where both defined, mm; ymid_undef_mismatch share
  extra             thermocline thickness, MIX and stratification number (mean / max |difference| where both
                    are defined, share of snapshots defined in only one run), outlet backflow (share of outlet
                    cells with velocity into the tank, per snapshot; mean over snapshots, share of snapshots with any)
  windows           field / profile / outlet error before, around (+0.2 t_end) and after the outlet event
usage: cmp_tank.py design.csv out.json  label:test.h5:ref.h5 ..."""
import csv, json, sys
import numpy as np, h5py
D = {r["run_id"]: r for r in csv.DictReader(open(sys.argv[1]))}
def coarsen(a, k):
    t, ny, nx = a.shape
    return a.reshape(t, ny // k, k, nx // k, k).mean((2, 4))
def backflow_share(f):
    """Share of the outlet-adjacent cells whose velocity points into the tank, per snapshot."""
    cj = json.loads(f.attrs["case_json"]); side, a0, b0 = cj["outlet_port"]; h = cj["mesh_h_m"]
    ny, nx = f["fields/T"].shape[1:]; ux, uy = f["fields/ux"], f["fields/uy"]
    if side in ("left", "right"):
        j = [k for k in range(ny) if a0 < (k + 0.5) * h < b0]; i = nx - 1 if side == "right" else 0
        u = ux[:, j, i] * (1 if side == "right" else -1)
    else:
        i = [k for k in range(nx) if a0 < (k + 0.5) * h < b0]; j = ny - 1 if side == "top" else 0
        u = uy[:, j, :][:, i] * (1 if side == "top" else -1)
    return (u < 0).mean(axis=1)
def pair_stats(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    return (float(np.mean(np.abs(x[ok] - y[ok]))) if ok.any() else None, float(np.max(np.abs(x[ok] - y[ok]))) if ok.any() else None,
            float(np.mean(np.isfinite(x) != np.isfinite(y))))
out = []
for spec in sys.argv[3:]:
    lab, ft, fr = spec.split(":")
    rid = lab.split("|")[0]; r = D[rid]; dT = abs(float(r["T_in"]) - float(r["T_0"]))
    with h5py.File(ft) as a, h5py.File(fr) as b:
        ta, tb = a["times_s"][:], b["times_s"][:]
        sel = [i for i in range(len(tb)) if tb[i] > 0 and ta[0] <= tb[i] <= ta[-1] + 1e-6]
        def at(F, tt):
            res = []
            for x in tt:
                j = min(max(int(np.searchsorted(ta, x)), 1), len(ta) - 1); w = (x - ta[j - 1]) / (ta[j] - ta[j - 1])
                w = min(max(w, 0.0), 1.0); res.append((1 - w) * F[j - 1] + w * F[j])
            return np.array(res)
        A = at(a["fields/T"], tb[sel]); B = b["fields/T"][sel]
        if A.shape[1] > B.shape[1]: A = coarsen(A, A.shape[1] // B.shape[1])
        elif B.shape[1] > A.shape[1]: B = coarsen(B, B.shape[1] // A.shape[1])
        d = A - B
        Ea, Eb = np.interp(tb, ta, a["metrics/E_J"][:]), b["metrics/E_J"][:]
        sa, sb = a["series/T_out_t_s"][:], b["series/T_out_t_s"][:]
        To = np.interp(sb, sa, a["series/T_out_K"][:]) - b["series/T_out_K"][:]
        ya, yb = np.interp(tb, ta, a["metrics/y_mid_m"][:]), b["metrics/y_mid_m"][:]
        ok = np.isfinite(ya) & np.isfinite(yb)
        # event windows from the reference run: outlet event = outlet T has moved 10 % of its total change
        To_ref = b["series/T_out_K"][:]; ch = np.abs(To_ref - To_ref[0]); tot = ch.max()
        t_ev = float(sb[np.argmax(ch > 0.1 * tot)]) if tot > 0 else float("nan")
        t_end = float(tb[-1]); ts = tb[sel]
        wins = {"early": ts < t_ev, "event": (ts >= t_ev) & (ts < t_ev + 0.2 * t_end), "late": ts >= t_ev + 0.2 * t_end}
        def wstat(m):
            if not m.any(): return None
            so = (sb >= ts[m][0]) & (sb <= ts[m][-1])
            return dict(n=int(m.sum()), t_from=float(ts[m][0]), t_to=float(ts[m][-1]),
                        field_pct=float(100 * np.sqrt(np.mean(d[m] ** 2)) / dT),
                        profile_pct=float(100 * np.sqrt(np.mean((A[m].mean(2) - B[m].mean(2)) ** 2)) / dT),
                        Tout_pct=float(100 * np.sqrt(np.mean(To[so] ** 2)) / dT) if so.any() else None)
        series = dict(t=ts.tolist(), field_pct=(100 * np.sqrt((d ** 2).mean((1, 2))) / dT).tolist(),
                      profile_pct=(100 * np.sqrt(((A.mean(2) - B.mean(2)) ** 2).mean(1)) / dT).tolist(),
                      dE_pct=(100 * (Ea - Eb)[sel] / max(np.max(np.abs(Eb - Eb[0])), 1e-30)).tolist(),
                      dymid_mm=(1000 * (ya - yb)[sel]).tolist(), tout_t=sb.tolist(), tout_ref=To_ref.tolist(),
                      tout_test=np.interp(sb, sa, a["series/T_out_K"][:]).tolist(),
                      dthick_mm=(1000 * (np.interp(tb, ta, a["metrics/thick_m"][:]) - b["metrics/thick_m"][:])[sel]).tolist(),
                      dMIX=(np.interp(tb, ta, a["metrics/MIX"][:]) - b["metrics/MIX"][:])[sel].tolist(),
                      backflow_ref=backflow_share(b)[sel].tolist(), backflow_test=np.interp(tb, ta, backflow_share(a))[sel].tolist())
        # thermocline thickness, MIX, stratification number (where defined in both), outlet backflow
        extra = {}
        for key in ("thick_m", "MIX", "Str"):
            xa, xb = np.interp(tb, ta, a[f"metrics/{key}"][:]), b[f"metrics/{key}"][:]
            m_, mx_, mis = pair_stats(xa[sel], xb[sel])
            extra[key] = dict(mean_abs_diff=m_, max_abs_diff=mx_, undefined_mismatch=mis,
                              ref_range=float(np.nanmax(xb) - np.nanmin(xb)) if np.isfinite(xb).any() else None)
        bfa, bfb = backflow_share(a), backflow_share(b)
        bfa_t = np.interp(tb, ta, bfa)
        extra["backflow"] = dict(ref_share_mean=float(bfb[sel].mean()), test_share_mean=float(bfa_t[sel].mean()),
                                 ref_snapshots_with_backflow=float((bfb[sel] > 0).mean()), test_snapshots_with_backflow=float((bfa_t[sel] > 0).mean()),
                                 mean_abs_diff=float(np.mean(np.abs(bfa_t[sel] - bfb[sel]))))
        row = dict(pair=lab, t_event_s=t_ev, extra=extra, windows={k: wstat(m) for k, m in wins.items()}, series=series, snapshots=len(sel), time_offset_s=float(np.max(np.abs(np.interp(tb[sel], ta, ta) - tb[sel]))) if len(ta) else 0,
                   grid=f"{a['fields/T'].shape[1:]} vs {b['fields/T'].shape[1:]}",
                   field_rms_pct=float(100 * np.sqrt(np.mean(d ** 2)) / dT),
                   mean_field_pct=float(100 * np.sqrt(np.mean(d.mean(0) ** 2)) / dT),
                   max_abs_K=float(np.max(np.abs(d))),
                   field_rms_K=float(np.sqrt(np.mean(d ** 2))),
                   profile_rms_pct=float(100 * np.sqrt(np.mean((A.mean(2) - B.mean(2)) ** 2)) / dT),
                   field_rms_pct_quarters=[float(100 * np.sqrt(np.mean(q ** 2)) / dT) for q in np.array_split(d, 4)],
                   E_pct=float(100 * np.max(np.abs(Ea - Eb)) / max(np.max(np.abs(Eb - Eb[0])), 1e-30)),
                   Tout_rms_pct=float(100 * np.sqrt(np.mean(To ** 2)) / dT),
                   ymid_mm=float(1000 * np.mean(np.abs(ya[ok] - yb[ok]))) if ok.any() else None,
                   ymid_undef_mismatch=float(np.mean(np.isfinite(ya) != np.isfinite(yb))),
                   t_end_s=float(tb[sel][-1]) if sel else 0)
    out.append(row)
    e = row["extra"]; fmt = lambda v, k=1: "n/a" if v is None else round(v, k)
    print(f"   thickness mean |d| {fmt(None if e['thick_m']['mean_abs_diff'] is None else 1000 * e['thick_m']['mean_abs_diff'])} mm (undefined mismatch {e['thick_m']['undefined_mismatch']:.2f})"
          f"  MIX mean |d| {fmt(e['MIX']['mean_abs_diff'], 4)} (ref range {fmt(e['MIX']['ref_range'], 3)})  Str mean |d| {fmt(e['Str']['mean_abs_diff'], 4)}"
          f"  outlet backflow share ref {e['backflow']['ref_share_mean']:.3f} test {e['backflow']['test_share_mean']:.3f} (snapshots with any: {e['backflow']['ref_snapshots_with_backflow']:.2f} / {e['backflow']['test_snapshots_with_backflow']:.2f})")
    w = row["windows"]; print("   windows (field / profile / outlet, % dT): " + "  ".join(
        f"{k} {v['t_from']:.0f}-{v['t_to']:.0f} s: {v['field_pct']:.2f} / {v['profile_pct']:.2f} / {v['Tout_pct'] if v['Tout_pct'] is None else round(v['Tout_pct'], 2)}"
        for k, v in w.items() if v) + f"   (outlet event {row['t_event_s']:.0f} s)")
    print(f"{lab:28s} n={row['snapshots']:3d} field {row['field_rms_pct']:6.2f} % ({row['field_rms_K']:.2f} K) quarters {[round(x,1) for x in row['field_rms_pct_quarters']]} profile {row['profile_rms_pct']:5.2f} %  mean-field {row['mean_field_pct']:6.2f} %  max {row['max_abs_K']:6.2f} K  "
          f"E {row['E_pct']:6.2f} %  Tout {row['Tout_rms_pct']:6.2f} %  ymid {row['ymid_mm'] if row['ymid_mm'] is None else round(row['ymid_mm'],1)} mm  t_end {row['t_end_s']:.0f}  {row['grid']}")
json.dump(out, open(sys.argv[2], "w"), indent=1)
