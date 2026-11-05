#!/usr/bin/env python3
"""PCM tail manager (2026-11-05, Saxam: "yes do 1 and 2" for speeding up the PCM campaign).

The campaign's finish date is set by its slowest ~20 cases (serial, on machines with more solvers
than physical cores), not by the total work. Runs on each PCM machine, every 10 minutes:

1. Priority. Running cases are ranked by estimated hours left, from the recent rate of the melted
   fraction (the stopAtMelt line in the solver log; cases stop at 0.995). The longest cases, up to
   the physical cores not used by GPU training or other CFD, keep their priority (nice 5, as
   started); a case outside them with less than 24 h left and at least half melted (earlier
   estimates are too optimistic, melting slows down) is lowered to nice 15. Numerics and
   results are unchanged; only the CPU share moves to the cases that set the end date. A lowered
   case cannot be raised again without root, so only clearly short cases are lowered.
2. Parallel restart. When at least 3 physical cores are idle, the longest serial case with more
   than 36 h left is moved to np = min(4, idle + 1) cores in place: wait for its next regular
   write (no extra snapshot times), stop the solver (its batch logs SOLVER_FAIL for the stop and
   goes on), then pcm_continue.sh <case> <np> carries on from that time and exports, slims and
   writes DONE as the batch would. Decomposition changes nothing but round-off; the restart path
   was tested on 2026-11-05 (melted fraction within 0.0003 of an uninterrupted run).
   One switch at a time per machine. A reboot is safe: tb_resume restarts the batch, which resumes
   the case on one core.

  setsid nohup python3 pcm_tail.py loop > /dev/null 2>&1 < /dev/null &
  python3 pcm_tail.py status            print the table, change nothing
Log: ~/of_runs/pcm_full/tail.log
"""
import os, re, signal, subprocess, sys, time

RUNS = os.path.expanduser("~/of_runs/pcm_full/runs")
LOG = os.path.expanduser("~/of_runs/pcm_full/tail.log")
SCR = os.path.dirname(os.path.abspath(__file__))
LOW_NICE, SHORT_H, LONG_H, MAX_NP = 15, 24.0, 36.0, 4
TIME = re.compile(r"^[0-9][0-9.e+-]*$")


def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M ", time.gmtime()) + msg + "\n")


def phys_cores():
    out = subprocess.run(["lscpu"], capture_output=True, text=True).stdout
    g = lambda k: int(re.search(rf"^{k}:\s+(\d+)", out, re.M).group(1))
    return g(r"Core\(s\) per socket") * g(r"Socket\(s\)")


def procs():
    """(pid, comm, state, nice, cwd, cmdline) for every process we can read."""
    out = []
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            st = open(f"/proc/{p}/stat").read()
            comm = st[st.index("(") + 1:st.rindex(")")]
            f = st[st.rindex(")") + 2:].split()
            cwd = os.readlink(f"/proc/{p}/cwd")
            cmd = open(f"/proc/{p}/cmdline").read().replace("\0", " ")
            out.append((int(p), comm, f[0], int(f[16]), cwd, cmd))
        except (OSError, ValueError):
            pass
    return out


def tail_log(c):
    """Recent progress of a case: (t, endTime, melted, h_left, h_left_from_endTime)."""
    logs = [os.path.join(c, n) for n in ("log.solver.cont", "log.solver") if os.path.exists(os.path.join(c, n))]
    if not logs:
        return None
    lg = max(logs, key=os.path.getmtime)
    with open(lg, "rb") as f:
        f.seek(max(0, os.path.getsize(lg) - 3_000_000))
        txt = f.read().decode(errors="replace")
    pts, t, a = [], None, None
    for line in txt.splitlines():
        if line.startswith("Time = "):
            t = float(line.split()[2])
        elif "volAverage(pcm,melting:alpha1)" in line and "value =" in line:
            a = float(line.split("value =")[1].split(",")[0])
        elif line.startswith("ExecutionTime") and t is not None and a is not None:
            pts.append((float(line.split()[2]), t, a))
    try:
        end = float(re.search(r"^endTime\s+([0-9.e+-]+);", open(os.path.join(c, "system/controlDict")).read(), re.M).group(1))
    except (OSError, AttributeError):
        end = None
    if len(pts) < 20:
        return None
    x1, t1, a1 = pts[-1]
    x0, t0, a0 = pts[max(0, len(pts) - 3000)]
    if x1 - x0 < 300:
        return None
    ra, rt = (a1 - a0) / (x1 - x0), (t1 - t0) / (x1 - x0)
    left_a = (0.995 - a1) / ra / 3600 if ra > 0 else 1e4
    left_t = (end - t1) / rt / 3600 if end and rt > 0 else 1e4
    return t1, end, a1, min(left_a, left_t), left_t


