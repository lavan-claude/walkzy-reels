#!/usr/bin/env python3
"""Baut ein Instagram-Karussell (1080x1350 PNG) aus einer JSON-Datei.
Aufruf: python3 tools/make_carousel.py reels/2026-10-05.json
JSON: {"date","theme":1-4,"cover":{"big","unit","sub"},"slides":[{"kind":"stake|idea|recap|cta","tag","h","s","items"}]}
Ausgabe: reels/<date>/slide1.png ... slideN.png"""
import json, os, sys
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); FD=os.path.join(HERE,"fonts")
FF=f"""@font-face{{font-family:'SG';font-weight:700;src:url('file://{FD}/space-grotesk-latin-700-normal.woff2')}}
@font-face{{font-family:'FR';font-weight:800;src:url('file://{FD}/fraunces-latin-800-normal.woff2')}}
@font-face{{font-family:'IN';font-weight:600;src:url('file://{FD}/inter-latin-600-normal.woff2')}}
@font-face{{font-family:'IN';font-weight:400;src:url('file://{FD}/inter-latin-400-normal.woff2')}}
*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:'IN'}}
.lab{{position:absolute;font-size:30px;font-weight:600;letter-spacing:.08em;text-transform:uppercase}}
"""
TH={1:dict(bg="#e6ff3d",ink="#0a0a0a",mut="#3a3d1a",ac="#0a0a0a",rule="#0a0a0a33"),
    2:dict(bg="#07090d",ink="#ffffff",mut="#9aa5b3",ac="#2d5bff",rule="#2a3342"),
    3:dict(bg="#ff4a1c",ink="#fff4e6",mut="#ffe0cf",ac="#fff4e6",rule="#fff4e655"),
    4:dict(bg="#efe8da",ink="#111111",mut="#5b564b",ac="#1b3cff",rule="#11111133")}
def esc(t): return t.replace("&","&amp;").replace("<","&lt;")
def chrome(c,i,n,last):
    return (f"<div class=lab style='left:80px;top:80px;color:{c['mut']}'>Walkzy · Webseiten &amp; KI</div>"
            f"<div class=lab style='right:80px;top:80px;color:{c['mut']}'>{i:02d}/{n:02d}</div>"
            f"<div class=lab style='left:80px;bottom:80px;color:{c['mut']}'>walkzy.de</div>"
            f"<div class=lab style='right:80px;bottom:80px;color:{c['mut']}'>{'Speichern' if last else 'Wischen →'}</div>")
def cover(t,cv,n):
    c=TH[t]; big=esc(cv['big']); unit=esc(cv.get('unit','')); sub=esc(cv['sub'])
    sc=min(1,4/max(len(cv['big']),1))
    if t==2: sc=min(1,1.1/max(len(cv['big']),1))
    h=chrome(c,1,n,False); css=f"body{{background:{c['bg']};color:{c['ink']}}}"
    if t==1:
        h+=f"<div class=big>{big}</div><div class=sub>{sub}</div>"
        css+=f".big{{position:absolute;left:20px;top:330px;font-family:'SG';font-weight:700;font-size:{int(520*sc)}px;line-height:1;letter-spacing:-.06em;white-space:nowrap}}.sub{{position:absolute;left:80px;top:900px;font-size:58px;font-weight:600;max-width:820px;line-height:1.15}}"
    elif t==2:
        h+=f"<div class=big>{big}</div><div class=txt>{unit}<small>{sub}</small></div>"
        css+=f".big{{position:absolute;right:{-90 if len(cv['big'])<2 else 40}px;top:{-120 if len(cv['big'])<2 else 130}px;font-family:'SG';font-weight:700;font-size:{int(1300*sc)}px;line-height:1;color:{c['ac']};letter-spacing:-.05em;white-space:nowrap}}.txt{{position:absolute;left:80px;bottom:240px;font-family:'SG';font-weight:700;font-size:130px;line-height:1;letter-spacing:-.03em;max-width:900px}}small{{display:block;font-family:'IN';font-weight:600;font-size:50px;letter-spacing:0;margin-top:34px;color:#cfd6df}}"
    elif t==3:
        h+=(f"<svg width=760 height=760 style='position:absolute;left:160px;top:230px' viewBox='0 0 760 760'><circle cx=380 cy=380 r=340 fill=none stroke='#fff4e6' stroke-width=14 opacity=.35 /><circle cx=380 cy=380 r=340 fill=none stroke='#fff4e6' stroke-width=14 stroke-dasharray='640 2137' transform='rotate(-90 380 380)' stroke-linecap=round /></svg>"
            f"<div class=big>{big}</div><div class=sub>{unit}<span>{sub}</span></div>")
        css+=f".big{{position:absolute;left:0;right:0;top:300px;text-align:center;font-family:'FR';font-weight:800;font-size:{int(660*sc)}px;line-height:1;white-space:nowrap}}.sub{{position:absolute;left:80px;bottom:200px;font-family:'FR';font-weight:800;font-size:96px;line-height:1.02;max-width:900px}}.sub span{{font-family:'IN';font-weight:600;font-size:46px;display:block;margin-top:24px}}"
    else:
        h+=f"<div class=row><div>{big}</div><div class=u>{unit}</div></div><div class=bar></div><div class=sub>{sub}</div>"
        css+=f".row{{position:absolute;left:70px;top:260px;display:flex;align-items:flex-end;gap:30px;font-family:'SG';font-weight:700;font-size:{int(700*sc)}px;line-height:.85;letter-spacing:-.06em;white-space:nowrap}}.u{{font-size:150px;letter-spacing:-.02em;color:{c['ac']};padding-bottom:30px}}.bar{{position:absolute;left:80px;right:80px;top:880px;height:26px;background:#111}}.bar:after{{content:'';position:absolute;left:0;top:0;height:26px;width:34%;background:{c['ac']}}}.sub{{position:absolute;left:80px;top:960px;font-size:52px;font-weight:600;line-height:1.2;max-width:900px}}"
    return h,css
