"""Temperature-only copies of the frozen runs, for GPU machines behind a slow link (pc5, 2026-11-04).
Training, evaluation and the baselines read only fields/T, metrics/*, times_s and tstar from
thermbench.h5 (plus case.json); velocity, pressure and the outlet time series are not used. The slim
copy keeps exactly those datasets (same float32 values, same gzip settings, checked equal after
writing), about 6.5x smaller (6.4 vs 41.8 MB for T0362_lam). Next to each slim file,
thermbench.h5.slim records the md5 of the full file it came from (must equal the manifest md5) and
the md5 of the slim file, so check_data.py can verify slim copies too.
  python3 make_slim.py <manifest> [--out ~/tb_slim]      (run in WSL on the laptop, the hub)
Output layout matches data.DEFAULT_ROOTS on the target: ~/tb_slim/<origin>/<batch>/<run_id>/...,
then rsync ~/tb_slim/ to <host>:tb_data/. Reruns skip runs already done."""
import hashlib, json, os, shutil, sys
import h5py
import numpy as np

KEEP = ("fields/T", "times_s", "tstar")
SIDE = ("DONE", "case.json", "metrics.json", "qc.json")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def target(root):
    """laptop ~/of_runs/<batch> -> laptop/<batch>; ~/tb_data/<origin>/<batch> stays <origin>/<batch>."""
    parts = os.path.normpath(root).split(os.sep)
    return os.path.join("laptop", parts[-1]) if parts[-2] == "of_runs" else os.path.join(parts[-2], parts[-1])


def slim(src, dst):
    with h5py.File(src, "r") as a, h5py.File(dst, "w") as b:
        for k in KEEP:
            d = a[k]
            b.create_dataset(k, data=d[:], chunks=d.chunks, compression=d.compression,
                             compression_opts=d.compression_opts, shuffle=d.shuffle)
        a.copy("metrics", b)
    with h5py.File(src, "r") as a, h5py.File(dst, "r") as b:
        for k in KEEP + tuple(f"metrics/{m}" for m in a["metrics"]):
            if not np.array_equal(a[k][:], b[k][:], equal_nan=True):   # MIX can hold NaN
                raise RuntimeError(f"{dst}: {k} differs from the source")


def main():
    man = json.load(open(sys.argv[1]))
    out = os.path.expanduser(sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "~/tb_slim")
    done = made = 0
    full = small = 0
    for e in man["runs"]:
        src = os.path.join(os.path.expanduser(e["root"]), e["run_id"])
        dst = os.path.join(out, target(e["root"]), e["run_id"])
        side = os.path.join(dst, "thermbench.h5.slim")
        if os.path.exists(side) and json.load(open(side))["src_md5"] == e["h5_md5"]:
            done += 1
            continue
        if md5(os.path.join(src, "thermbench.h5")) != e["h5_md5"]:
            sys.exit(f"{src}: thermbench.h5 md5 differs from the manifest")
        os.makedirs(dst, exist_ok=True)
        for f in SIDE:
            if os.path.exists(os.path.join(src, f)):
                shutil.copy2(os.path.join(src, f), dst)
        slim(os.path.join(src, "thermbench.h5"), os.path.join(dst, "thermbench.h5"))
        json.dump({"src_md5": e["h5_md5"], "slim_md5": md5(os.path.join(dst, "thermbench.h5")), "kept": KEEP + ("metrics",)},
                  open(side, "w"))
        made += 1
        full += os.path.getsize(os.path.join(src, "thermbench.h5"))
        small += os.path.getsize(os.path.join(dst, "thermbench.h5"))
    print(f"{len(man['runs'])} runs: {made} slimmed now ({full / 1e9:.1f} -> {small / 1e9:.1f} GB), {done} already done; out {out}")


if __name__ == "__main__":
    main()
