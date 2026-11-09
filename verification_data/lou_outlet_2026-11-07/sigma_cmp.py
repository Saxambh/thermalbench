import json, glob, numpy as np
T_REF=846.0; TC,TH=293.15,333.15
d=json.load(open("fig15_333K_initial.json")); s=np.array(d["sigma"]); ri=np.array(d["Ri"])
o=np.vstack([np.loadtxt(f,comments="#") for f in sorted(glob.glob("ours_outletT_*.dat"))]); o=o[np.argsort(o[:,0])]
ot=o[:,0]/T_REF; oT=(o[:,1]-TC)/(TH-TC)
# ours: sigma = int (1 - T*out) dt*  (port energy balance, constant rho cp)
sig_o=np.concatenate([[0],np.cumsum(0.5*((1-oT[1:])+(1-oT[:-1]))*np.diff(ot))])
# Lou: T*out from slope of sigma, local linear fit over +-0.05 t*
def slope(t):
    m=(s[:,0]>t-0.05)&(s[:,0]<t+0.05); return np.polyfit(s[m,0],s[m,1],1)[0]
ri0=ri[(ri[:,0]>=0.2)&(ri[:,0]<=0.6),1].mean()
print("plateau slope of Lou sigma (t* 0.2-0.6):", round(np.polyfit(s[(s[:,0]>.2)&(s[:,0]<.6),0],s[(s[:,0]>.2)&(s[:,0]<.6),1],1)[0],3))
print(" t*   sigma_Lou sigma_ours | T*out: Lou(1-slope) Lou(Ri,const beta) ours")
for t in np.arange(0.3,1.501,0.05):
    sl=np.interp(t,s[:,0],s[:,1]); so=np.interp(t,ot,sig_o) if t<=ot.max() else np.nan
    tr=1-np.interp(t,ri[:,0],ri[:,1])/ri0; to=np.interp(t,ot,oT) if t<=ot.max() else np.nan
    print(f"{t:.2f}  {sl:.3f}     {so:.3f}      |  {1-slope(t):.3f}          {tr:.3f}           {to:.3f}")