def cases():
    """Running PCM cases on this machine: {case_dir: [pids]} and the cores used by other work."""
    run, other = {}, 0
    for pid, comm, state, nice, cwd, cmd in procs():
        if state == "T":                                   # paused (lab pilots)
            continue
        if comm.startswith("buoyantPimple"):
            if cwd.startswith(RUNS + "/") and cwd.count("/") == RUNS.count("/") + 1:
                run.setdefault(cwd, []).append((pid, nice, "-parallel" in cmd))
            else:
                other += 1                                 # other CFD (lab 3D, pilots)
        elif "train.py" in cmd and "python" in comm:
            other += 2                                     # GPU training: the process and its data threads
    return run, other


def status(act=False):
    run, other = cases()
    cores = phys_cores()
    rows = []
    for c, ps in run.items():
        s = tail_log(c)
        rows.append((s[3] if s else 1e4, c, ps, s))
    rows.sort(key=lambda r: -r[0])
    budget, used = cores - other, 0
    for left, c, ps, s in rows:
        used += len(ps)
        keep = used <= budget
        nice = min(n for _, n, _ in ps)
        tag = "keep" if keep or left >= SHORT_H or not s or s[2] < 0.5 else ("low" if nice >= LOW_NICE else "lower")
        if not act:
            print(f"{os.path.basename(c):7s} {len(ps)} proc nice {nice:2d}  "
                  + (f"t {s[0]:7.0f}/{s[1]:.0f}  melted {s[2]:.3f}  ~{left:6.1f} h left" if s else "no rate yet") + f"  {tag}")
        elif tag == "lower" and s:
            for pid, _, _ in ps:
                try:
                    os.setpriority(os.PRIO_PROCESS, pid, LOW_NICE)
                except OSError:
                    pass
            log(f"{os.path.basename(c)} lowered to nice {LOW_NICE} (~{left:.1f} h left, melted {s[2]:.3f})")
    procs_n = sum(len(ps) for _, _, ps, _ in rows)
    idle = cores - other - procs_n
    if not act:
        print(f"{cores} physical cores, {other} used by other work, {procs_n} PCM solver processes, idle {idle}")
        return
    pending = [p for p in procs() if "pcm_tail.py switch" in p[5]]   # a switch still waiting or running
    if idle >= 3 and not pending:
        cand = [(left, c, ps) for left, c, ps, s in rows
                if s and left > LONG_H and len(ps) == 1 and not ps[0][2]]   # a lowered case restarts at nice 5
        if cand:
            left, c, ps = cand[0]
            np_ = min(MAX_NP, idle + 1)
            open(os.path.join(c, "TAIL_SWITCH"), "w").write(f"{np_}\n")
            subprocess.Popen(["setsid", "nohup", sys.executable, os.path.abspath(__file__), "switch", c, str(np_), str(ps[0][0])],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
            log(f"{os.path.basename(c)}: {idle} cores idle, moving it to {np_} cores (~{left:.1f} h left on one)")


def complete(d):
    for f in ("T", "U", "p_rgh", "melting:alpha1", "phi"):
        p = os.path.join(d, f)
        try:
            if os.path.getsize(p) == 0:
                return False
            with open(p, "rb") as fh:
                fh.seek(max(0, os.path.getsize(p) - 200))
                if b"\n// ***" not in fh.read():
                    return False
        except OSError:
            return False
    return True


def switch(c, np_, pid):
    name = os.path.basename(c)
    times = lambda: sorted((x for x in os.listdir(c) if TIME.match(x)), key=float)
    start = times()[-1]
    t_wait = time.time()
    while True:                                    # the next regular write, complete on disk
        if not os.path.exists(f"/proc/{pid}"):
            log(f"{name}: solver ended before its next write (finished?), no switch")
            os.remove(os.path.join(c, "TAIL_SWITCH"))
            return
        new = [x for x in times() if float(x) > float(start)]
        if new and complete(os.path.join(c, new[-1])):
            break
        if time.time() - t_wait > 12 * 3600:
            log(f"{name}: no new write in 12 h, switch dropped")
            os.remove(os.path.join(c, "TAIL_SWITCH"))
            return
        time.sleep(20)
    os.kill(pid, signal.SIGTERM)
    for _ in range(60):
        if not os.path.exists(f"/proc/{pid}"):
            break
        time.sleep(1)
    else:
        os.kill(pid, signal.SIGKILL)
        time.sleep(5)
    with open(os.path.join(RUNS, "batch.log"), "a") as f:
        f.write(f"{name} SWITCHED to {np_} cores by pcm_tail.py at t = {new[-1]} (the SOLVER_FAIL line for it is this planned stop)\n")
    log(f"{name}: stopped after its write at t = {new[-1]}, continuing on {np_} cores")
    rc = subprocess.run(["bash", os.path.join(SCR, "pcm_continue.sh"), c, str(np_)]).returncode
    log(f"{name}: parallel continuation ended, exit {rc}" + (" (DONE)" if os.path.exists(os.path.join(c, "DONE")) else ""))
    os.remove(os.path.join(c, "TAIL_SWITCH"))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        status(False)
    elif cmd == "switch":
        switch(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == "loop":
        log(f"pcm_tail started on {os.uname().nodename}, pid {os.getpid()}")
        while True:
            try:
                status(True)
            except Exception as e:                 # keep going; the next pass retries
                log(f"pass failed: {e!r}")
            time.sleep(600)