def inner(t,sl,i,n):
    c=TH[t]; last=(i==n); k=sl['kind']
    h=chrome(c,i,n,last); css=f"body{{background:{c['bg']};color:{c['ink']}}}.main{{position:absolute;left:80px;right:140px;top:250px;bottom:250px;display:flex;flex-direction:column;justify-content:center}}h1{{font-family:'SG';font-weight:700;font-size:118px;line-height:1.02;letter-spacing:-.03em}}p{{font-size:50px;line-height:1.3;color:{c['mut']};margin-top:44px;font-weight:400}}.tag{{font-size:34px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;margin-bottom:34px;color:{c['ac'] if t!=1 else c['ink']};{'background:#0a0a0a;color:#e6ff3d;padding:8px 18px;align-self:flex-start' if t==1 else ''}}}ol{{list-style:none;margin-top:56px}}li{{font-size:48px;line-height:1.2;padding:32px 0;border-top:3px solid {c['rule']};display:flex;gap:34px;align-items:baseline}}li b{{font-family:'SG';color:{c['ac'] if t!=1 else c['ink']};font-size:56px}}"
    body="<div class=main>"
    if sl.get('tag'): body+=f"<div class=tag>{esc(sl['tag'])}</div>"
    if k=="recap":
        body+=f"<h1 style='font-size:100px'>{esc(sl['h'])}</h1><ol>"+"".join(f"<li><b>{j+1}</b>{esc(x)}</li>" for j,x in enumerate(sl['items']))+"</ol>"
    else:
        body+=f"<h1>{esc(sl['h'])}</h1>"+(f"<p>{esc(sl['s'])}</p>" if sl.get('s') else "")
    return h+body+"</div>",css
def main(path):
    d=json.load(open(path)); t=int(d.get('theme',1)); n=1+len(d['slides'])
    single=(d.get('mode')=='single')
    out=os.path.join(os.path.dirname(os.path.abspath(path)),d['date']); os.makedirs(out,exist_ok=True)
    pages=[cover(t,d['cover'],n)]+[inner(t,s,i+2,n) for i,s in enumerate(d['slides'])]
    if single: pages[0]=(pages[0][0].replace('Wischen →','walkzy.de').replace('01/01',''),pages[0][1])
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={"width":1080,"height":1350})
        for i,(h,css) in enumerate(pages,1):
            fn=os.path.join(out,f"_s{i}.html"); open(fn,"w").write(f"<!doctype html><meta charset=utf-8><style>{FF}{css}</style>{h}")
            pg.goto("file://"+fn); pg.wait_for_timeout(300); pg.screenshot(path=os.path.join(out,f"slide{i}.png")); os.remove(fn)
        b.close()
    print(n,"Folien in",out)
if __name__=="__main__": main(sys.argv[1])
