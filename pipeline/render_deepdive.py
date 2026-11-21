"""Render the Sunday "Deep dive" carousel (10 slides).
usage: python pipeline/render_deepdive.py posts/<sun>/post.json posts/<sun>   -> exit 2 on overflow"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import e, pct, cls, frame, shoot, money

d = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2])
N, B, DL = 10, d["brand"], d["date_label"]

CSS = """
.kicker { margin-top:70px; font:700 26px/1 IN; letter-spacing:.16em; text-transform:uppercase; color:var(--amber); }
.dd h1 { font-size:92px; margin-top:34px; }
.co { margin-top:34px; font:600 30px/1.3 IN; color:#C9CDD3; }
.stats3 { margin-top:56px; display:grid; grid-template-columns:repeat(3,1fr); gap:18px; }
.st { border:2px solid #2A303A; border-radius:22px; padding:26px 24px; }
.st .k { font:600 22px/1 IN; letter-spacing:.08em; text-transform:uppercase; color:#9399A3; }
.st .v { margin-top:16px; font:700 44px/1 JM; }
.hook { margin-top:44px; font:400 32px/1.45 IN; color:#C9CDD3; }
.tease { position:absolute; left:84px; right:84px; bottom:120px; display:flex; justify-content:space-between;
  font:600 30px/1 SG; color:var(--ink); background:var(--amber); border-radius:20px; padding:26px 30px; }
.bul { margin-top:40px; display:flex; flex-direction:column; gap:20px; }
.bul p { font:400 31px/1.42 IN; color:var(--ink2); padding-left:34px; position:relative; }
.bul p:before { content:""; position:absolute; left:0; top:15px; width:14px; height:14px; border-radius:4px; background:var(--amber); }
.seg { margin-top:40px; }
.seg .sb { display:flex; height:46px; border-radius:12px; overflow:hidden; }
.seg .lg { margin-top:18px; display:flex; flex-wrap:wrap; gap:12px 26px; font:600 25px/1.2 IN; }
.seg .lg i { display:inline-block; width:18px; height:18px; border-radius:5px; margin-right:10px; vertical-align:-2px; }
.seg .src { margin-top:14px; font:400 21px/1.3 IN; color:var(--muted); }
.take { margin-top:30px; font:600 31px/1.38 IN; color:var(--ink); border-left:8px solid var(--amber); padding-left:24px; }
.chartbox { margin-top:34px; background:#fff; border:2px solid var(--line); border-radius:26px; padding:26px 26px 18px; }
.legend { display:flex; gap:30px; font:600 24px/1 IN; margin-bottom:14px; }
.legend i { display:inline-block; width:26px; height:8px; border-radius:4px; margin-right:10px; vertical-align:4px; }
.pills { margin-top:26px; display:flex; gap:16px; flex-wrap:wrap; }
.pills span { font:700 28px/1 JM; padding:14px 18px; border-radius:14px; background:#fff; border:2px solid var(--line); }
.tiles { margin-top:34px; display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.tile { padding:28px 30px; }
.tile .big { font:700 58px/1 JM; }
.tile .t { margin-top:12px; font:600 25px/1.3 IN; color:var(--ink2); }
.dollar { margin-top:30px; }
.dollar .db { display:flex; height:54px; border-radius:12px; overflow:hidden; font:700 22px/54px IN; color:#fff; }
.dollar .db span { padding-left:14px; white-space:nowrap; overflow:hidden; }
.dollar p { margin-top:12px; font:500 24px/1.35 IN; color:var(--muted); }
.ig { margin-top:40px; background:var(--ink); color:#F5F3EC; border-radius:28px; padding:40px 40px; }
.ig .n { font:700 120px/1 JM; color:var(--amber); }
.ig .l { margin-top:16px; font:600 30px/1.35 IN; color:#C9CDD3; }
.cmp { margin-top:30px; display:flex; flex-direction:column; gap:16px; }
.cmp .r { display:grid; grid-template-columns:330px 1fr 130px; gap:18px; align-items:center; font:600 26px/1.25 IN; }
.cmp .tr { height:30px; background:#EEEBE3; border-radius:8px; position:relative; overflow:hidden; }
.cmp .tr i { position:absolute; left:0; top:0; bottom:0; border-radius:8px; }
.cmp .v { font:700 30px/1 JM; text-align:right; }
.fine { margin-top:22px; font:400 21px/1.4 IN; color:var(--muted); }
.cases { margin-top:36px; display:flex; flex-direction:column; gap:20px; }
.case { background:#fff; border:2px solid var(--line); border-radius:24px; padding:28px 32px 24px; display:grid; grid-template-columns:62px 1fr; gap:20px; }
.case .num { width:62px; height:62px; border-radius:16px; display:grid; place-items:center; font:700 32px/1 JM; color:#fff; }
.case p { font:500 29px/1.38 IN; color:var(--ink2); }
.case small { display:block; margin-top:10px; font:500 21px/1 IN; color:var(--muted); }
.w .d { font-size:26px !important; }
.dd10 .watch { gap:14px; margin-top:34px; } .dd10 .w { padding:22px 30px; } .dd10 .q { margin-top:28px; padding:30px 36px; font-size:40px; } .dd10 .disc { margin-top:20px; }
"""


def svg_line(points, W=860, H=420):
    """points: list of (stock, spx) indexed to 100."""
    vals = [v for p in points for v in p]
    lo, hi = min(vals + [100]), max(vals + [100])
    pad = (hi - lo) * 0.08 or 1
    lo, hi = lo - pad, hi + pad
    n = len(points)
    X = lambda i: 70 + i * (W - 90) / (n - 1)
    Y = lambda v: 10 + (hi - v) / (hi - lo) * (H - 50)
    grid = ""
    import math
    nice = [1, 2, 2.5, 5, 10]
    raw = (hi - lo) / 4
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    step = min((m * mag for m in nice if m * mag >= raw), default=raw)
    v = math.ceil(lo / step) * step
    while v <= hi:
        grid += f'<line x1="70" x2="{W - 20}" y1="{Y(v):.0f}" y2="{Y(v):.0f}" stroke="#EEEBE3" stroke-width="2"/><text x="60" y="{Y(v) + 8:.0f}" text-anchor="end" font-family="JM" font-size="20" fill="#6B7079">{v:.0f}</text>'
        v += step
    line = lambda k, col, w: f'<polyline fill="none" stroke="{col}" stroke-width="{w}" stroke-linejoin="round" points="{" ".join(f"{X(i):.1f},{Y(p[k]):.1f}" for i, p in enumerate(points))}"/>'
    years = ""
    for i, wk in enumerate(d["price_chart"]):
        if i > 8 and wk["week"][:4] != d["price_chart"][i - 1]["week"][:4]:
            years += f'<text x="{X(i):.0f}" y="{H - 8}" font-family="JM" font-size="20" fill="#6B7079" text-anchor="middle">{wk["week"][:4]}</text>'
    return f'<svg width="{W}" height="{H}">{grid}{line(1, "#B9B4A8", 4)}{line(0, "#0E1116", 5)}{years}</svg>'


def svg_bars(rows, W=860, H=400):
    """rows: list of (label, revenue, net_income)."""
    m = max(r[1] for r in rows)
    n = len(rows)
    bw = (W - 40) / n
    out = ""
    for i, (lab, rev, ni) in enumerate(rows):
        x = 20 + i * bw
        hr = rev / m * (H - 110)
        out += f'<rect x="{x + bw*0.12:.0f}" y="{H - 50 - hr:.0f}" width="{bw*0.38:.0f}" height="{hr:.0f}" rx="8" fill="#0E1116"/>'
        out += f'<text x="{x + bw*0.31:.0f}" y="{H - 60 - hr:.0f}" text-anchor="middle" font-family="JM" font-weight="700" font-size="21" fill="#0E1116">{money(rev)}</text>'
        if ni is not None:
            hn = max(ni, 0) / m * (H - 110)
            col = "#0E8A5F" if ni >= 0 else "#D23C3C"
            out += f'<rect x="{x + bw*0.52:.0f}" y="{H - 50 - hn:.0f}" width="{bw*0.38:.0f}" height="{max(hn, 3):.0f}" rx="8" fill="{col}"/>'
            out += f'<text x="{x + bw*0.71:.0f}" y="{H - 60 - hn:.0f}" text-anchor="middle" font-family="JM" font-weight="700" font-size="21" fill="{col}">{money(ni)}</text>'
        out += f'<text x="{x + bw/2:.0f}" y="{H - 14}" text-anchor="middle" font-family="IN" font-weight="600" font-size="24" fill="#1A1F27">{e(lab)}</text>'
    return f'<svg width="{W}" height="{H}">{out}</svg>'


def cover():
    s3 = [("Share price", f"${d['price']:,.2f}"), ("Company value", money(d["market_cap"])),
          ("1 year", pct(d["perf_1y"], 1) if d.get("perf_1y") is not None else "—")]
    st = "".join(f'<div class="st"><div class="k">{k}</div><div class="v {cls(d["perf_1y"]) if k == "1 year" and d.get("perf_1y") is not None else ""}">{v}</div></div>' for k, v in s3)
    return frame(0, N, f"""<div class="kicker">Sunday deep dive</div><div class="dd"><h1>{e(d['title'])}</h1></div>
      <p class="co">{e(d['name'])} · {e(d['ticker'])} · {e(d['industry'])}</p>
      <div class="stats3">{st}</div><p class="hook">{e(d['hook'])}</p>
      <div class="tease"><span>10 slides, plain English</span><span>Swipe →</span></div>""", B, DL, dark=True)


def what():
    b = "".join(f"<p>{e(x)}</p>" for x in d["what_it_does"])
    seg = ""
    s = d.get("segments")
    if s:
        cols = ["#0E1116", "#F2B33D", "#0E8A5F", "#6B7079", "#D23C3C", "#B9B4A8"]
        bars = "".join(f'<i style="display:block;width:{it["pct"]}%;background:{cols[i % 6]}"></i>' for i, it in enumerate(s["items"]))
        lg = "".join(f'<span><i style="background:{cols[i % 6]}"></i>{e(it["name"])} {it["pct"]:.0f}%</span>' for i, it in enumerate(s["items"]))
        seg = f'<div class="seg"><div class="label" style="margin-top:0">Where the money comes from ({e(s["period"])})</div><div class="sb" style="margin-top:18px">{bars}</div><div class="lg">{lg}</div><div class="src">Source: {e(s["source_name"])}</div></div>'
    return frame(1, N, f"""<div class="label">The business</div><h2>What {e(d['short_name'])} does</h2><div class="bul">{b}</div>{seg}""", B, DL, right="Swipe →")


def price():
    pts = [(p["stock"], p["spx"]) for p in d["price_chart"]]
    pills = "".join(f'<span class="{cls(v)}">{lab} {pct(v, 1)}</span>' for lab, v in [("1 year", d.get("perf_1y")), ("5 years", d.get("perf_5y"))] if v is not None)
    return frame(2, N, f"""<div class="label">Share price</div><h2>5 years vs the S&amp;P 500</h2>
      <div class="chartbox"><div class="legend"><span><i style="background:#0E1116"></i>{e(d['ticker'])}</span><span><i style="background:#B9B4A8"></i>S&amp;P 500</span><span class="muted">$100 invested</span></div>{svg_line(pts)}</div>
      <div class="pills">{pills}</div><p class="take">{e(d['takeaways']['price'])}</p>""", B, DL, right="Swipe →")


def growth():
    rows = [(a["fy"], a["revenue"], a["net_income"]) for a in d["annual"]]
    c = f'<span>Sales growth: {pct(d["revenue_cagr"], 1)} a year over {d["cagr_years"]} years</span>' if d.get("revenue_cagr") is not None else ""
    return frame(3, N, f"""<div class="label">The money</div><h2>Sales and profit, by year</h2>
      <div class="chartbox"><div class="legend"><span><i style="background:#0E1116"></i>Sales</span><span><i style="background:#0E8A5F"></i>Profit</span></div>{svg_bars(rows)}</div>
      <div class="pills">{c}</div><p class="take">{e(d['takeaways']['growth'])}</p>""", B, DL, right="Swipe →")


def margins():
    m = d["margins"]
    tiles = [(m.get("gross"), "Gross margin", "left after making the product"), (m.get("operating"), "Operating margin", "left after running the business"),
             (m.get("net"), "Net margin", "profit after everything, incl. tax"), (m.get("fcf"), "Cash margin", "free cash left over")]
    t = "".join(f'<div class="tile"><div class="big">{v:.0f}%</div><div class="t"><b>{a}</b>: {b}</div></div>' for v, a, b in tiles if v is not None)
    net = max(min(m.get("net") or 0, 100), 0)
    dollar = f"""<div class="dollar"><div class="db"><span style="width:{100 - net}%;background:#B9B4A8">Costs, tax, etc.</span><span style="width:{net}%;background:#0E8A5F">{net:.0f}¢ profit</span></div>
      <p>Of every $1 of sales in {e(d['annual'][-1]['fy'])}</p></div>""" if m.get("net") is not None else ""
    return frame(4, N, f"""<div class="label">How much it keeps</div><h2>Profitability</h2><div class="tiles">{t}</div>{dollar}
      <p class="take">{e(d['takeaways']['margins'])}</p>""", B, DL, right="Swipe →")


def health():
    a = d["annual"][-1]
    tiles = [(money(d["cash"]), "cash in the bank"), (money(d["debt"]), "debt"),
             (money(d["fcf_ttm"]) if d.get("fcf_ttm") else "—", "free cash flow, last 12 months"),
             (money(a["buybacks"]) if a.get("buybacks") else "—", f"spent buying back its own shares ({e(a['fy'])})"),
             (f"{d['pe_trailing']:.1f}×" if d.get("pe_trailing") else "—", "price ÷ last year’s profit (P/E)"),
             (f"{d['pe_forward']:.1f}×" if d.get("pe_forward") else "—", "price ÷ next year’s expected profit")]
    t = "".join(f'<div class="tile"><div class="big" style="font-size:48px">{v}</div><div class="t">{k}</div></div>' for v, k in tiles)
    return frame(5, N, f"""<div class="label">Balance sheet</div><h2>Cash, debt and price tag</h2><div class="tiles">{t}</div>
      <p class="take">{e(d['takeaways']['health'])}</p>""", B, DL, right="Swipe →")


def assumes():
    a = d["assumptions"]
    if d.get("implied_growth") is not None:
        g = d["implied_growth"]
        m = max(abs(g), abs(d.get("revenue_cagr") or 0), 1)
        rows = [(f"Sales grew ({d['cagr_years']} yrs)", d.get("revenue_cagr")), ("Price assumes (next 10 yrs)", g)]
        cmp = "".join(f'<div class="r"><div>{lab}</div><div class="tr"><i style="width:{abs(v)/m*100:.0f}%;background:{"#F2B33D" if "assumes" in lab else "#0E1116"}"></i></div><div class="v">{pct(v, 1)}</div></div>' for lab, v in rows if v is not None)
        core = f"""<div class="ig"><div class="n">{pct(g, 1)}</div><div class="l">a year: the growth in free cash flow, for 10 years, that today’s price is betting on</div></div>
          <div class="cmp">{cmp}</div>"""
        fine = f"Reverse DCF: today’s company value ({money(d['enterprise_value'])} incl. debt, minus cash) vs free cash flow of {money(d['fcf_ttm'])} ({e(d['fcf_basis'])}), a {a['discount_rate']:.0f}% yearly return investors want, and {a['terminal_growth']:.0f}% growth after year {a['years']}. A way to read the price, not a forecast."
    else:
        core = f"""<div class="ig"><div class="n">{d['pe_trailing']:.0f}×</div><div class="l">price ÷ last year’s profit. Cash flow is too small or negative to work out what growth the price assumes.</div></div>""" if d.get("pe_trailing") else ""
        fine = "Free cash flow is negative or missing, so the growth the price implies can’t be worked out."
    return frame(6, N, f"""<div class="label">What the price is betting on</div><h2>Reading the price tag</h2>{core}
      <p class="take">{e(d['takeaways']['assumes'])}</p><p class="fine">{fine}</p>""", B, DL, right="Swipe →")


def case(i, key, title, col):
    items = "".join(f'<div class="case"><div class="num" style="background:{col}">{k}</div><p>{e(x["text"])}<small>Source: {e(x["source_name"])}</small></p></div>'
                    for k, x in enumerate(d[key], 1))
    return frame(i, N, f"""<div class="label" style="color:{col}">{title}</div><h2>{'Why fans are excited' if key == 'bull' else 'Why sceptics worry'}</h2>
      <div class="cases">{items}</div>""", B, DL, right="Swipe →")


def watch():
    ws = "".join(f'<div class="w"><div class="d">{e(w["when"])}</div><div><h3>{e(w["title"])}</h3><p>{e(w["text"])}</p></div></div>' for w in d["watch"])
    return frame(9, N, f"""<div class="dd10"><div class="label">Coming up</div><h2>What to watch</h2><div class="watch">{ws}</div>
      <div class="q">{e(d['question'])}<span>Tell us in the comments 👇</span></div>
      <p class="disc">For information only, not financial advice. Data: Yahoo Finance, company reports. Figures as of {e(d['as_of_label'])}.</p></div>""", B, DL)


slides = [cover(), what(), price(), growth(), margins(), health(), assumes(),
          case(7, "bull", "The bull case", "#0E8A5F"), case(8, "bear", "The bear case", "#D23C3C"), watch()]
problems = shoot(slides, out, CSS)
for p in problems:
    print(p)
print("rendered", len(slides), "slides")
sys.exit(2 if problems else 0)
