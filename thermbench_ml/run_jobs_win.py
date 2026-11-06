"""Windows job runner for training on a machine without bash (2026-11-06: the Lund workstation, RTX 4500 Ada,
approved by Jouri Kanters: Python from python.org + PyTorch from pytorch.org in one folder on D:, no admin, no
system changes). Does what run_final.sh does per job: skip jobs whose result is already in results/<split>.json,
otherwise run train.py with the same common options, appending its output to results/run_final.log.

  python run_jobs_win.py <jobs file> <data folder>          e.g.  python run_jobs_win.py jobs_lund.txt D:\\SaxamML\\tb_data
  jobs file lines: "<model> <split> <seed> <epochs> [flags]", e.g. "fno random 1 60 --hybrid --canon"
Stop: close the window (the running job is lost, finished ones are kept); start again to continue.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = "manifest_full_h5mm.json"
SUB = ["laptop/full_h5mm", "laptop/full_h5mm_x", "lab/full_h5mm", "lab/full_h5mm_x", "pc3/full_h5mm"]   # as data.DEFAULT_ROOTS


def name(model, seed, flags):
    return model + ("_hybrid" if "hybrid" in flags else "") + ("_canon" if "canon" in flags else "") + (f"_s{seed}" if seed != "0" else "")


def done(split, n):
    try:
        return n in json.load(open(os.path.join(HERE, "results", f"{split}.json")))["results"]
    except (OSError, ValueError, KeyError):
        return False


def main():
    jobs_file, data = sys.argv[1], sys.argv[2]
    roots = [os.path.join(data, s) for s in SUB if os.path.isdir(os.path.join(data, s))]
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    log = open(os.path.join(HERE, "results", "run_final.log"), "a", buffering=1)
    say = lambda m: (print(m, flush=True), log.write(m + "\n"))
    say(f"=== run_jobs_win {time.strftime('%Y-%m-%d %H:%M', time.gmtime())} UTC on {os.environ.get('COMPUTERNAME', '?')}, "
        f"{len(roots)} data folders")
    chk = subprocess.run([sys.executable, "check_data.py", MANIFEST], cwd=HERE, capture_output=True, text=True,
                         env={**os.environ, "TB_ROOTS": os.pathsep.join(roots)})
    say(chk.stdout.strip() or chk.stderr.strip())
    if chk.returncode != 0:
        say("data check failed: not all frozen runs are here and intact")
        sys.exit(1)
    jobs = [l.split(None, 4) for l in open(jobs_file) if l.strip()]
    for j in jobs:
        model, split, seed, ep = j[:4]
        flags = j[4].split() if len(j) > 4 else []
        n = name(model, seed, " ".join(flags))
        if done(split, n):
            say(f"--- {split}: {n} already done, skipped")
            continue
        say(f"--- {split}: {model} {' '.join(flags)} seed {seed} ({ep} epochs) {time.strftime('%H:%M', time.gmtime())}")
        cmd = [sys.executable, "train.py", "--model", model, *flags, "--split", split, "--seed", seed, "--epochs", ep,
               "--manifest", MANIFEST, "--gpu-data", "--amp", "--batch", "16", "--threads", "2",
               "--outdir", "results", "--roots", *roots]
        p = subprocess.Popen(cmd, cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            ep_line = line.startswith("epoch") and not line.split()[1].endswith("0")
            if not ep_line:
                say(line.rstrip())
        if p.wait() != 0:
            say(f"!!! {split}: {n} failed, exit {p.returncode}")
    say(f"=== worker lund done {time.strftime('%Y-%m-%d %H:%M', time.gmtime())} UTC")


if __name__ == "__main__":
    main()
