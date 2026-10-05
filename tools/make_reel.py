#!/usr/bin/env python3
"""Baut ein Text-Reel (1080x1920, mp4) aus JSON: {"date","theme","scenes":[{"t0","t1","lines":[{"text","size","color"}],"big":optional}],"duration"}
Aufruf: python3 tools/make_reel.py reels/DATUM-reel.json -> reels/DATUM-reel.mp4"""
import json, os, sys, subprocess, shutil
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); FD=os.path.join(HERE,"fonts")
TH={1:("#e6ff3d","#0a0a0a","#3a3d1a","#0a0a0a"),2:("#07090d","#ffffff","#9aa5b3","#2d5bff"),3:("#ff4a1c","#fff4e6","#ffe0cf","#fff4e6"),4:("#efe8da","#111111","#5b564b","#1b3cff")}
def html(d):
    bg,ink,mut,ac=TH[int(d.get('theme',2))]
    sc=""
    for i,s in enumerate(d['scenes']):
        big=f"<div class=big style='font-size:{min(560,int(1650/len(s['big'])))}px'>{s['big']}</div>" if s.get('big') else ""
        lines="".join(f"<div class='ln' data-i={j} style='font-size:{l.get('size',110)}px;color:{ {'ac':ac,'mut':mut}.get(l.get('color'),ink) }'>{l['text']}</div>" for j,l in enumerate(s['lines']))
        sc+=f"<div class=sc id=s{i} data-t0={s['t0']} data-t1={s['t1']}>{big}{lines}</div>"
    return f"""<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:SG;font-weight:700;src:url('file://{FD}/space-grotesk-latin-700-normal.woff2')}}
@font-face{{font-family:IN;font-weight:600;src:url('file://{FD}/inter-latin-600-normal.woff2')}}
*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1920px;background:{bg};color:{ink};overflow:hidden;position:relative;font-family:IN}}
.sc{{position:absolute;inset:0;padding:0 90px;display:flex;flex-direction:column;justify-content:center;opacity:0}}
.big{{font-family:SG;font-weight:700;font-size:560px;line-height:.9;letter-spacing:-.06em;color:{ac};margin-bottom:60px;white-space:nowrap}}
.ln{{font-family:SG;font-weight:700;line-height:1.08;letter-spacing:-.02em;margin-top:18px;opacity:0}}
.top,.bot{{position:absolute;left:90px;right:90px;font-size:32px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:{mut};display:flex;justify-content:space-between}}
.top{{top:110px}}.bot{{bottom:150px}}
.bar{{position:absolute;left:0;top:0;height:10px;background:{ac}}}
</style><div class=top><span>Walkzy · Webseiten &amp; KI</span><span></span></div>{sc}<div class=bot><span>walkzy.de</span><span>Speichern</span></div><div class=bar id=bar></div>
<script>
const E=x=>1-Math.pow(1-x,3);
function setT(t,D){{document.getElementById('bar').style.width=(t/D*1080)+'px';
document.querySelectorAll('.sc').forEach(s=>{{const t0=+s.dataset.t0,t1=+s.dataset.t1;const on=t>=t0&&t<t1;s.style.opacity=on?1:0;if(!on)return;
 const lt=t-t0;const big=s.querySelector('.big');if(big){{const k=E(Math.min(1,lt/0.5));big.style.transform='translateY('+(60*(1-k))+'px) scale('+(0.92+0.08*k)+')';big.style.opacity=k}}
 s.querySelectorAll('.ln').forEach((l,j)=>{{const k=E(Math.max(0,Math.min(1,(lt-0.35-j*0.45)/0.45)));l.style.opacity=k;l.style.transform='translateY('+(40*(1-k))+'px)'}});
 const out=Math.max(0,Math.min(1,(t1-t)/0.25));s.style.opacity=out;}})}}
</script>"""
def main(path):
    d=json.load(open(path)); D=d['duration']; fps=24; n=int(D*fps)
    base=os.path.splitext(os.path.abspath(path))[0]; tmp=base+"_frames"; os.makedirs(tmp,exist_ok=True)
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={"width":1080,"height":1920})
        fn=base+"_tmp.html"; open(fn,"w").write(html(d)); pg.goto("file://"+fn); pg.wait_for_timeout(500)
        for i in range(n):
            pg.evaluate(f"setT({i/fps},{D})"); pg.screenshot(path=f"{tmp}/f{i:04d}.png")
        b.close(); os.remove(fn)
    out=base+".mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-framerate",str(fps),"-i",f"{tmp}/f%04d.png","-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-shortest","-c:v","libx264","-pix_fmt","yuv420p","-crf","18","-c:a","aac","-b:a","96k","-movflags","+faststart",out],check=True)
    shutil.rmtree(tmp); print(out)
if __name__=="__main__": main(sys.argv[1])
