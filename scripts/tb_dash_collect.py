"""ThermalStorageBench dashboard collector (runs on the laptop): every 60 s asks all four machines for
their status (tb_dash_probe.py, over ssh in parallel) and writes ~/tb_dash/status.json, with a
progress history (every 10 min) for the chart. Served by tb_dash.sh with tb_dash.html."""
import json, os, subprocess, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE = os.path.join(HERE, "tb_dash_probe.py")
OUT = os.path.expanduser("~/tb_dash"); os.makedirs(OUT, exist_ok=True)
HOSTS = {"laptop": None, "lab": "labpc", "pc3": "saxam@pc3", "pc4": "saxam@pc4", "pc5": "pc5"}
HIST = f"{OUT}/history.jsonl"
last = {}


def probe(name):
    cmd = ["python3", PROBE] if HOSTS[name] is None else \
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOSTS[name], "python3", "-"]
    try:
        p = subprocess.run(cmd, stdin=open(PROBE) if HOSTS[name] else subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=50)
        return name, {"ok": True, **json.loads(p.stdout)}
    except Exception as e:  # noqa: BLE001
        prev = last.get(name)
        return name, {"ok": False, "error": str(e)[:200], "last_ok": prev["time"] if prev else None,
                      **({k: prev[k] for k in ("lists", "threads")} if prev else {})}


t_hist = 0
while True:
    with ThreadPoolExecutor(len(HOSTS)) as ex:
        res = dict(ex.map(probe, HOSTS))
    for k, v in res.items():
        if v["ok"]:
            last[k] = v
    now = time.time()
    if now - t_hist >= 600 and all(k in last for k in HOSTS):
        tot = {}
        for v in last.values():
            for l in v["lists"]:
                fam = "PCM" if l["family"] == "PCM" else l["family"]
                tot[fam] = tot.get(fam, 0) + l["done"]
        with open(HIST, "a") as f:
            f.write(json.dumps({"t": now, **tot}) + "\n")
        t_hist = now
    hist = []
    if os.path.exists(HIST):
        hist = [json.loads(l) for l in open(HIST) if l.strip()][-1000:]
    tmp = f"{OUT}/status.json.tmp"
    json.dump({"updated": now, "hosts": res, "history": hist}, open(tmp, "w"))
    os.replace(tmp, f"{OUT}/status.json")
    time.sleep(max(5, 60 - (time.time() - now)))
