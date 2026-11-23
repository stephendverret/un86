"""UN86 post and reel maker.

    python3 kit/make.py week.json

week.json is a list of posts. Every post has "date" (YYYY-MM-DD), "slug" and "type".
Output goes to posts/<date>-<slug>.jpg (1080x1350) or .mp4 (1080x1920, 30 fps, silent).

Image types (all take "theme": "ink" or "paper"):
  statement  kicker, headline, body, size ("lead" for short lines, "mid" for longer ones)
  list       kicker, headline, rows: [[label, text], ...]
  phone      kicker, headline, body, screen (a file in kit/img, e.g. "count.jpg")
  offer      kicker, headline, rows, button
  html       inner (raw HTML inside the slide, for anything else)

Reel ("type": "reel"):
  title:    {kicker, headline, sub}
  segments: [{clip: "count" | "order" | "ways", kicker, caption, start, dur}]  (seconds into the clip)
  end:      {kicker, headline, body, button, foot}
"""
import html, json, os, subprocess, sys, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

KIT = Path(__file__).resolve().parent
ROOT = KIT.parent
OUT = ROOT / "posts"
CSS = (KIT / "base.css").read_text()
LOGO_D = (KIT / "logo_dark.svg").read_text()
LOGO_L = (KIT / "logo_light.svg").read_text()
E = html.escape

EXTRA = """
.s{display:flex;flex-direction:column}
.kick{font:500 30px/1 "IBM Plex Mono",monospace;letter-spacing:.1em;text-transform:uppercase}
.lead{font-weight:800;font-size:96px;line-height:1;letter-spacing:-.03em;text-wrap:balance}
.mid{font-weight:800;font-size:76px;line-height:1.02;letter-spacing:-.025em;text-wrap:balance}
.body{font-size:42px;line-height:1.3}
.rows{display:flex;flex-direction:column;margin-top:48px}
.row{display:flex;gap:32px;align-items:baseline;padding:30px 0;border-top:3px dashed #8C877D}
.row:last-child{border-bottom:3px dashed #8C877D}
.row .k{font:500 32px "IBM Plex Mono",monospace;color:#B3261E;min-width:180px}
.row .v{font-size:40px;line-height:1.3}
.phone{position:absolute;left:50%;transform:translateX(-50%);width:560px;border:14px solid #141414;border-bottom:none;border-radius:64px 64px 0 0;overflow:hidden;background:#141414;box-shadow:0 30px 60px rgba(0,0,0,.18)}
.phone img{width:100%;display:block;border-radius:50px 50px 0 0}
.tagbtn{display:inline-block;background:#B3261E;color:#fff;font-weight:700;font-size:40px;padding:26px 40px;border-radius:6px}
"""


def page(body, w, h):
    return f"<html><head><meta charset='utf-8'><style>{CSS}{EXTRA}</style></head><body style='margin:0;width:{w}px;height:{h}px'>{body}</body></html>"


def foot(dark):
    return f'<div class="foot">{LOGO_L if dark else LOGO_D}<span class="eyebrow" style="color:{"#8C877D" if dark else "#5E5A52"}">un86.app</span></div>'


def slide_html(p):
    t = p.get("type")
    dark = p.get("theme", "ink") == "ink"
    soft = "#DDD8CC" if dark else "#5E5A52"
    kick = f'<p class="kick" style="color:{"#8C877D" if dark else "#5E5A52"};margin-top:{120 if t in ("statement", "offer") else 40}px">{E(p.get("kicker", ""))}</p>'
    rows = "".join(f'<div class="row"><span class="k">{E(k)}</span><span class="v">{E(v)}</span></div>' for k, v in p.get("rows", []))
    show_foot, style = True, ""
    if t == "statement":
        cls = p.get("size", "lead")
        inner = kick + f'<h1 class="{cls}" style="margin-top:48px">{E(p["headline"])}</h1>' + (f'<p class="body" style="color:{soft};margin-top:56px">{E(p["body"])}</p>' if p.get("body") else "")
    elif t == "list":
        inner = kick + f'<h2 class="mid" style="margin-top:28px">{E(p["headline"])}</h2><div class="rows">{rows}</div>'
    elif t == "offer":
        inner = kick + f'<h1 class="lead" style="margin-top:48px">{E(p["headline"])}</h1><div class="rows">{rows}</div>' + (f'<div style="margin-top:56px"><span class="tagbtn">{E(p["button"])}</span></div>' if p.get("button") else "")
    elif t == "phone":
        show_foot, style = False, "padding-bottom:0"
        img = (KIT / "img" / p["screen"]).as_uri()
        inner = kick + f'<h2 class="mid" style="margin-top:28px">{E(p["headline"])}</h2>' + (f'<p class="body" style="color:{soft};margin-top:20px;font-size:38px">{E(p["body"])}</p>' if p.get("body") else "") + f'<div class="phone" style="top:440px;height:910px"><img src="{img}"></div>'
    elif t == "html":
        inner = p["inner"]
    else:
        raise SystemExit(f"unknown type {t}")
    return f'<div class="s {"ink" if dark else "paper"}" style="{style}"><div class="rule" style="top:0"></div>{inner}{foot(dark) if show_foot else ""}</div>'


