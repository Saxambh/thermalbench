import csv, numpy as np
r = list(csv.DictReader(open("/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/design_v2_full.csv")))
cases = {x["case_id"]: x for x in r}
v = lambda k: np.array([float(c[k]) for c in cases.values()])
print("cases", len(cases), "H unique", set(c["H"] for c in cases.values()))
for k in ("Re", "Ri", "W", "AR", "u_in"):
    a = v(k); print(k, "min %.4g q10 %.4g q90 %.4g max %.4g" % (a.min(), *np.quantile(a, [.1, .9]), a.max()))
print("turb", {t: sum(x["turb"] == t for x in r) for t in set(x["turb"] for x in r)})
