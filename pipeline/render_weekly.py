"""Render the "Week in review" carousel (7 slides).
usage: python pipeline/render_weekly.py posts/<sat>/post.json posts/<sat>   -> exit 2 on overflow"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import e, pct, cls, frame, shoot

d = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2])
N, B, DL = 7, d["brand"], d["date_label"]

CSS = """
.wk h1 { font-size:96px; margin-top:70px; }
.kicker { margin-top:70px; font:700 26px/1 IN; letter-spacing:.16em; text-transform:uppercase; color:var(--amber); }
.spark { margin-top:34px; }
.tease { position:absolute; left:84px; right:84px; bottom:120px; display:flex; justify-content:space-between; align-items:center;
  font:600 30px/1 SG; color:var(--ink); background:var(--amber); border-radius:20px; padding:26px 30px; }
.ff { background:var(--amber); }
.ff .top, .ff .foot { color:var(--ink); }
.ff .bell { background:var(--ink); } .ff .bell i { border-color:var(--amber); }
.fflab { margin-top:120px; font:700 30px/1 IN; letter-spacing:.16em; text-transform:uppercase; }
.fftext { margin-top:44px; font:700 64px/1.14 SG; letter-spacing:-1.5px; text-wrap:pretty; }
.ffsrc { margin-top:44px; font:500 24px/1.4 IN; opacity:.7; }
.days { margin-top:50px; display:flex; flex-direction:column; gap:22px; }
.dr { background:#fff; border:2px solid var(--line); border-radius:22px; padding:30px 30px; display:grid; grid-template-columns:90px 1fr 170px; align-items:center; column-gap:22px; row-gap:10px; }
.dr .dn { font:700 34px/1 JM; }
.dr .lab { font:600 29px/1.25 IN; color:var(--ink2); }
.dr .v { font:700 36px/1 JM; text-align:right; }
.dr .bar2 { grid-column:2 / 4; height:12px; border-radius:6px; background:#EEEBE3; position:relative; overflow:hidden; }
.dr .bar2 i { position:absolute; top:0; bottom:0; border-radius:6px; }
.rows.five { gap:12px; margin-top:28px; }
.five .row { padding:18px 26px; row-gap:6px; border-radius:20px; }
.five .tk { font-size:34px; display:inline; } .five .nm { font-size:23px; display:inline; margin:0 0 0 14px; }
.five .pill { font-size:30px; padding:8px 14px; border-radius:12px; }
.five .why { font-size:24px; line-height:1.32; }
.tiles { margin-top:44px; display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:22px; }
.tile { min-width:0; }
.tile .big { font:700 72px/1 JM; }
.tile .big.sm { font-size:46px; }
.tile .t { margin-top:16px; font:600 27px/1.3 IN; color:var(--ink2); }
.ytd { margin-top:30px; font:600 28px/1.4 IN; color:var(--ink2); }
.ytd b { font-family:JM; }
"""


def spark():
    pts = [d["base_close"]] + [x["close"] for x in d["spx_days"]]
    lo, hi = min(pts), max(pts)
    W, H = 912, 150
    xy = [(i * W / (len(pts) - 1), H - 10 - (p - lo) / ((hi - lo) or 1) * (H - 20)) for i, p in enumerate(pts)]
    col = "#3DD598" if pts[-1] >= pts[0] else "#FF6B6B"
    path = " ".join(f"{x:.0f},{y:.0f}" for x, y in xy)
    labels = "".join(f'<text x="{x:.0f}" y="{H + 34}" fill="#9399A3" font-family="JM" font-size="22" text-anchor="middle">{e(lab)}</text>'
                     for (x, _), lab in zip(xy, ["Fri"] + [s["day"] for s in d["spx_days"]]))
    return f'<svg class="spark" width="{W}" height="{H + 44}" viewBox="-30 0 {W + 60} {H + 44}"><polyline points="{path}" fill="none" stroke="{col}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>{"".join(f"<circle cx=\'{x:.0f}\' cy=\'{y:.0f}\' r=\'8\' fill=\'{col}\'/>" for x, y in xy)}{labels}</svg>'


def cover():
    h = e(d["headline"]).replace(e(d["headline_em"]), f"<em>{e(d['headline_em'])}</em>", 1) if d.get("headline_em") else e(d["headline"])
    sp = d["indices"]["S&P 500"]
    others = " · ".join(f"{e(k)} <b class='{cls(v['chg'])}'>{pct(v['chg'])}</b>" for k, v in d["indices"].items() if k != "S&P 500")
    return frame(0, N, f"""<div class="kicker">Week in review · {e(d['week_label'])}</div><div class="wk"><h1>{h}</h1></div>
  <div class="idx"><span class="lab">S&amp;P 500 this week</span><span class="chg {cls(sp['chg'])}">{pct(sp['chg'])}</span></div>
  <div class="sub">{others}</div>{spark()}
  <div class="tease"><span>💡 Plus: this week’s fun fact</span><span>Swipe →</span></div>""", B, DL, dark=True)


def funfact():
    f = d["fun_fact"]
    return frame(1, N, f"""<div class="fflab">💡 Fun fact</div><p class="fftext">{e(f['text'])}</p>
      <p class="ffsrc">Source: {e(f['source_name'])}</p>""", B, DL, dark="ff", right="The week →")


def days():
    m = max(abs(x["chg"]) for x in d["spx_days"]) or 1
    rows = []
    for x in d["spx_days"]:
        w = abs(x["chg"]) / m * 50
        left = 50 if x["chg"] >= 0 else 50 - w
        col = "var(--up)" if x["chg"] >= 0 else "var(--down)"
        rows.append(f"""<div class="dr"><div class="dn">{e(x['day'])}</div><div class="lab">{e(x['label'])}</div>
          <div class="v {cls(x['chg'])}">{pct(x['chg'])}</div><div class="bar2"><i style="left:{left}%;width:{w}%;background:{col}"></i></div></div>""")
    return frame(2, N, f"""<div class="label">Day by day · S&amp;P 500</div><h2>{e(d['days_title'])}</h2><div class="days">{''.join(rows)}</div>""", B, DL, right="Swipe →")


def movers(i, key):
    rows = "".join(f"""<div class="row"><div><div class="tk">{e(r['ticker'])}</div><div class="nm">{e(r['name'])}</div></div>
      <div class="pill {cls(r['chg'])}">{pct(r['chg'])}</div><p class="why">{e(r['why'])}</p></div>""" for r in d[key])
    c = cls(d[key][0]["chg"])
    word = "winners" if c == "up" else "losers"
    return frame(i, N, f"""<div class="label {c}">Top 5 {word} of the week</div><h2>{'What went up' if c == 'up' else 'What went down'}</h2>
      <div class="rows five">{rows}</div>""", B, DL, right="Swipe →")


def numbers():
    s = d["stats"]
    bm = s["biggest_day_move"]
    tiles = [
        (f"{s['pct_up']}%", "of S&amp;P 500 stocks rose this week", ""),
        (f"{s['spx_up_days']} of {d['sessions']}", "days the S&amp;P 500 closed higher", ""),
        (f"{e(bm['ticker'])} {pct(bm['chg'])}", f"biggest one-day move ({e(bm['name'])}, {e(bm['day'])})", "sm"),
        (f"{pct(s['best_sector'][1])}", f"best sector: {e(s['best_sector'][0])}<br>worst: {e(s['worst_sector'][0])} {pct(s['worst_sector'][1])}", "sm"),
    ]
    t = "".join(f'<div class="tile"><div class="big {c}">{a}</div><div class="t">{b}</div></div>' for a, b, c in tiles)
    return frame(5, N, f"""<div class="label">By the numbers</div><h2>{e(d['numbers_title'])}</h2><div class="tiles">{t}</div>
      <p class="ytd">S&amp;P 500 so far this year: <b class="{cls(s['spx_ytd'])}">{pct(s['spx_ytd'])}</b></p>""", B, DL, right="Swipe →")


def nextweek():
    ws = "".join(f'<div class="w"><div class="d">{e(w["when"])}</div><div><h3>{e(w["title"])}</h3><p>{e(w["text"])}</p></div></div>' for w in d["watch"])
    return frame(6, N, f"""<div class="label">Coming up</div><h2>Next week</h2><div class="watch">{ws}</div>
  <div class="q">{e(d['question'])}<span>Tell us in the comments 👇</span></div>
  <p class="disc">For information only, not financial advice. Prices are closing prices from Yahoo Finance.</p>""", B, DL)


slides = [cover(), funfact(), days(), movers(3, "winners"), movers(4, "losers"), numbers(), nextweek()]
problems = shoot(slides, out, CSS)
for p in problems:
    print(p)
print("rendered", len(slides), "slides")
sys.exit(2 if problems else 0)