# ---------- reels ----------
SX, SY, SW, SH = 270, 500, 540, 1168
REEL_CSS = """
.v{width:1080px;height:1920px;padding:110px 96px;position:relative;overflow:hidden;font-family:"Libre Franklin",sans-serif}
.cap{position:absolute;left:96px;right:96px;top:250px}
.cap .eyebrow{color:#B3261E;margin-bottom:22px}
.cap h2{font-size:80px}
.bez{position:absolute;left:254px;top:484px;width:572px;height:1200px;border-radius:66px;background:#141414;box-shadow:0 40px 80px rgba(0,0,0,.22)}
"""


def vpage(body, cls):
    return f"<html><head><meta charset='utf-8'><style>{CSS}{REEL_CSS}</style></head><body style='margin:0'><div class='v {cls}'><div class='rule' style='top:0'></div>{body}</div></body></html>"


def run(cmd):
    subprocess.run(cmd, check=True)


ENC = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", "30"]


def make_reel(pg, p, dest):
    tmp = Path(tempfile.mkdtemp())
    parts = []
    t = p["title"]
    pg.set_viewport_size({"width": 1080, "height": 1920})
    pg.set_content(vpage(f"""<div style='position:absolute;left:96px;right:96px;top:560px'>
      <div class='eyebrow' style='color:#B3261E;margin-bottom:40px'>{E(t.get('kicker', ''))}</div>
      <h1 style='font-size:124px'>{E(t['headline'])}</h1>
      {f"<p class='big' style='margin-top:48px;color:#C9C3B6'>{E(t['sub'])}</p>" if t.get('sub') else ''}</div>
      <div style='position:absolute;left:96px;bottom:300px'>{LOGO_L}</div>""", "ink")); pg.wait_for_timeout(300)
    pg.screenshot(path=str(tmp / "title.png"))
    run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(tmp / "title.png"), "-vf", "format=yuv420p,loop=-1:1,trim=duration=2.6,fade=in:st=0:d=0.3", *ENC, str(tmp / "p0.mp4")])
    parts.append(tmp / "p0.mp4")
    for i, s in enumerate(p["segments"], 1):
        pg.set_content(vpage(f"<div class='cap'><div class='eyebrow'>{E(s.get('kicker', ''))}</div><h2>{E(s['caption'])}</h2></div><div class='bez'></div>", "paper")); pg.wait_for_timeout(200)
        pg.screenshot(path=str(tmp / f"bg{i}.png"))
        clip = KIT / "broll" / f"{s['clip']}.mp4"
        trim = ["-ss", str(s.get("start", 0))] + (["-t", str(s["dur"])] if s.get("dur") else [])
        run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp / f"bg{i}.png"), *trim, "-i", str(clip), "-i", str(KIT / "img" / "phone-ring.png"),
             "-filter_complex", f"[0]loop=loop=-1:size=1,setpts=N/30/TB[bg];[1]scale={SW}:{SH}:flags=lanczos,setpts=PTS-STARTPTS[s];[bg][s]overlay={SX}:{SY}:shortest=1[a];[a][2]overlay=0:0,format=yuv420p",
             *ENC, str(tmp / f"p{i}.mp4")])
        parts.append(tmp / f"p{i}.mp4")
    e = p["end"]
    pg.set_content(vpage(f"""<div style='position:absolute;left:96px;right:96px;top:420px'>
      <div class='eyebrow' style='color:#E05A4F;margin-bottom:40px'>{E(e.get('kicker', ''))}</div>
      <h1 style='font-size:112px'>{E(e['headline'])}</h1>
      {f"<p class='big' style='margin-top:44px;font-size:54px'>{E(e['body'])}</p>" if e.get('body') else ''}
      {f"<div class='btn' style='margin-top:64px;font-size:50px'>{E(e['button'])}</div>" if e.get('button') else ''}
      {f"<p class='big' style='margin-top:56px;color:#C9C3B6'>{E(e['foot'])}</p>" if e.get('foot') else ''}</div>
      <div style='position:absolute;left:96px;bottom:300px'>{LOGO_L}</div>""", "ink")); pg.wait_for_timeout(300)
    pg.screenshot(path=str(tmp / "end.png"))
    run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", str(tmp / "end.png"), "-vf", "format=yuv420p,loop=-1:1,trim=duration=4.6,fade=out:st=4.1:d=0.5", *ENC, str(tmp / "pz.mp4")])
    parts.append(tmp / "pz.mp4")
    (tmp / "list.txt").write_text("".join(f"file '{x}'\n" for x in parts))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-c", "copy", "-movflags", "+faststart", str(dest) + ".part.mp4"])
    os.replace(str(dest) + ".part.mp4", dest)
    # cover frame for previews
    run(["ffmpeg", "-v", "error", "-y", "-i", str(dest), "-frames:v", "1", "-q:v", "3", str(dest.with_suffix(".jpg"))])


def main(spec):
    posts = json.loads(Path(spec).read_text())
    OUT.mkdir(exist_ok=True)
    made = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        for p in posts:
            name = f"{p['date']}-{p['slug']}"
            if p["type"] == "reel":
                dest = OUT / f"{name}.mp4"; make_reel(pg, p, dest)
            else:
                pg.set_viewport_size({"width": 1080, "height": 1350})
                pg.set_content(page(slide_html(p), 1080, 1350)); pg.wait_for_timeout(400)
                dest = OUT / f"{name}.jpg"
                pg.locator(".s").screenshot(path=str(dest), type="jpeg", quality=92)
            made.append(str(dest.relative_to(ROOT)))
            print("made", dest.relative_to(ROOT))
        b.close()
    return made


if __name__ == "__main__":
    main(sys.argv[1])
