"""Nachbearbeitung: Blender-Bilder hochskalieren, Regen und Text drüberlegen, Video mit Ton bauen.

Aufruf: python post.py BILDORDNER AUSGABE.mp4 TON.wav
Regen ist fest vorberechnet (gleicher Startwert), unter dem Schirm bleibt es trocken.
"""
import sys, os, json, math, random, subprocess
from PIL import Image, ImageDraw, ImageFont

SRC, OUT, AUDIO = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS = 1080, 1920, 24
FONT = os.path.join(os.path.dirname(__file__), "..", "regen", "assets", "JetBrainsMono-Medium.ttf")
font = ImageFont.truetype(FONT, 34)
schirm = json.load(open(os.path.join(SRC, "schirm.json")))
frames = sorted(f for f in os.listdir(SRC) if f.startswith("f_") and f.endswith(".png"))
rng = random.Random(11)
DROPS = [(rng.random() * W, rng.random() * H, 0.8 + rng.random() * 0.5, 0.5 + rng.random() * 0.5) for _ in range(900)]
SPLASH = [(rng.random() * W, 1180 + rng.random() * 700, rng.random()) for _ in range(160)]
TMP = "/tmp/claude-0/post_frames"
os.makedirs(TMP, exist_ok=True)


def spaced(draw, text, y, alpha, color=(236, 236, 240)):
    sp = 34 * 0.26
    widths = [draw.textlength(c, font=font) for c in text]
    total = sum(widths) + sp * (len(text) - 1)
    x = (W - total) / 2
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=font, fill=(*color, int(255 * alpha)))
        x += w + sp


def fade(t, start, dur=0.7):
    k = min(max((t - start) / dur, 0), 1)
    return k * k * (3 - 2 * k)


for i, name in enumerate(frames):
    t = i / FPS
    img = Image.open(os.path.join(SRC, name)).convert("RGB").resize((W, H), Image.LANCZOS)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = schirm[min(i, len(schirm) - 1)]
    ux0, ux1, uy = s["x0"] * W, s["x1"] * W, (1 - s["y"]) * H   # Unterkante Schirm in Pixeln
    for x0, y0, sp, a in DROPS:
        y = (y0 + t * 2300 * sp) % (H + 80) - 40
        x = (x0 - (y - y0) * 0.04) % W
        if ux0 < x < ux1 and y > uy:   # trocken unter dem Schirm
            continue
        L = 34 * sp
        d.line([(x, y), (x - 1.4, y + L)], fill=(190, 200, 220, int(90 * a)), width=2)
    for x, y, ph in SPLASH:  # kleine Spritzer auf der Straße
        k = (t * 3 + ph) % 1
        if k < 0.25:
            r = 3 + k * 26
            d.ellipse([x - r, y - r * 0.25, x + r, y + r * 0.25], outline=(170, 180, 200, int(70 * (1 - k * 4))), width=1)
    spaced(d, "GLEICHER REGEN.", 250, fade(t, 0.4))
    spaced(d, "ANDERER TAG.", 302, fade(t, 1.6))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    img.save(f"{TMP}/p_{i:04d}.png")
    if i % 48 == 0:
        print("bild", i, flush=True)

subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{TMP}/p_%04d.png", "-i", AUDIO,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-r", str(FPS),
                "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
print("VIDEO OK", OUT)
