"""PCM fine-mesh label check (PLAN.md, Part A): label shift and rescoring against 0.25 mm labels.

  python compare_finemesh.py shift   --fine-roots <dir> [<dir> ...]
  python compare_finemesh.py rescore --fine-roots <dir> [<dir> ...] [--ckpt-dirs <dir> ...]
  python compare_finemesh.py verdicts

Fine runs: <root>/<case_id>/{DONE, thermbench.h5}, for the case ids of selection.json only.

Fine labels on the dataset grid: the fine fields are 2 x 2 block-averaged (spotcheck.block) at the dataset run's own
snapshot times. The fine run writes at the same interval and runs longer (it melts later), so its first n - 1 snapshot
times must equal the dataset's (relative 1e-6), else the case is reported and excluded. The dataset's last snapshot is
its auto-stop time, off the write grid; there the fine fields are interpolated linearly in time between the two
bracketing fine snapshots (found on the spot runs P0083 and P0301 before launch, 10 November). Fins snap to the finer mesh
slightly differently (P0083: 9 of 8,200 cells differ after block averaging), so the block-averaged fine mask may differ
from the dataset mask in at most 1 % of the cells, else the case is excluded; the count is reported per case, and
scoring always uses the dataset mask (an input).

shift   -> shift.json: per case, field rmse (K and % of dT, the paper's rmse_K definition), liquid-fraction rmse on
           the PCM cells, t90 and t99 of the melted fraction (each from its own full dense series), their shift.
rescore -> rescore.json: every model of the paper scored on the finished fine cases of each split's test set, with
           the unchanged pcm_evaluate code path, twice: against the dataset labels and against the fine labels.
           Melt times: the true t90 comes from the label set's own full series (fine: the fine run's whole series).
           Baselines are refit on train + val as in pcm_evaluate; networks use the released checkpoints
           (results_pcm_release/ckpt) and the seeds 3-4 checkpoints (results_pcm_s34/ckpt, material splits).
verdicts -> verdicts.json / verdicts.md: per split, models averaged over seeds per case; for every model pair the
           paired bootstrap (10,000 resamples over cases, seed 20261110) of the mean difference in rmse_K and t90_err
           under both label sets, and the PLAN's verdict: holds / not resolved by the labels / flips.
"""
import argparse, glob, hashlib, itertools, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
sys.path.insert(0, ML)
import pcm_baselines, pcm_evaluate, pcm_metrics
from pcm_data import DEFAULT_ROOTS, index
from pcm_splits import SPLITS, split_runs

MAN = os.path.join(ML, "manifest_pcm.json")
SEL = json.load(open(os.path.join(HERE, "selection.json")))
CASES = [c["case_id"] for c in SEL["cases"]]
BOOT, BOOT_SEED = 10000, 20261110


