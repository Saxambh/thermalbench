"""Tank verification comparisons (2026-11-06). Each pair: test run vs reference run, same design.
Fields are compared on the coarser of the two grids (finer one block-averaged by the integer ratio) at the
reference snapshot times (test fields interpolated linearly in time), t > 0 only.
  field_rms_pct     RMS over all cells and snapshots, % of dT = |T_in - T_0|
  mean_field_pct    RMS of the time-averaged field difference (less sensitive to phase drift), % of dT
  max_abs_K         largest local difference
  E_pct             max |E_test - E_ref| / max |E_ref - E_ref(0)|, %   (stored energy)
  Tout_rms_pct      outlet temperature series, RMS difference, % of dT
  ymid_mm           mean |y_mid difference| where both defined, mm; ymid_undef_mismatch share
usage: cmp_tank.py design.csv out.json  label:test.h5:ref.h5 ..."""
import csv, json, sys
import numpy as np, h5py
D = {r["run_id"]: r for r in csv.DictReader(open(sys.argv[1]))}
def coarsen(a, k):
    t, ny, nx = a.shape
    return a.reshape(t, ny // k, k, nx // k, k).mean((2, 4))
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
                      tout_test=np.interp(sb, sa, a["series/T_out_K"][:]).tolist())
        row = dict(pair=lab, t_event_s=t_ev, windows={k: wstat(m) for k, m in wins.items()}, series=series, snapshots=len(sel), time_offset_s=float(np.max(np.abs(np.interp(tb[sel], ta, ta) - tb[sel]))) if len(ta) else 0,
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
    w = row["windows"]; print("   windows (field / profile / outlet, % dT): " + "  ".join(
        f"{k} {v['t_from']:.0f}-{v['t_to']:.0f} s: {v['field_pct']:.2f} / {v['profile_pct']:.2f} / {v['Tout_pct'] if v['Tout_pct'] is None else round(v['Tout_pct'], 2)}"
        for k, v in w.items() if v) + f"   (outlet event {row['t_event_s']:.0f} s)")
    print(f"{lab:28s} n={row['snapshots']:3d} field {row['field_rms_pct']:6.2f} % ({row['field_rms_K']:.2f} K) quarters {[round(x,1) for x in row['field_rms_pct_quarters']]} profile {row['profile_rms_pct']:5.2f} %  mean-field {row['mean_field_pct']:6.2f} %  max {row['max_abs_K']:6.2f} K  "
          f"E {row['E_pct']:6.2f} %  Tout {row['Tout_rms_pct']:6.2f} %  ymid {row['ymid_mm'] if row['ymid_mm'] is None else round(row['ymid_mm'],1)} mm  t_end {row['t_end_s']:.0f}  {row['grid']}")
json.dump(out, open(sys.argv[2], "w"), indent=1)
