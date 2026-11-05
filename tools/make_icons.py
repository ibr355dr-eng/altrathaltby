#!/usr/bin/env python3
"""يولّد الأيقونات وصورة المشاركة (og.png) بكروم بلا واجهة. يُشغَّل عند تغيير الشعار فقط."""
import struct, subprocess, tempfile
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "site/static/icons"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MARK = ('<path d="M32 32V6A26 26 0 0 1 58 32Z" fill="#a8323a"/><path d="M32 32H58A26 26 0 0 1 32 58Z" fill="#b7831b"/>'
        '<path d="M32 32V58A26 26 0 0 1 6 32Z" fill="#4b3c5a"/><path d="M32 32H6A26 26 0 0 1 32 6Z" fill="#3f6f8c"/>'
        '<circle cx="32" cy="32" r="9" fill="#fffdf8"/>')
SVG = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="31" fill="#fffdf8"/>{MARK}</svg>'


def shot(html, w, h, name):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "i.html"
        f.write_text(html, encoding="utf-8")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={d}/p",
                        "--force-device-scale-factor=1", f"--window-size={w},{h}", "--virtual-time-budget=4000",
                        f"--screenshot={OUT / name}", f.as_uri()], check=True, capture_output=True)


def icon(size, name, bg="transparent", pad=0.0):
    inner = int(size * (1 - 2 * pad))
    shot(f'<html><body style="margin:0;background:{bg};width:{size}px;height:{size}px;display:grid;place-items:center">'
         f'<div style="width:{inner}px;height:{inner}px">{SVG.replace("<svg ", "<svg width=100% height=100% ")}</div></body></html>', size, size, name)


(OUT / "favicon.svg").write_text(SVG, encoding="utf-8")
icon(32, "favicon-32.png")
icon(180, "apple-touch-icon.png", "#f7f3ea", 0.08)
icon(192, "icon-192.png")
icon(512, "icon-512.png")
icon(512, "icon-512-maskable.png", "#f7f3ea", 0.18)
png = (OUT / "favicon-32.png").read_bytes()
(OUT / "favicon.ico").write_bytes(struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", 32, 32, 0, 0, 1, 32, len(png), 22) + png)
(OUT / "favicon-32.png").unlink()

shot(f"""<html dir="rtl"><head><link href="https://fonts.googleapis.com/css2?family=Amiri:wght@700&family=Noto+Naskh+Arabic:wght@500&display=swap" rel="stylesheet"></head>
<body style="margin:0;width:1200px;height:630px;background:#f7f3ea;display:flex;align-items:center;gap:56px;padding:0 90px;box-sizing:border-box;font-family:Amiri,serif;color:#1f1a14">
<div style="width:300px;height:300px;flex:none">{SVG.replace("<svg ", "<svg width=100% height=100% ")}</div>
<div><div style="font-size:96px;font-weight:700;line-height:1.2">التراث الطبي</div>
<div style="font-family:'Noto Naskh Arabic',serif;font-size:36px;color:#5a5045;margin-top:12px">مرجع بحوث الطب العربي القديم وطب الأخلاط</div>
<div style="font-family:'Noto Naskh Arabic',serif;font-size:28px;color:#7a4b1f;margin-top:28px">altrathaltby.com</div></div></body></html>""", 1200, 630, "og.png")
print(sorted(p.name for p in OUT.iterdir()))
