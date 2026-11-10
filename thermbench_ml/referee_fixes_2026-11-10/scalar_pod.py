"""Referee fix 4 (PLAN.md): practitioner baselines, settings fixed here before any score.

  python scalar_pod.py tank|pcm

Inputs of every model: the run's parameter vector (data.PARAMS / pcm_data.PARAMS, as the networks get them) plus the
dimensionless time of the snapshot (tank t*, PCM tau). Fitted on train + val of each split, scored on the test runs at
the benchmark's snapshots (tank every 10th, PCM every 5th, t > 0). Inputs are standardised on the training rows.

Scalar regressors (no field): one model per quantity.
  gbm  sklearn HistGradientBoostingRegressor(max_iter=500, learning_rate=0.05, random_state=0)
  gp   sklearn GaussianProcessRegressor, ARD RBF + white noise, normalize_y, on 2,000 training rows drawn with seed 0
       (n_restarts_optimizer=2, random_state=0)
  Tank quantities: stored-energy fraction (mean theta), near-outlet theta, thermocline midpoint y_mid (rows where the
  label has one). Scored as metrics.score does: energy_err, T_out_err_K, y_mid_err_m.
  PCM quantities: melted fraction per snapshot (scored as melt_frac_err) and t90 (one row per run, target
  log(t90 / t_ref) from the CFD's own full series; scored as pcm_metrics.melt_time's relative error; always reached).
POD + regression (fields):
  POD of the training fields (theta; PCM theta and liquid fraction stacked), zero-padded to the widest domain,
  at most 8,000 training snapshots drawn with seed 0, 32 modes (randomized SVD, seed 0); one gbm (settings above)
  per mode coefficient. Scored with the unchanged evaluate.evaluate / pcm_evaluate.evaluate, so every field and
  engineering metric is comparable with the paper's tables.
Writes scalar_pod_<family>.json and prints one line per split and model.
"""
import json, os, sys, time
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel
from sklearn.utils.extmath import randomized_svd

HERE = os.path.dirname(os.path.abspath(__file__))
ML = os.path.dirname(HERE)
sys.path.insert(0, ML)
FAM = sys.argv[1]
NMODES, NPOD, NGP = 32, 8000, 2000


def gbm():
    return HistGradientBoostingRegressor(max_iter=500, learning_rate=0.05, random_state=0)


def gp(d):
    k = ConstantKernel(1.0) * RBF(length_scale=np.ones(d), length_scale_bounds=(1e-2, 1e3)) + WhiteKernel(1e-3, (1e-8, 1e0))
    return GaussianProcessRegressor(k, normalize_y=True, n_restarts_optimizer=2, random_state=0)


class Std:
    def fit(self, X):
        self.m, self.s = X.mean(0), X.std(0) + 1e-9
        return self

    def __call__(self, X):
        return (X - self.m) / self.s


def fit_scalar(X, y, kind):
    ok = np.isfinite(y)
    X, y = X[ok], y[ok]
    if kind == "gbm":
        return gbm().fit(X, y)
    sel = np.random.default_rng(0).choice(len(X), min(NGP, len(X)), replace=False)
    return gp(X.shape[1]).fit(X[sel], y[sel])


class POD:
    """Field model: POD modes of the padded training fields, gbm per coefficient. predict(run, idx) -> fields."""

    def __init__(self, nx_max, layers, crop):
        self.nx_max, self.layers, self.crop = nx_max, layers, crop

    def fit(self, rows, feats):
        F = np.stack(rows).astype(np.float32)            # [n, L*ny*nx_max]
        self.mean = F.mean(0)
        U, S, Vt = randomized_svd(F - self.mean, NMODES, random_state=0)
        self.modes = Vt.astype(np.float32)
        C = (F - self.mean) @ self.modes.T
        self.std = Std().fit(feats)
        self.reg = [gbm().fit(self.std(feats), C[:, k]) for k in range(NMODES)]
        self.energy = float((S ** 2).sum() / ((F - self.mean) ** 2).sum())
        return self

    def fields(self, x):
        c = np.stack([r.predict(self.std(x)) for r in self.reg], 1)
        return (self.mean + c @ self.modes).reshape(len(x), *self.layers)