def block(a):   # [t, 2ny, 2nx] -> [t, ny, nx], as scripts/spotcheck.py
    t, ny, nx = a.shape
    return a[:, :ny // 2 * 2, :nx // 2 * 2].reshape(t, ny // 2, 2, nx // 2, 2).mean((2, 4))


class FineLabels:
    """A dataset run whose labels are the fine run's, block-averaged at the dataset snapshot times. Inputs (meta,
    times, mask) stay the dataset run's, so every predictor sees exactly what it saw in the paper."""

    def __init__(self, run, fine_dir):
        import h5py
        self._run, self.fine_dir = run, fine_dir
        t = run.times()[0]
        with h5py.File(os.path.join(fine_dir, "thermbench.h5"), "r") as f:
            tf = f["times_s"][:]
            self.ok, self.why = True, ""
            n = len(t) - 1     # the dataset's last snapshot is its auto-stop time, off the write grid
            if len(tf) < len(t) or not np.allclose(tf[:n], t[:n], rtol=1e-6, atol=1e-9) or not tf[n - 1] <= t[n] <= tf[-1]:
                self.ok, self.why = False, f"snapshot times differ (fine {len(tf)}, dataset {len(t)})"
                return
            j = int(np.searchsorted(tf, t[n]))          # tf[j-1] < t[n] <= tf[j]
            wj = (t[n] - tf[j - 1]) / (tf[j] - tf[j - 1])
            last = lambda k: (1 - wj) * f[k][j - 1].astype(np.float64) + wj * f[k][j].astype(np.float64)
            T = block(np.concatenate([f["fields/T"][:n].astype(np.float64), last("fields/T")[None]]))
            A = block(np.concatenate([f["fields/alpha"][:n].astype(np.float64), last("fields/alpha")[None]]))
            mf = block(f["mask"][:][None].astype(np.float64))[0]
            self.n_mask_diff = int((np.round(mf) != run.mask()).sum()) if mf.shape == run.mask().shape else -1
            if T.shape[1:] != run.mask().shape or not 0 <= self.n_mask_diff <= 0.01 * run.mask().size:
                self.ok, self.why = False, f"fine mask differs from the dataset mask in {self.n_mask_diff} cells (> 1 %)"
                return
            self.T, self.A = T.astype(np.float32), A.astype(np.float32)
            wf = f["mask"][:] > 0
            self.full_t, self.full_f = tf, f["fields/alpha"][:][:, wf].mean(1)

    def field(self, name="T", idx=None, theta=False):
        a = {"T": self.T, "alpha": self.A}[name]
        a = a if idx is None else a[np.sort(np.atleast_1d(idx))]
        if theta and name == "T":
            a = (a - self._run.T0) / (self._run.Tw - self._run.T0)
        return a.astype(np.float32)

    def __getattr__(self, k):
        return getattr(self._run, k)


def evaluate(model, test, stride, melt_series):
    """pcm_evaluate.evaluate with the true melt series passed in (label set's own full series)."""
    per_run = []
    for r in test:
        t = r.times()[0]
        idx = np.arange(stride, len(t), stride)
        p_th, p_a = model.predict(r, idx)
        m = r.meta
        S = m["props"]["cp"] * (m["T_wall_K"] - m["T_init_K"]) / m["props"]["L"]
        sc = pcm_metrics.score(p_th, p_a, r.field("T", idx=idx, theta=True), r.field("alpha", idx=idx),
                               r.mask(), r.Tw - r.T0, S, t[idx])
        t_q = np.linspace(0, pcm_metrics.TAU_H, pcm_metrics.N_Q) * r.t_ref
        w = r.mask() > 0
        f_q = np.concatenate([model.predict(pcm_evaluate.QueryRun(r, t_q[i:i + 50]), np.arange(len(t_q[i:i + 50])))[1][:, w].mean(1)
                              for i in range(0, len(t_q), 50)])
        tt, ft = melt_series(r)
        sc |= pcm_metrics.melt_time(t_q, f_q, tt, ft)
        per_run.append(sc | {"run_id": r.run_id})
    return per_run


def load(fine_roots):
    runs = {r.run_id: r for r in index(DEFAULT_ROOTS, manifest=MAN)}
    fine, skipped = {}, {}
    for c in CASES:
        d = [os.path.join(os.path.expanduser(root), c) for root in fine_roots]
        d = [x for x in d if os.path.exists(os.path.join(x, "DONE")) and os.path.exists(os.path.join(x, "thermbench.h5"))]
        if not d:
            skipped[c] = "not finished"
            continue
        fl = FineLabels(runs[c], d[0])
        if fl.ok:
            fine[c] = fl
        else:
            skipped[c] = fl.why
    return runs, fine, skipped


def shift(a):
    runs, fine, skipped = load(a.fine_roots)
    rows = []
    for c, fl in fine.items():
        r = runs[c]
        dT = r.Tw - r.T0
        th_d, th_f = r.field("T", theta=True), fl.field("T", theta=True)
        w = r.mask() > 0
        rmse = float(np.sqrt(((th_d - th_f) ** 2).mean(axis=(1, 2))).mean() * dT)
        a_rmse = float(np.sqrt(((r.field("alpha") - fl.field("alpha"))[:, w] ** 2).mean(1)).mean())
        td, fd = r.times()[0], r.field("alpha")[:, w].mean(1)
        out = {"case_id": c, "stratum": next(x["stratum"] for x in SEL["cases"] if x["case_id"] == c),
               "material": r.meta.get("material"), "dT_K": dT, "rmse_K": rmse, "rmse_pct_dT": 100 * rmse / dT,
               "alpha_rmse": a_rmse, "n_mask_diff": fl.n_mask_diff, "fine_dir": fl.fine_dir}
        for lv in (0.9, 0.99):
            t0, t1 = pcm_metrics._t_cross(td, fd, lv), pcm_metrics._t_cross(fl.full_t, fl.full_f, lv)
            out[f"t{int(lv * 100)}_s"] = [float(t0), float(t1)]
            out[f"t{int(lv * 100)}_shift_pct"] = float(100 * (t1 - t0) / t0)
        rows.append(out)
    json.dump({"n_finished_ok": len(rows), "skipped": skipped, "rows": rows}, open(os.path.join(HERE, "shift.json"), "w"), indent=1)
    print(f"{len(rows)} cases; skipped {len(skipped)}")
    for k in ("rmse_pct_dT", "alpha_rmse", "t90_shift_pct", "t99_shift_pct"):
        v = np.array([x[k] for x in rows])
        if len(v):
            print(f"{k:15s} median {np.median(v):7.3f}  min {v.min():7.3f}  max {v.max():7.3f}")


def rescore(a):
    import torch, pcm_train
    from models import MODELS
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    runs, fine, skipped = load(a.fine_roots)
    allruns = list(runs.values())
    out = {"manifest_md5": hashlib.md5(open(MAN, "rb").read()).hexdigest(), "fine_cases": sorted(fine), "skipped": skipped, "splits": {}}
    lab_d = lambda r: (r.times()[0], r.field("alpha")[:, r.mask() > 0].mean(1))
    lab_f = lambda r: (r.full_t, r.full_f)
    for split in SPLITS:
        s = split_runs(allruns, split)
        test = [r for r in s["test"] if r.run_id in fine]
        if not test:
            continue
        test_f = [fine[r.run_id] for r in test]
        res = {}
        for name in pcm_baselines.MAKERS:
            m = pcm_baselines.MAKERS[name]().fit(s["train"] + s["val"])
            res[name] = {"coarse": evaluate(m, test, 5, lab_d), "fine": evaluate(m, test_f, 5, lab_f)}
        for arch in ("fno", "unet", "transolver"):
            for hyb in (False, True):
                enc = pcm_train.Encoder(s["train"], hybrid=hyb)
                for tag in ("", "_s1", "_s2", "_s3", "_s4"):
                    name = f"{arch}{'_hybrid' if hyb else ''}{tag}"
                    ck = [p for d in a.ckpt_dirs for p in [os.path.join(os.path.expanduser(d), f"ckpt_pcm_{name}_{split}.pt")] if os.path.exists(p)]
                    if not ck:
                        continue
                    net = MODELS[arch](enc.channels, cout=2, **({"width": 32} if arch == "fno" else {"base": 32}))
                    net.load_state_dict(torch.load(ck[0], map_location=dev)); net.to(dev).eval()
                    pred = pcm_train.Predictor(net, enc, dev)
                    res[name] = {"coarse": evaluate(pred, test, 5, lab_d), "fine": evaluate(pred, test_f, 5, lab_f),
                                 "ckpt": ck[0], "ckpt_md5": hashlib.md5(open(ck[0], "rb").read()).hexdigest()}
                    print(f"{split:15s} {name:22s} n {len(test)}  rmse_K coarse "
                          f"{np.mean([x['rmse_K'] for x in res[name]['coarse']]):.3f}  fine {np.mean([x['rmse_K'] for x in res[name]['fine']]):.3f}", flush=True)
        out["splits"][split] = {"n_test_fine": len(test), "models": res}
        json.dump(out, open(os.path.join(HERE, "rescore.json"), "w"), indent=1)
    print("done")


def base(name):   # fno_hybrid_s3 -> fno_hybrid
    return name.rsplit("_s", 1)[0] if name[-3:-1] == "_s" else name


def verdicts(a):
    R = json.load(open(os.path.join(HERE, "rescore.json")))
    rng = np.random.default_rng(BOOT_SEED)
    out, md = {}, ["# Fine-mesh rescoring: pair verdicts (PLAN.md decision rules)", ""]
    for split, S in R["splits"].items():
        groups = {}
        for name in S["models"]:
            groups.setdefault(base(name), []).append(name)
        ids = [p["run_id"] for p in S["models"][next(iter(S["models"]))]["coarse"]]
        table = {}
        for g, names in groups.items():
            table[g] = {}
            for lab in ("coarse", "fine"):
                for k in ("rmse_K", "t90_err"):
                    per = np.array([[{p["run_id"]: p for p in S["models"][n][lab]}[i][k] for i in ids] for n in names], float)
                    table[g][(lab, k)] = np.nanmean(per, 0)   # mean over seeds per case
        idx = rng.integers(0, len(ids), (BOOT, len(ids)))
        out[split] = {"n_cases": len(ids), "seeds": {g: len(v) for g, v in groups.items()},
                      "means": {g: {f"{l}_{k}": float(np.nanmean(v)) for (l, k), v in table[g].items()} for g in table}, "pairs": []}
        md += [f"## {split} ({len(ids)} cases)", "", "| pair | metric | diff 0.5 mm | diff 0.25 mm [95 % CI] | verdict |", "|---|---|---|---|---|"]
        for g1, g2 in itertools.combinations(sorted(table), 2):
            for k in ("rmse_K", "t90_err"):
                d = {lab: table[g1][(lab, k)] - table[g2][(lab, k)] for lab in ("coarse", "fine")}
                if np.isnan(d["fine"]).all():
                    continue
                bf = np.nanmean(d["fine"][idx], 1)
                lo, hi = np.nanpercentile(bf, [2.5, 97.5])
                mc, mf = float(np.nanmean(d["coarse"])), float(np.nanmean(d["fine"]))
                if lo <= 0 <= hi:
                    v = "not resolved by the labels"
                elif np.sign(mc) == np.sign(mf):
                    v = "holds"
                else:
                    v = "flips"
                out[split]["pairs"].append({"a": g1, "b": g2, "metric": k, "diff_coarse": mc, "diff_fine": mf, "ci_fine": [float(lo), float(hi)], "verdict": v})
                md.append(f"| {g1} - {g2} | {k} | {mc:+.3f} | {mf:+.3f} [{lo:+.3f}, {hi:+.3f}] | {v} |")
        md.append("")
    json.dump(out, open(os.path.join(HERE, "verdicts.json"), "w"), indent=1)
    open(os.path.join(HERE, "verdicts.md"), "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["shift", "rescore", "verdicts"])
    ap.add_argument("--fine-roots", nargs="+", default=["~/tb_data/finemesh_2026-11-10/*"])
    ap.add_argument("--ckpt-dirs", nargs="+", default=[os.path.join(ML, "results_pcm_release", "ckpt"), os.path.join(ML, "results_pcm_s34", "ckpt")])
    a = ap.parse_args()
    a.fine_roots = [g for r in a.fine_roots for g in (glob.glob(os.path.expanduser(r)) or [r])]
    {"shift": shift, "rescore": rescore, "verdicts": verdicts}[a.what](a)
