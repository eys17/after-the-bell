"""Shared look for every After the Bell carousel (fonts, colours, frame, rendering)."""
import html, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parents[1]
F = HERE / "node_modules/@fontsource"
e = html.escape

CSS = f"""
@font-face {{ font-family: SG; src: url('file://{F}/space-grotesk/files/space-grotesk-latin-600-normal.woff2'); font-weight: 600; }}
@font-face {{ font-family: SG; src: url('file://{F}/space-grotesk/files/space-grotesk-latin-700-normal.woff2'); font-weight: 700; }}
@font-face {{ font-family: IN; src: url('file://{F}/inter/files/inter-latin-400-normal.woff2'); font-weight: 400; }}
@font-face {{ font-family: IN; src: url('file://{F}/inter/files/inter-latin-600-normal.woff2'); font-weight: 600; }}
@font-face {{ font-family: JM; src: url('file://{F}/jetbrains-mono/files/jetbrains-mono-latin-600-normal.woff2'); font-weight: 600; }}
@font-face {{ font-family: JM; src: url('file://{F}/jetbrains-mono/files/jetbrains-mono-latin-700-normal.woff2'); font-weight: 700; }}
:root {{ --paper:#F5F3EC; --ink:#0E1116; --ink2:#1A1F27; --muted:#6B7079; --line:#DEDAD0;
  --up:#0E8A5F; --down:#D23C3C; --upbg:#E2F2EA; --downbg:#FBE5E3; --amber:#F2B33D; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ width:1080px; height:1350px; font-family:IN; color:var(--ink); background:var(--paper); }}
.s {{ width:1080px; height:1350px; padding:80px 84px 0; position:relative; display:flex; flex-direction:column; }}
.dark {{ background:var(--ink); color:#F5F3EC; }}
.top {{ display:flex; justify-content:space-between; align-items:center; font:600 24px/1 IN; letter-spacing:.12em; text-transform:uppercase; }}
.brand {{ display:flex; align-items:center; gap:14px; }}
.bell {{ width:30px; height:30px; border-radius:7px; background:var(--amber); display:grid; place-items:center; }}
.bell i {{ width:14px; height:14px; border:3px solid var(--ink); border-bottom:0; border-radius:8px 8px 2px 2px; position:relative; }}
.muted {{ color:var(--muted); }}
.dark .muted {{ color:#9399A3; }}
.foot {{ position:absolute; left:84px; right:84px; bottom:56px; display:flex; justify-content:space-between; font:500 22px/1 IN; color:var(--muted); }}
.dots {{ display:flex; gap:10px; }} .dots b {{ width:12px; height:12px; border-radius:50%; background:currentColor; opacity:.3; }} .dots b.on {{ opacity:1; }}
h1 {{ font:700 112px/1.0 SG; letter-spacing:-3px; margin-top:120px; text-wrap:balance; }}
h1 em {{ font-style:normal; color:var(--amber); }}
.idx {{ margin-top:70px; display:flex; align-items:baseline; gap:28px; }}
.idx .lab {{ font:600 26px/1 IN; letter-spacing:.1em; text-transform:uppercase; color:#9399A3; }}
.sub {{ margin-top:22px; font:600 26px/1 JM; color:#9399A3; }} .sub b {{ font-weight:700; }}
.idx .v {{ font:700 64px/1 JM; }}
.chg {{ font:700 64px/1 JM; }}
.up {{ color:var(--up); }} .down {{ color:var(--down); }}
.dark .up {{ color:#3DD598; }} .dark .down {{ color:#FF6B6B; }}
.breadth {{ margin-top:44px; }}
.bar {{ height:22px; border-radius:11px; overflow:hidden; display:flex; }}
.bar i {{ display:block; height:100%; }}
.blab {{ margin-top:16px; display:flex; justify-content:space-between; font:600 24px/1 JM; }}
.ctx {{ margin-top:56px; font:400 34px/1.45 IN; color:#C9CDD3; max-width:880px; }}
.cta {{ position:absolute; left:84px; bottom:120px; font:600 30px/1 SG; color:var(--amber); }}
.label {{ font:700 26px/1 IN; letter-spacing:.14em; text-transform:uppercase; margin-top:70px; }}
h2 {{ font:700 76px/1.02 SG; letter-spacing:-2px; margin-top:20px; }}
.rows {{ margin-top:46px; display:flex; flex-direction:column; gap:26px; }}
.row {{ background:#fff; border:2px solid var(--line); border-radius:26px; padding:34px 38px; display:grid; grid-template-columns:1fr auto; column-gap:24px; row-gap:16px; }}
.tk {{ font:700 46px/1 JM; }}
.nm {{ font:600 28px/1.1 IN; color:var(--muted); margin-top:10px; }}
.pill {{ font:700 46px/1 JM; padding:16px 22px; border-radius:16px; align-self:start; }}
.pill.up {{ background:var(--upbg); }} .pill.down {{ background:var(--downbg); }}
.why {{ grid-column:1 / -1; font:400 30px/1.42 IN; color:var(--ink2); }}
.chart {{ margin-top:50px; display:flex; flex-direction:column; gap:16px; }}
.cr {{ display:grid; grid-template-columns:270px 1fr; align-items:center; gap:18px; font:600 27px/1 IN; }}
.track {{ position:relative; height:46px; }}
.track .zero {{ position:absolute; left:{{Z}}%; top:-8px; bottom:-8px; width:2px; background:var(--ink); opacity:.25; }}
.track .b {{ position:absolute; top:0; height:100%; border-radius:6px; }}
.track .n {{ position:absolute; top:50%; transform:translateY(-50%); font:700 25px/1 JM; white-space:nowrap; }}
.note {{ margin-top:30px; font:400 24px/1.4 IN; color:var(--muted); }}
.watch {{ margin-top:46px; display:flex; flex-direction:column; gap:22px; }}
.w {{ display:grid; grid-template-columns:120px 1fr; gap:26px; background:#fff; border:2px solid var(--line); border-radius:24px; padding:30px 34px; }}
.w .d {{ font:700 34px/1.1 JM; color:var(--ink); background:var(--amber); border-radius:14px; display:grid; place-items:center; height:76px; }}
.w h3 {{ font:700 40px/1.1 SG; }}
.w p {{ margin-top:10px; font:400 28px/1.4 IN; color:var(--ink2); }}
.q {{ margin-top:50px; padding:38px 40px; background:var(--ink); color:#F5F3EC; border-radius:26px; font:700 44px/1.18 SG; letter-spacing:-.5px; }}
.q span {{ display:block; margin-top:18px; font:600 26px/1 IN; color:var(--amber); letter-spacing:0; }}
.disc {{ margin-top:34px; font:400 22px/1.45 IN; color:var(--muted); }}
"""