def tank():
    import evaluate, metrics
    from data import DEFAULT_ROOTS, index, pad, port_maps
    from splits import SPLITS, split_runs
    runs = index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_full_h5mm.json"))
    nx_max = max(r.meta["nx"] for r in runs)
    ny = runs[0].meta["ny"]
    cache = {}
    t0 = time.time()
    for r in runs:
        tau = r.times()[1]
        idx = np.arange(10, len(tau), 10)
        th = r.field("T", idx=idx, theta=True)
        o = port_maps(r.meta, r.meta["ny"], r.meta["nx"])[1]
        cache[r.run_id] = {"x": np.column_stack([np.repeat(r.params()[None], len(idx), 0), tau[idx]]),
                           "e": th.mean((1, 2)), "out": (th * (o / o.sum())).sum((1, 2)), "ymid": metrics.y_mid(th, r.meta["mesh_h_m"]),
                           "f": pad(th, nx_max)[0].reshape(len(idx), -1).astype(np.float16), "dT": r.Th - r.Tc}
    print(f"loaded {len(cache)} runs in {time.time() - t0:.0f} s", flush=True)

    class Field:
        def __init__(self, pod):
            self.pod = pod

        def predict(self, run, idx):
            tau = run.times()[1][np.atleast_1d(idx)]
            x = np.column_stack([np.repeat(run.params()[None], len(tau), 0), tau])
            return self.pod.fields(x)[:, 0, :, : run.meta["nx"]]

    out = {}
    for split in SPLITS:
        s = split_runs(runs, split)
        tr, te = [cache[r.run_id] for r in s["train"] + s["val"]], s["test"]
        X = np.concatenate([c["x"] for c in tr])
        sd = Std().fit(X)
        res = {}
        for kind in ("gbm", "gp"):
            t1 = time.time()
            mdl = {q: fit_scalar(sd(X), np.concatenate([c[q] for c in tr]), kind) for q in ("e", "out", "ymid")}
            per = []
            for r in te:
                c = cache[r.run_id]
                p = {q: mdl[q].predict(sd(c["x"])) for q in mdl}
                both = np.isfinite(c["ymid"])
                per.append({"run_id": r.run_id, "energy_err": float(np.abs(np.clip(p["e"], 0, 1) - c["e"]).mean()),
                            "T_out_err_K": float(np.abs(np.clip(p["out"], 0, 1) - c["out"]).mean() * c["dT"]),
                            "y_mid_err_m": float(np.abs(p["ymid"] - c["ymid"])[both].mean()) if both.any() else float("nan")})
            res[f"scalar_{kind}"] = {"energy_err": float(np.mean([p["energy_err"] for p in per])),
                                     "T_out_err_K": float(np.mean([p["T_out_err_K"] for p in per])),
                                     "y_mid_err_m": float(np.nanmean([p["y_mid_err_m"] for p in per])), "per_run": per,
                                     "fit_s": round(time.time() - t1)}
            print(f"{split:8s} scalar_{kind}: energy {res[f'scalar_{kind}']['energy_err']:.4f}  outlet {res[f'scalar_{kind}']['T_out_err_K']:.3f} K  "
                  f"ymid {1000 * res[f'scalar_{kind}']['y_mid_err_m']:.1f} mm", flush=True)
        rng = np.random.default_rng(0)
        allrows = [(i, j) for i, c in enumerate(tr) for j in range(len(c["x"]))]
        sel = [allrows[k] for k in rng.choice(len(allrows), min(NPOD, len(allrows)), replace=False)]
        t1 = time.time()
        pod = POD(nx_max, (1, ny, nx_max), None).fit([tr[i]["f"][j] for i, j in sel], np.stack([tr[i]["x"][j] for i, j in sel]))
        agg, per = evaluate.evaluate(Field(pod), te, 10)
        res["pod_gbm"] = agg | {"per_run": per, "pod_energy": pod.energy, "fit_s": round(time.time() - t1)}
        print(f"{split:8s} pod_gbm: field {100 * agg['rmse_theta']:.2f} % dT  energy {agg['energy_err']:.4f}  outlet {agg['T_out_err_K']:.3f} K  "
              f"ymid {1000 * agg['y_mid_err_m']:.1f} mm  (POD energy {pod.energy:.4f})", flush=True)
        out[split] = res
        json.dump(out, open(os.path.join(HERE, "scalar_pod_tank.json"), "w"))


