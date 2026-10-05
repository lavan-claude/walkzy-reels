#!/usr/bin/env python3
"""Erzeugt eigene, lizenzfreie Hintergrundmusik (ruhiger, filmischer Pad-Sound mit Puls und Riser). Aufruf: make_music.py out.wav dauer_sek [riser_bei] [impact_bei]"""
import sys, numpy as np, wave
sr=44100; D=float(sys.argv[2]); riser=float(sys.argv[3]) if len(sys.argv)>3 else None; imp=float(sys.argv[4]) if len(sys.argv)>4 else None
t=np.arange(int(sr*D))/sr; rng=np.random.default_rng(7)
def lp(x,fc):
    a=np.exp(-2*np.pi*fc/sr); y=np.zeros_like(x); s=0.0
    for i in range(len(x)): s=(1-a)*x[i]+a*s; y[i]=s
    return y
chords=[[55.0,110.0,164.81,220.0],[43.65,87.31,130.81,174.61],[65.41,130.81,196.0,261.63],[49.0,98.0,146.83,196.0]]  # Am F C G
seg=D/len(chords); out=np.zeros_like(t)
for ci,ch in enumerate(chords):
    t0=ci*seg; m=(t>=t0)&(t<t0+seg+1.2); tt=t[m]-t0
    env=np.minimum(1,tt/1.6)*np.exp(-np.maximum(0,tt-seg)*2.0)
    sig=np.zeros_like(tt)
    for f in ch:
        for det in (-0.004,0,0.004):
            ff=f*(1+det); sig+=2*((tt*ff)%1)-1
    out[m]+=sig*env/ (len(ch)*3)
out=lp(out,900)*1.8
# sub-puls
beat=60/72; k=np.zeros_like(t)
for b in np.arange(0,D,beat*2):
    i=int(b*sr); n=int(0.5*sr)
    if i+n<len(t):
        tt=np.arange(n)/sr; k[i:i+n]+=np.sin(2*np.pi*(46+60*np.exp(-tt*18))*tt)*np.exp(-tt*7)*0.55
out+=k
if riser is not None:
    r0=max(0,riser-2.5); m=(t>=r0)&(t<riser); tt=(t[m]-r0)/(riser-r0)
    n=lp(rng.standard_normal(m.sum()),3500); out[m]+=n*tt**2*0.35
if imp is not None:
    i=int(imp*sr); n=int(2.2*sr); tt=np.arange(n)/sr
    if i+n>len(t): n=len(t)-i; tt=tt[:n]
    out[i:i+n]+=np.sin(2*np.pi*(38+120*np.exp(-tt*10))*tt)*np.exp(-tt*2.2)*0.9
# einfacher Hall
for dl,g in ((0.23,0.35),(0.41,0.25),(0.67,0.18)):
    d=int(dl*sr); o=out.copy(); o[d:]+=out[:-d]*g; out=o
fade=np.minimum(1,np.minimum(t/0.8,(D-t)/1.5)); out*=fade
out=out/np.max(np.abs(out))*0.85
st=np.stack([out,np.roll(out,int(0.012*sr))],1)
with wave.open(sys.argv[1],"w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st*32767).astype(np.int16).tobytes())