CSS += """
.tile {{ background:#fff; border:2px solid var(--line); border-radius:26px; padding:34px 36px; }}
"""
CSS = CSS.replace("{{", "{").replace("}}", "}")


def pct(x, d=2):
    return f"{'+' if x > 0 else '−' if x < 0 else ''}{abs(x):.{d}f}%"


def cls(x):
    return "up" if x > 0 else "down"


def money(x):
    """$ with B/T/M, e.g. 215.9B"""
    a = abs(x)
    s = f"{a/1e12:.2f}T" if a >= 1e12 else f"{a/1e9:.1f}B" if a >= 1e9 else f"{a/1e6:.0f}M"
    return ("−$" if x < 0 else "$") + s


def frame(i, n, body, brand, date_label, dark=False, right=""):
    dots = "".join(f'<b class="{"on" if k == i else ""}"></b>' for k in range(n))
    kind = "dark" if dark is True else (dark or "")
    return f"""<div class="s {kind}">
  <div class="top"><div class="brand"><div class="bell"><i></i></div>{e(brand)}</div><div class="muted">{e(date_label)}</div></div>
  {body}
  <div class="foot"><div class="dots">{dots}</div><div>{right}</div></div></div>"""


def shoot(slides, out: Path, extra_css="", check=".s > *:not(.foot):not(.top)"):
    """Render slides to out/slide_N.jpg. Returns the list of overflow problems."""
    out.mkdir(parents=True, exist_ok=True)
    for f in list(out.glob("slide_*.png")) + list(out.glob("slide_*.jpg")):
        f.unlink()
    problems = []
    tmp = out / "_slide.html"
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(slides, 1):
            tmp.write_text(f"<html><head><meta charset='utf-8'><style>{CSS}{extra_css}</style></head><body>{s}</body></html>")
            pg.goto(tmp.resolve().as_uri(), wait_until="load")
            pg.evaluate("document.fonts.ready.then(()=>1)"); pg.wait_for_timeout(150)
            over = pg.evaluate("""(sel) => { const f=document.querySelector('.foot').getBoundingClientRect().top;
              const bad=[]; document.querySelectorAll(sel + ', .s *').forEach(el=>{ const r=el.getBoundingClientRect();
                if (el.closest('.foot')||el.closest('.top')) return;
                if (r.height>0 && r.bottom>f-8) bad.push((el.className||el.tagName)+'');
                if (r.width>0 && (r.right>1080-40 || r.left<40) && !el.closest('.full')) bad.push('wide:'+(el.className||el.tagName)); });
              return [...new Set(bad)].slice(0,6) }""", check)
            if over:
                problems.append(f"slide {i} overflow: {over}")
            pg.screenshot(path=str(out / f"slide_{i}.jpg"), type="jpeg", quality=92)
        b.close()
    tmp.unlink(missing_ok=True)
    return problems
