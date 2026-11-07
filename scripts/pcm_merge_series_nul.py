"""NUL-tolerant version of the postProcessing merge in pcm_continue.sh (2026-11-07).
P0095, P0280 and P0316 finished solving, but pcm_continue.sh's merge stopped on series files holding NUL
bytes from an interrupted write, so the export failed. Same rule as pcm_repair_series.py: rows sorted by
time, a later restart folder wins from its start time on, NUL bytes removed, malformed lines (first token not
a number, or a token count different from the file's usual count) dropped. The merged series is written into
the first folder and the later folders are removed, as pcm_continue.sh does. Back up postProcessing first.
    pcm_merge_series_nul.py <case_dir>"""
import os, re, sys, shutil
from collections import Counter
num = re.compile(r"^[0-9][0-9.e+-]*$")
pp = os.path.join(os.path.abspath(sys.argv[1]), "postProcessing")
for fo in sorted(os.listdir(pp)):
    d = os.path.join(pp, fo)
    subs = sorted((s for s in os.listdir(d) if num.match(s)), key=float)
    if not subs:
        continue   # one folder is still cleaned (P0280, P0316: merged before the crash, one bad row left)
    names = sorted({f for s in subs for f in os.listdir(os.path.join(d, s))})
    for fn in names:
        header, rows, bad, lines_all = [], {}, 0, []
        for k, s in enumerate(subs):
            f = os.path.join(d, s, fn)
            if not os.path.exists(f):
                continue
            start = float(s); nxt = float(subs[k + 1]) if k + 1 < len(subs) else float("inf")
            for l in open(f, "rb").read().replace(b"\0", b"").decode("ascii", "ignore").splitlines():
                if l.startswith("#"):
                    if k == 0: header.append(l)
                    continue
                if l.strip():
                    lines_all.append((start, nxt, l))
        ntok = Counter(len(l.split()) for _, _, l in lines_all).most_common(1)[0][0]
        for start, nxt, l in lines_all:
            p = l.split()
            try:
                t = float(p[0])
            except ValueError:
                bad += 1; continue
            if len(p) != ntok:
                bad += 1; continue
            if not (start - 1e-9 <= t < nxt):
                continue
            rows.setdefault(t, []).append(l) if fo == "wallHeat" else rows.__setitem__(t, [l])
        out = header + [l for t in sorted(rows) for l in rows[t]]
        os.makedirs(os.path.join(d, subs[0]), exist_ok=True)
        open(os.path.join(d, subs[0], fn), "w").write("\n".join(out) + "\n")
        print(f"{fo}/{fn}: {len(subs)} folders -> {len(out) - len(header)} rows, {bad} malformed dropped, "
              f"t {min(rows):g} to {max(rows):g}")
    for s in subs[1:]:
        shutil.rmtree(os.path.join(d, s))
