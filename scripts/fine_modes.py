import csv, collections
r = list(csv.DictReader(open("/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/design_v2_fine128.csv")))
print(list(r[0].keys()))
c = collections.Counter((x.get("mode"), x.get("inlet_type")) for x in r); print(c)
f = list(csv.DictReader(open("/mnt/d/Lund PhD Application/04_Publications/Research_Paper_RP4_ThermBench/design_v2_full.csv")))
print(collections.Counter(x.get("mode") for x in f), len(f))
