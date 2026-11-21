"""Weekend step 1a: numbers for the "Week in review" post.

usage: python pipeline/weekly_data.py <saturday YYYY-MM-DD>
The week is every trading session from Monday to Friday before that Saturday (holidays are
simply absent). Weekly moves are measured from the previous week's last close.
writes posts/<saturday>/weekly_data.json
exit 0 = ok, 3 = no trading sessions that week, 1 = error
"""
import json, sys, datetime as dt
from pathlib import Path
import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import constituents  # same S&P 500 list as the daily post

ROOT = Path(__file__).resolve().parents[1]


def main(sat: str) -> int:
    saturday = dt.date.fromisoformat(sat)
    if saturday.weekday() != 5:
        print("give the Saturday date"); return 1
    monday = saturday - dt.timedelta(days=5)
    sp = constituents()
    tick = [s.replace(".", "-") for s in sp.Symbol]
    meta = {t: (n, s, i) for t, n, s, i in zip(tick, sp.Security, sp["GICS Sector"], sp["GICS Sub-Industry"])}

    start, end = monday - dt.timedelta(days=12), saturday
    px = yf.download(tick, start=str(start), end=str(end), progress=False, auto_adjust=True, threads=True)["Close"].dropna(how="all")
    week = [d for d in px.index if monday <= d.date() < saturday]
    if not week:
        print("no trading sessions in the week of", monday); return 3
    before = [d for d in px.index if d.date() < monday]
    base, last = before[-1], week[-1]
    if px.loc[last].notna().sum() < 450:
        print("prices incomplete for", last.date()); return 1

    wk = (px.loc[last] / px.loc[base] - 1).dropna() * 100
    sect = pd.Series({t: meta[t][1] for t in wk.index})
    sub = pd.Series({t: meta[t][2] for t in wk.index})

    def row(t):
        peers = [p for p in sub[sub == sub[t]].index if p != t]
        news = []
        try:
            for n in (yf.Ticker(t).news or [])[:6]:
                c = n.get("content", n)
                news.append({"title": c.get("title"), "date": c.get("pubDate")})
        except Exception:
            pass
        daily = (px[t].loc[[base] + week].pct_change().dropna() * 100).round(2)
        return dict(ticker=t, name=meta[t][0], sector=meta[t][1], sub_industry=meta[t][2],
                    close=round(float(px[t].loc[last]), 2), chg=round(float(wk[t]), 2),
                    daily={str(k.date()): float(v) for k, v in daily.items()},
                    sub_industry_peers={p: round(float(wk[p]), 2) for p in sorted(peers, key=lambda p: -abs(wk[p]))[:4]},
                    yahoo_headlines=news)

    # indices: weekly move and the S&P's daily path
    idx, spx_days = {}, []
    for sym, label in [("^GSPC", "S&P 500"), ("^IXIC", "Nasdaq"), ("^DJI", "Dow")]:
        s = yf.download(sym, start=str(start), end=str(end), progress=False, auto_adjust=True)["Close"].squeeze().dropna()
        b = s[[d for d in s.index if d.date() < monday]].iloc[-1]
        w = s[[d for d in s.index if monday <= d.date() < saturday]]
        idx[label] = dict(close=round(float(w.iloc[-1]), 2), chg=round(float(w.iloc[-1] / b - 1) * 100, 2))
        if label == "S&P 500":
            prev = b
            for d, v in w.items():
                spx_days.append(dict(date=str(d.date()), day=d.strftime("%a"), close=round(float(v), 2),
                                     chg=round(float(v / prev - 1) * 100, 2)))
                prev = v
            ytd = yf.download(sym, start=f"{saturday.year - 1}-12-20", end=str(end), progress=False, auto_adjust=True)["Close"].squeeze().dropna()
            y0 = ytd[[d for d in ytd.index if d.year < saturday.year]].iloc[-1]
            idx[label]["ytd"] = round(float(w.iloc[-1] / y0 - 1) * 100, 2)

    # daily moves of every stock, for "by the numbers"
    dmove = (px.loc[[base] + week].pct_change().iloc[1:] * 100)
    big = dmove.stack().dropna()
    (bd, bt), bv = big.abs().idxmax(), None
    bv = float(big[(bd, bt)])
    sectors = wk.groupby(sect).median().sort_values(ascending=False)
    order = wk.sort_values()

    # headlines of our own daily posts that week (for the day-by-day labels)
    ours = {}
    for d in week:
        p = ROOT / "posts" / str(d.date()) / "post.json"
        if p.exists():
            ours[str(d.date())] = json.loads(p.read_text()).get("headline")

    out = dict(
        saturday=sat, week_start=str(monday), week_end=str(last.date()), sessions=len(week),
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        indices=idx, spx_days=spx_days, our_daily_headlines=ours,
        breadth_up=int((wk > 0).sum()), breadth_down=int((wk < 0).sum()), n=int(len(wk)),
        winners=[row(t) for t in order.index[::-1][:5]],
        losers=[row(t) for t in order.index[:5]],
        sectors=[[s, round(float(v), 2)] for s, v in sectors.items()],
        stats=dict(
            pct_up=round(float((wk > 0).mean() * 100)),
            spx_up_days=sum(1 for d in spx_days if d["chg"] > 0),
            biggest_day_move=dict(ticker=bt, name=meta[bt][0], date=str(bd.date()), day=bd.strftime("%A"), chg=round(bv, 2)),
            best_sector=[sectors.index[0], round(float(sectors.iloc[0]), 2)],
            worst_sector=[sectors.index[-1], round(float(sectors.iloc[-1]), 2)],
            spx_ytd=idx["S&P 500"]["ytd"],
        ),
        source="Yahoo Finance closing prices, S&P 500 constituents",
    )
    d = ROOT / "posts" / sat; d.mkdir(parents=True, exist_ok=True)
    (d / "weekly_data.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"week {monday}..{last.date()} ({len(week)} sessions): S&P {idx['S&P 500']['chg']:+.2f}%, {out['stats']['pct_up']}% of stocks up")
    for k in ("winners", "losers"):
        print(k, [(r["ticker"], r["chg"]) for r in out[k]])
    print("stats", out["stats"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
