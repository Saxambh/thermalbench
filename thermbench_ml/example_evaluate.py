"""Evaluate a model on ThermalStorageBench in the same way as every model in the paper.

    python example_evaluate.py --family tank --split random --model idw     # reproduces Table 2: 9.32 %
    python example_evaluate.py --family pcm  --split random --model idw     # reproduces Table 3: 2.55 K
    python example_evaluate.py --family tank --split ood_mode --model mine  # your model (edit MyTankModel)

A model needs two methods:
  fit(train_runs) -> self             train on the split's training (and validation) runs
  predict(run, idx) -> fields         predict the snapshots idx of one test run
      tank: theta [len(idx), ny, nx], theta = (T - Tc) / (Th - Tc)
      PCM:  (theta [len(idx), ny, nx], liquid fraction [len(idx), ny, nx])
A run gives its design inputs as run.params() (names in data.PARAMS / pcm_data.PARAMS), its times as
run.times() -> (t in s, t* for the tank or tau = t / t_ref for PCM), and its grid size in run.meta.
The true fields (run.field(...)) are for training runs only; the scoring code reads them for test runs.

Scoring uses the unchanged evaluate.evaluate / pcm_evaluate.evaluate (tank: every 10th snapshot; PCM: every
5th, plus the melt-time query on a fixed input-only grid), so the numbers are directly comparable with
Tables 2 and 3. Report every metric printed, per training seed for learned models, and for PCM the share of
runs reaching t90 next to the t90 error.
"""
import argparse, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


class MyTankModel:
    """Template: replace with your model. This one predicts the initial field (the 'initial' baseline)."""

    def fit(self, train):
        return self

    def predict(self, run, idx):
        th0 = run.field("T", idx=[0], theta=True)[0]
        return np.repeat(th0[None], len(np.atleast_1d(idx)), 0)


class MyPCMModel:
    """Template: replace with your model. This one predicts the initial state (nothing melts)."""

    def fit(self, train):
        return self

    def predict(self, run, idx):
        ny, nx = run.mask().shape
        n = len(np.atleast_1d(idx))
        return np.zeros((n, ny, nx), np.float32), np.zeros((n, ny, nx), np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=["tank", "pcm"], required=True)
    ap.add_argument("--split", default="random")
    ap.add_argument("--model", default="idw", help="a baseline name (initial, knn, nn, idw, rbf, ...) or 'mine'")
    a = ap.parse_args()
    if a.family == "tank":
        import baselines
        from data import DEFAULT_ROOTS, index
        from splits import split_runs
        from evaluate import evaluate
        runs = index(DEFAULT_ROOTS, manifest=os.path.join(HERE, "manifest_full_h5mm.json"))
        makers = {"initial": baselines.Initial, "ideal_stratified": baselines.IdealStratified, "knn": baselines.KNN,
                  "nn": baselines.NN, "idw": baselines.IDW, "rbf": baselines.RBF, "mine": MyTankModel}
        stride, key, unit, scale = 10, "rmse_theta", "% of dT", 100
    else:
        import pcm_baselines
        from pcm_data import DEFAULT_ROOTS, index
        from pcm_splits import split_runs
        from pcm_evaluate import evaluate
        runs = index(DEFAULT_ROOTS, manifest=os.path.join(HERE, "manifest_pcm.json"))
        makers = dict(pcm_baselines.MAKERS) | {"mine": MyPCMModel}
        stride, key, unit, scale = 5, "rmse_K", "K", 1
    s = split_runs(runs, a.split)
    print(f"{a.family} / {a.split}: train {len(s['train'])}, val {len(s['val'])}, test {len(s['test'])} runs")
    model = makers[a.model]().fit(s["train"] + s["val"])
    res, per_run = evaluate(model, s["test"], stride)
    print(f"{a.model}: field RMSE {scale * res[key]:.2f} {unit}")
    for k, v in res.items():
        print(f"  {k:16s} {v:.4f}")


if __name__ == "__main__":
    main()
