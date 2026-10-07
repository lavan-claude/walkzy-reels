#!/usr/bin/env python3
"""Synthetischer Beat fuer Reels: Kick, Hi-Hat, Bass, Akkord-Pad, Riser. 
Aufruf: python3 tools/make_beat.py out.wav DAUER [wendepunkt_sek] [bpm]
Vor dem Wendepunkt: ruhig (Pad + Hi-Hat), danach voller Beat. Selbst erzeugt, keine Lizenzfragen."""
import sys, numpy as np, wave
out=sys.argv[1]; D=float(sys.argv[2]); T=float(sys.argv[3]) if len(sys.argv)>3 else 6.4; bpm=float(sys.argv[4]) if len(sys.argv)>4 else 100
sr=44100; n=int(D*sr); t=np.arange(n)/sr; mix=np.zeros(n); rng=np.random.default_rng(7)
beat=60/bpm
def add(sig,at,g=1.0):
    i=int(at*sr)
    if i>=n: return
    j=min(n,i+len(sig)); mix[i:j]+=sig[:j-i]*g
def kick(): 
    x=np.arange(int(.35*sr))/sr; f=45+90*np.exp(-x*28); ph=2*np.pi*np.cumsum(f)/sr
    return np.sin(ph)*np.exp(-x*9)
def hat(o=False):
    x=np.arange(int((.22 if o else .06)*sr))/sr; nz=rng.standard_normal(len(x)); nz=np.diff(nz,prepend=0)
    return nz*np.exp(-x*(18 if o else 70))*.5
def clap():
    x=np.arange(int(.18*sr))/sr; return rng.standard_normal(len(x))*np.exp(-x*22)*.6
def bass(f,d):
    x=np.arange(int(d*sr))/sr; return (np.sin(2*np.pi*f*x)+.3*np.sin(4*np.pi*f*x))*np.minimum(1,x*60)*np.exp(-x*3.2)
def pad(freqs,d):
    x=np.arange(int(d*sr))/sr; s=sum(np.sin(2*np.pi*f*x)+.5*np.sin(2*np.pi*f*1.004*x) for f in freqs)/len(freqs)
    env=np.minimum(1,x/0.6)*np.minimum(1,(d-x)/0.6); return s*env
# Akkorde Am - F - C - G (je 4 Schlaege)
chords=[(220,261.63,329.63,55),(174.61,220,261.63,43.65),(261.63,329.63,392,65.41),(196,246.94,293.66,49)]
bar=beat*4; k=0
while k*bar<D:
    c=chords[k%4]; add(pad(c[:3],bar+.3),k*bar,.16 if k*bar<T else .12); k+=1
# Beat ab Wendepunkt (auf naechsten Takt gerastert)
start=np.ceil(T/beat)*beat if T>0 else 0
b=0
while b*beat<D:
    at=b*beat; step=b%16
    if at<T:
        if b%2==0: add(hat(),at+beat/2,.35)
    if at>=T-1e-6 or at>=start:
        if at>=start:
            if b%4 in (0,): add(kick(),at,1.0)
            if b%4==2: add(clap(),at,.7)
            if b%4==3: add(kick(),at+beat/2,.7)
            add(hat(),at+beat/2,.55); add(hat(),at,.3)
            c=chords[(int(at//bar))%4]; add(bass(c[3],beat*.9),at,.55)
            if b%4==1: add(bass(c[3]*2,beat*.4),at+beat/2,.3)
    b+=1
# Riser + Impact am Wendepunkt
ri=int(max(0,T-1.6)*sr); rl=int(min(1.6,T)*sr)
if T>0 and rl>0:
    x=np.arange(rl)/sr; fr=300+2600*(x/1.6)**2; r=np.sin(2*np.pi*np.cumsum(fr)/sr)*0.5+rng.standard_normal(rl)*0.25
    mix[ri:ri+rl]+=r*(x/1.6)**2*.28
add(kick()*1.2,T,1.0); x=np.arange(int(.9*sr))/sr; add(rng.standard_normal(len(x))*np.exp(-x*5)*.35,T,1)
mix*=np.minimum(1,t/0.4)*np.minimum(1,(D-t)/1.2)
# weicher Limiter, Normalisierung auf ca. -3 dBFS
mix=np.tanh(mix*1.4); mix=mix/np.max(np.abs(mix))*0.7
st=np.stack([mix,np.roll(mix,40)*0.98],1)
w=wave.open(out,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st*32767).astype('<i2').tobytes()); w.close()
