import h5py, numpy as np, os, json
V = os.path.expanduser("~/tb_verify")
for rid, alt in (("T0211_sst", "v2/T0211_sst_n4"), ("T0052_sst", "reg/T0052_sst_n4"), ("T0156_sst", "reg/T0156_sst_n4")):
    with h5py.File(f"{V}/ds/{rid}/thermbench.h5") as a, h5py.File(f"{V}/{alt}/thermbench.h5") as b:
        Ta, ta, Tb, tb = a["fields/T"][:], a["times_s"][:], b["fields/T"][:], b["times_s"][:]
        cj = json.loads(a.attrs["case_json"]) if "case_json" in a.attrs else None
    dT = abs(Ta.max() - Ta.min())
    sel = [i for i, t in enumerate(ta) if t > 0 and tb[0] <= t <= tb[-1]]
    d = []
    for i in sel:
        j = min(max(int(np.searchsorted(tb, ta[i])), 1), len(tb) - 1); w = (ta[i] - tb[j-1]) / (tb[j] - tb[j-1])
        d.append(((1 - w) * Tb[j-1] + w * Tb[j]) - Ta[i])
    d = np.array(d) / dT
    print(rid, f"pooled RMS {100*np.sqrt((d**2).mean()):.2f} %  mean of per-snapshot RMS {100*np.sqrt((d**2).mean((1,2))).mean():.2f} %  (dT from field range {dT:.2f} K, n {len(sel)})")
