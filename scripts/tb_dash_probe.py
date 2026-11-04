"""ThermBench dashboard probe: status of this machine as one JSON object on stdout.
Run locally or over ssh (python3 - < tb_dash_probe.py); standard library only.
Batch lists per machine are listed in LISTS; runs moved to another machine (MOVED_TO_*
placeholders) are not counted on this one."""
import csv, glob, json, os, re, socket, subprocess, time

HOSTS = {"Saxam": "laptop", "DESKTOP-HK82PPA": "lab", "SoRrYnAh": "pc3", "GHLAB-SERVER": "pc4", "sure": "pc5"}
host = HOSTS.get(socket.gethostname(), socket.gethostname())
R = "/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench"
LISTS = {
    "laptop": [("Tank", "main", "run_id", f"{R}/design_v2_full_laptop_n2.csv", "~/of_runs/full_h5mm"),
               ("Tank", "extra", "run_id", f"{R}/design_v2_full_laptopx_n2.csv", "~/of_runs/full_h5mm_x"),
               ("PCM", "full", "case_id", "~/thermbench/pcm_full_laptop.csv", "~/of_runs/pcm_full/runs"),
               ("PCM", "from pc4", "case_id", "~/thermbench/pcm_more_laptop.csv", "~/of_runs/pcm_full/runs")],
    "lab": [("Tank", "main", "run_id", "~/thermbench/design_v2_full_lab_n2.csv", "~/of_runs/full_h5mm"),
            ("Tank", "extra", "run_id", "~/thermbench/design_v2_full_labx_n2.csv", "~/of_runs/full_h5mm_x"),
            ("Tank", "moved in", "run_id", "~/thermbench/design_v2_full_laby_n2.csv", "~/of_runs/full_h5mm_x"),
            ("Tank", "moved in 2", "run_id", "~/thermbench/design_v2_full_labz_n2.csv", "~/of_runs/full_h5mm_x"),
            ("PCM pilot", "", "case_id", "~/thermbench/scripts/pcm_pilot.csv", "~/of_runs/pcm_pilot"),
            ("PCM", "full", "case_id", "~/thermbench/pcm_full_lab.csv", "~/of_runs/pcm_full/runs"),
            ("PCM", "from pc4", "case_id", "~/thermbench/pcm_more_lab.csv", "~/of_runs/pcm_full/runs")],
    "pc3": [("Tank", "main", "run_id", "~/thermbench/design_v2_full_pc3_n2.csv", "~/of_runs/full_h5mm"),
            ("PCM", "full", "case_id", "~/thermbench/pcm_full_pc3.csv", "~/of_runs/pcm_full/runs"),
            ("PCM", "from pc4", "case_id", "~/thermbench/pcm_more_pc3.csv", "~/of_runs/pcm_full/runs")],
    "pc4": [("PCM", "full", "case_id", "~/thermbench/pcm_full_pc4.csv", "~/of_runs/pcm_full/runs")],
    # pc5 (friend's PC, 2026-11-04): pc4 cases moved by pcm_rebalance.py, solver in the ofbox container
    "pc5": [("PCM", "from pc4", "case_id", "~/thermbench/pcm_more_pc5.csv", "~/of_runs/pcm_full/runs")],
}
ex = os.path.expanduser


def tail(path, n=6000):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2); f.seek(max(0, f.tell() - n)); return f.read().decode(errors="ignore")
    except OSError:
        return ""


def failures(d, family):
    if family.startswith("PCM"):
        return tail(f"{d}/batch.log", 200000).count("FAIL")
    n = 0
    try:
        for row in csv.reader(open(f"{d}/batch_status.csv")):
            if len(row) > 1 and ("fail" in row[1] or row[1] == "incomplete"):
                n += 1
    except OSError:
        pass
    return n


lists = []
for fam, name, col, f, d in LISTS.get(host, []):
    f, d = ex(f), ex(d)
    if not os.path.exists(f):
        continue
    ids = [r[col] for r in csv.DictReader(open(f))]
    done = moved = 0
    for i in ids:
        if os.path.exists(f"{d}/{i}/DONE"):
            if glob.glob(f"{d}/{i}/MOVED*"):
                moved += 1
            else:
                done += 1
    total = len(ids) - moved
    if total:
        lists.append({"family": fam, "name": name, "done": done, "total": total, "failed": failures(d, fam)})

cases = {}
for pid in subprocess.run(["pgrep", "-f", "buoyantPimpleFoam"], capture_output=True, text=True).stdout.split():
    try:
        if not open(f"/proc/{pid}/comm").read().startswith("buoyantPimple"):
            continue
        cwd = os.readlink(f"/proc/{pid}/cwd")
        if not os.path.exists(f"{cwd}/system/controlDict"):
            continue
        et = int(subprocess.run(["ps", "-o", "etimes=", "-p", pid], capture_output=True, text=True).stdout.strip() or 0)
    except (OSError, ValueError):
        continue
    c = cases.setdefault(cwd, {"np": 0, "et": et}); c["np"] += 1; c["et"] = max(c["et"], et)
runs = []
for case, c in cases.items():
    kind = "PCM" if "pcm" in case else "3D" if "lou3d" in case else "Tank"
    t = re.findall(r"^Time = ([0-9.eE+-]+)", tail(f"{case}/log.solver"), re.M)
    t = float(t[-1]) if t else 0.0
    if kind == "PCM":
        lf = 0.0
        fs = sorted(glob.glob(f"{case}/postProcessing/liquidFraction/*/volFieldValue.dat"))
        if fs:
            rows = [l.split() for l in tail(fs[-1], 2000).splitlines() if l and not l.startswith("#")]
            if rows and len(rows[-1]) > 1:
                lf = float(rows[-1][1])
        frac, info = min(lf / 0.995, 1.0), f"melted {100 * lf:.1f} %, {t / 3600:.2f} h simulated"
    else:
        m = re.search(r"^endTime\s+([0-9.eE+-]+);", tail(f"{case}/system/controlDict", 100000), re.M)
        e = float(m.group(1)) if m else 0.0
        frac, info = (t / e if e else 0.0), f"{t:.0f} / {e:.0f} s simulated"
    runs.append({"kind": kind, "batch": os.path.basename(os.path.dirname(case)), "name": os.path.basename(case),
                 "np": c["np"], "frac": round(frac, 4), "elapsed_h": round(c["et"] / 3600, 2),
                 "left_h": round(c["et"] * (1 - frac) / frac / 3600, 1) if frac > 0.01 else None, "info": info})
mem = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo") if l.split(":")[0] in ("MemTotal", "MemAvailable")}
print(json.dumps({"host": host, "time": time.time(), "load": os.getloadavg()[0], "threads": os.cpu_count(),
                  "mem_total_gb": round(mem["MemTotal"] / 1048576, 1), "mem_avail_gb": round(mem["MemAvailable"] / 1048576, 1),
                  "uptime_h": round(float(open("/proc/uptime").read().split()[0]) / 3600, 1), "lists": lists, "runs": runs}))
