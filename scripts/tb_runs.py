"""List every running ThermBench simulation on this machine, one line each (used by tb_monitor.sh;
read from stdin over ssh, so it needs only python3). Also counts finished runs per batch folder."""
import glob, os, re, socket, subprocess, time

def tail(path, n=6000):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2); f.seek(max(0, f.tell() - n)); return f.read().decode(errors="ignore")
    except OSError:
        return ""

def end_time(case):
    m = re.search(r"^endTime\s+([0-9.eE+-]+);", tail(f"{case}/system/controlDict", 100000), re.M)
    return float(m.group(1)) if m else None

host = {"Saxam": "laptop", "DESKTOP-HK82PPA": "lab", "SoRrYnAh": "pc3", "GHLAB-SERVER": "pc4"}.get(socket.gethostname(), socket.gethostname())
cases = {}
for pid in subprocess.run(["pgrep", "-f", "buoyantPimpleFoam"], capture_output=True, text=True).stdout.split():
    try:
        if not open(f"/proc/{pid}/comm").read().startswith("buoyantPimple"):
            continue                      # skip mpirun and shell wrappers
        cwd = os.readlink(f"/proc/{pid}/cwd")
        if not os.path.exists(f"{cwd}/system/controlDict"):
            continue
        et = int(subprocess.run(["ps", "-o", "etimes=", "-p", pid], capture_output=True, text=True).stdout.strip() or 0)
    except (OSError, ValueError):
        continue
    c = cases.setdefault(cwd, {"np": 0, "et": et}); c["np"] += 1; c["et"] = max(c["et"], et)
now = time.time()
for case, c in sorted(cases.items()):
    name = os.path.basename(case); batch = os.path.basename(os.path.dirname(case))
    kind = "PCM" if "pcm" in case else "3D" if "lou3d" in case else "tank"
    t = [float(x) for x in re.findall(r"^Time = ([0-9.eE+-]+)", tail(f"{case}/log.solver"), re.M)]
    t = t[-1] if t else 0.0
    if kind == "PCM":
        f = sorted(glob.glob(f"{case}/postProcessing/liquidFraction/*/volFieldValue.dat"))
        lf = 0.0
        if f:
            rows = [l.split() for l in tail(f[-1], 2000).splitlines() if l and not l.startswith("#")]
            lf = float(rows[-1][1]) if rows and len(rows[-1]) > 1 else 0.0
        frac, info = min(lf / 0.995, 1.0), f"melted {100 * lf:5.1f} %, sim {t / 3600:5.2f} h"
    else:
        e = end_time(case) or 0
        frac, info = (t / e if e else 0.0), f"sim {t:7.0f} / {e:6.0f} s"
    eta = c["et"] * (1 - frac) / frac / 3600 if frac > 0.01 else None
    print(f"RUN|{host}|{kind}|{batch}/{name}|{c['np']}|{frac:.4f}|{c['et'] / 3600:.2f}|{'' if eta is None else f'{eta:.1f}'}|{info}")
for label, d in [("tank", "~/of_runs/full_h5mm"), ("tank extra", "~/of_runs/full_h5mm_x"),
                 ("PCM", "~/of_runs/pcm_full/runs"), ("PCM pilot", "~/of_runs/pcm_pilot")]:
    d = os.path.expanduser(d)
    if os.path.isdir(d):
        done = [p for p in glob.glob(f"{d}/*/DONE") if not glob.glob(f"{os.path.dirname(p)}/MOVED*")]
        print(f"DONE|{host}|{label}|{len(done)}")
print(f"HOST|{host}|{os.getloadavg()[0]:.1f}|{os.cpu_count()}")
