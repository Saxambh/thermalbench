"""Package ThermalStorageBench for a data repository (prepared 9 November 2026; run in WSL on the laptop).

  python3 make_release.py                 # dry run: plan the archives, write release/plan/, change nothing
  python3 make_release.py --build OUTDIR  # write the tar archives and SHA256SUMS into OUTDIR (e.g. on G:)

Contents, all taken from the frozen manifests (no file outside them is packed):
  tank_runs_NN.tar  each tank run folder: thermbench.h5, case.json, metrics.json, qc.json, system/
  pcm_runs_NN.tar   each PCM run folder, same files
  checkpoints.tar   96 tank checkpoints (results_merged/ckpt, without the replaced WRONG_SOURCE file) and
                    108 PCM checkpoints (results_pcm_release/ckpt), with their provenance tables
  manifests.tar     the two frozen manifests, the split code, label flags, dataset cards
Archives are cut at about 5 GB so that each upload is manageable. Logs and raw OpenFOAM time folders are
not packed (they stay on the machines until the DOI exists). The name inside the archives is still
'thermbench'; the rename to ThermalStorageBench is applied before the real build (see PLAN.md).
"""
import argparse, hashlib, json, os, tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ML = os.path.join(ROOT, "thermbench_ml")
KEEP = ("thermbench.h5", "case.json", "metrics.json", "qc.json")
SHARD = 5.0 * 1024 ** 3


def run_files(root, rid):
    d = os.path.join(root, rid)
    out = [os.path.join(d, f) for f in KEEP if os.path.exists(os.path.join(d, f))]
    sysd = os.path.join(d, "system")
    if os.path.isdir(sysd):
        out += [os.path.join(dp, f) for dp, _, fs in os.walk(sysd) for f in fs]
    return out


def plan_family(man, prefix):
    runs = sorted(json.load(open(os.path.join(ML, man)))["runs"], key=lambda r: r["run_id"])
    shards, cur, size, missing = [], [], 0, []
    for r in runs:
        files = run_files(r["root"], r["run_id"])
        if not any(f.endswith("thermbench.h5") for f in files):
            missing.append(r["run_id"]); continue
        s = sum(os.path.getsize(f) for f in files)
        if cur and size + s > SHARD:
            shards.append((cur, size)); cur, size = [], 0
        cur.append((r, files)); size += s
    if cur:
        shards.append((cur, size))
    return [(f"{prefix}_{i + 1:02d}.tar", c, s) for i, (c, s) in enumerate(shards)], missing


def extra():
    ck = []
    for d in ("results_merged/ckpt", "results_pcm_release/ckpt"):
        for f in sorted(os.listdir(os.path.join(ML, d))):
            if f.endswith(".pt") and "WRONG_SOURCE" not in f:
                ck.append(os.path.join(ML, d, f))
    ck += [os.path.join(ML, "repro_pcm_2026-11-08", "ckpt_sources.tsv"), os.path.join(ML, "repro_all_2026-11-08", "repro_all.json")]
    meta = [os.path.join(ML, f) for f in ("manifest_full_h5mm.json", "manifest_pcm.json", "splits.py", "pcm_splits.py", "label_flags_tank.json")]
    meta += [os.path.join(ROOT, f) for f in ("DATASET_CARD_tank_draft.md", "DATASET_CARD_pcm_draft.md")]
    return [("checkpoints.tar", ck), ("manifests.tar", meta)]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--build"); a = ap.parse_args()
    t, mt = plan_family("manifest_full_h5mm.json", "tank_runs")
    p, mp = plan_family("manifest_pcm.json", "pcm_runs")
    ex = extra()
    os.makedirs(os.path.join(HERE, "plan"), exist_ok=True)
    L = ["archive\truns\tfiles\tGB\tfirst_run\tlast_run"]
    for name, c, s in t + p:
        L.append(f"{name}\t{len(c)}\t{sum(len(f) for _, f in c)}\t{s / 1024 ** 3:.2f}\t{c[0][0]['run_id']}\t{c[-1][0]['run_id']}")
    for name, files in ex:
        L.append(f"{name}\t\t{len(files)}\t{sum(os.path.getsize(f) for f in files) / 1024 ** 3:.2f}\t\t")
    open(os.path.join(HERE, "plan", "archives.tsv"), "w").write("\n".join(L) + "\n")
    tot = sum(s for _, _, s in t + p) + sum(os.path.getsize(f) for _, fs in ex for f in fs)
    print("\n".join(L)); print(f"total {tot / 1024 ** 3:.1f} GB in {len(t) + len(p) + len(ex)} archives; missing runs: tank {mt}, pcm {mp}")
    if not a.build:
        return
    os.makedirs(a.build, exist_ok=True)
    sums = []
    for name, c, _ in t + p:
        with tarfile.open(os.path.join(a.build, name), "w") as tf:
            for r, files in c:
                for f in files:
                    tf.add(f, arcname=os.path.join(name.split("_runs")[0], r["run_id"], os.path.relpath(f, os.path.join(r["root"], r["run_id"]))))
    for name, files in ex:
        with tarfile.open(os.path.join(a.build, name), "w") as tf:
            for f in files:
                tf.add(f, arcname=os.path.relpath(f, ROOT))
    for name in sorted(os.listdir(a.build)):
        if name.endswith(".tar"):
            h = hashlib.sha256()
            with open(os.path.join(a.build, name), "rb") as fh:
                for b in iter(lambda: fh.read(1 << 22), b""):
                    h.update(b)
            sums.append(f"{h.hexdigest()}  {name}")
    open(os.path.join(a.build, "SHA256SUMS"), "w").write("\n".join(sums) + "\n")
    print("built", len(sums), "archives in", a.build)


if __name__ == "__main__":
    main()
