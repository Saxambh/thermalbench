import json, numpy as np
from scipy.optimize import brentq
Tc_, Td = np.array([20,25,30,35,40,45,50,55,60.]), np.array([2.07,2.57,3.03,3.45,3.85,4.22,4.58,4.91,5.23])
beta = lambda T: np.interp(T, Tc_, Td)
c = json.load(open("compare.json"))["rows"]
print("t*    T*_const  T*_beta(mean)  T*_beta(Tout)   ours")
for r in c:
    if r["lou"] is None: continue
    ratio = 1 - r["lou"]                       # Ri/Ri0 as digitised
    out = []
    for f in (lambda To: beta((60+To)/2), lambda To: beta(To)):
        g = lambda To: f(To)*(60-To) / (f(20)*40) - ratio
        To = brentq(g, 19.99, 60) if g(19.99) * g(60) < 0 else 20
        out.append((To-20)/40)
    print(f"{r['t_star']:.2f}  {r['lou']:.3f}     {out[0]:.3f}          {out[1]:.3f}          {'' if r['ours'] is None else format(r['ours'],'.3f')}")