def pcm():
    import pcm_evaluate, pcm_metrics
    from pcm_data import DEFAULT_ROOTS, index, pad
    from pcm_splits import SPLITS, split_runs
    runs = index(DEFAULT_ROOTS, manifest=os.path.join(ML, "manifest_pcm.json"))
    nx_max = max(r.mask().shape[1] for r in runs)
    ny = runs[0].mask().shape[0]
    cache = {}
    t0 = time.time()
    for r in runs:
        t, tau = r.times()
        idx = np.arange(5, len(t), 5)
        w = r.mask() > 0
        a_all = r.field("alpha")
        fser = a_all[:, w].mean(1)
        th = r.field("T", idx=idx, theta=True)
        cache[r.run_id] = {"x": np.column_stack([np.repeat(r.params()[None], len(idx), 0), tau[idx]]), "p": r.params(),
                           "f": fser[idx], "t90": pcm_metrics._t_cross(t, fser, 0.9), "tref": r.t_ref,
                           "F": np.concatenate([pad(th, nx_max)[0], pad(a_all[idx], nx_max)[0]], 1).reshape(len(idx), -1).astype(np.float16)}
    print(f"loaded {len(cache)} runs in {time.time() - t0:.0f} s", flush=True)

    class Field:
        def __init__(self, pod):
            self.pod = pod

        def predict(self, run, idx):
            tau = run.times()[1][np.atleast_1d(idx)]
            x = np.column_stack([np.repeat(run.params()[None], len(tau), 0), tau])
            f = self.pod.fields(x)
            nx = run.mask().shape[1]
            return f[:, 0, :ny, :nx], np.clip(f[:, 0, ny:, :nx], 0, 1)

    out = {}
    for split in SPLITS:
        s = split_runs(runs, split)
        tr, te = [cache[r.run_id] for r in s["train"] + s["val"]], s["test"]
        X = np.concatenate([c["x"] for c in tr])
        P = np.stack([c["p"] for c in tr])
        sd, sp = Std().fit(X), Std().fit(P)
        res = {}
        for kind in ("gbm", "gp"):
            t1 = time.time()
            mf = fit_scalar(sd(X), np.concatenate([c["f"] for c in tr]), kind)
            mt = fit_scalar(sp(P), np.log(np.array([c["t90"] / c["tref"] for c in tr])), kind)
            per = []
            for r in te:
                c = cache[r.run_id]
                tp = float(np.exp(mt.predict(sp(c["p"][None]))[0]) * c["tref"])
                per.append({"run_id": r.run_id, "melt_frac_err": float(np.abs(np.clip(mf.predict(sd(c["x"])), 0, 1) - c["f"]).mean()),
                            "t90_err": abs(tp - c["t90"]) / c["t90"], "t90_reached": 1.0})
            res[f"scalar_{kind}"] = {"melt_frac_err": float(np.mean([p["melt_frac_err"] for p in per])),
                                     "t90_err": float(np.mean([p["t90_err"] for p in per])), "per_run": per, "fit_s": round(time.time() - t1)}
            print(f"{split:15s} scalar_{kind}: melt frac {res[f'scalar_{kind}']['melt_frac_err']:.4f}  t90 {100 * res[f'scalar_{kind}']['t90_err']:.1f} %", flush=True)
        rng = np.random.default_rng(0)
        allrows = [(i, j) for i, c in enumerate(tr) for j in range(len(c["x"]))]
        sel = [allrows[k] for k in rng.choice(len(allrows), min(NPOD, len(allrows)), replace=False)]
        t1 = time.time()
        pod = POD(nx_max, (1, 2 * ny, nx_max), None).fit([tr[i]["F"][j] for i, j in sel], np.stack([tr[i]["x"][j] for i, j in sel]))
        agg, per = pcm_evaluate.evaluate(Field(pod), te, 5)
        res["pod_gbm"] = agg | {"per_run": per, "pod_energy": pod.energy, "fit_s": round(time.time() - t1)}
        print(f"{split:15s} pod_gbm: field {agg['rmse_K']:.2f} K  alpha {agg['alpha_rmse']:.4f}  t90 {100 * agg['t90_err']:.1f} % "
              f"(reached {agg['t90_reached']:.2f})  (POD energy {pod.energy:.4f})", flush=True)
        out[split] = res
        json.dump(out, open(os.path.join(HERE, "scalar_pod_pcm.json"), "w"))


{"tank": tank, "pcm": pcm}[FAM]()
