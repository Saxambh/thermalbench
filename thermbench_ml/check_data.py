"""Check that every run of a frozen manifest is present on this machine and intact (thermbench.h5
md5 as recorded at freeze time). Run by run_final.sh before training on each GPU machine.
  python3 check_data.py manifest_full_h5mm.json | manifest_pcm.json"""
import glob, hashlib, json, os, sys
ROOTS = ["~/of_runs/full_h5mm", "~/of_runs/full_h5mm_x", "~/tb_data/laptop/full_h5mm", "~/tb_data/laptop/full_h5mm_x",
         "~/tb_data/lab/full_h5mm", "~/tb_data/lab/full_h5mm_x", "~/tb_data/pc3/full_h5mm"]   # as data.DEFAULT_ROOTS
PCM_ROOTS = ["~/of_runs/pcm_full/runs", "~/tb_data/laptop/pcm_full", "~/tb_data/lab/pcm_full", "~/tb_data/pc3/pcm_full",
             "~/tb_data/pc4/pcm_full", "~/tb_data/pc5/pcm_full", "~/tb_data/pc6/pcm_full"]   # as pcm_data.DEFAULT_ROOTS
m = json.load(open(sys.argv[1]))
if m.get("family") == "pcm":   # PCM manifest (pcm_freeze_manifest.py)
    ROOTS = PCM_ROOTS
where = {}
for root in ROOTS:   # first root wins, as data.index
    for done in glob.glob(os.path.join(os.path.expanduser(root), "*", "DONE")):
        p = os.path.dirname(done)
        rid = os.path.basename(p)
        if rid not in where and not glob.glob(f"{p}/MOVED_TO_*") and os.path.exists(f"{p}/thermbench.h5"):
            where[rid] = p
missing, bad, n_slim = [], [], 0
for e in m["runs"]:
    p = where.get(e["run_id"])
    if p is None:
        missing.append(e["run_id"]); continue
    h = hashlib.md5()
    with open(f"{p}/thermbench.h5", "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    if h.hexdigest() != e["h5_md5"]:
        # a temperature-only copy (make_slim.py, pc5) passes if it comes from the frozen file and is itself intact
        side = f"{p}/thermbench.h5.slim"
        s = json.load(open(side)) if os.path.exists(side) else {}
        if s.get("src_md5") == e["h5_md5"] and s.get("slim_md5") == h.hexdigest():
            n_slim += 1
        else:
            bad.append(e["run_id"])
print(f"{len(m['runs'])} manifest runs: {len(m['runs']) - len(missing) - len(bad)} present and intact, "
      f"{len(missing)} missing {missing[:8]}, {len(bad)} differ {bad[:8]}" + (f" ({n_slim} temperature-only copies)" if n_slim else ""))
sys.exit(1 if missing or bad else 0)
