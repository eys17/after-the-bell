"""Step 1: market data for one US session.

usage: python pipeline/data.py [YYYY-MM-DD]      (default: today in New York)
writes posts/<date>/data.json
exit 0 = ok, 3 = market closed that day (nothing to post), 4 = session not closed yet, 1 = error
"""
import json, sys, io, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
import urllib.request
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
SP_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"


def constituents() -> pd.DataFrame:
    local = ROOT / "pipeline" / "sp500.csv"
    try:
        raw = urllib.request.urlopen(SP_URL, timeout=20).read().decode()
        df = pd.read_csv(io.StringIO(raw))
        if len(df) > 480:
            local.write_text(raw)
            return df
    except Exception as exc:  # fall back to the last good copy
        print("constituents: using cached list:", exc)
    return pd.read_csv(local)


def main() -> int:
    ny_today = dt.datetime.now(ZoneInfo("America/New_York")).date()
    day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else ny_today
    now_ny = dt.datetime.now(ZoneInfo("America/New_York"))
    if day > now_ny.date() or (day == now_ny.date() and now_ny.time() < dt.time(16, 20)):
        print(f"{day}: the US session has not closed yet (New York time {now_ny:%H:%M}) - refusing to use intraday prices")
        return 4
    sp = constituents()
    tick = [s.replace(".", "-") for s in sp.Symbol]
    meta = {t: (n, s, i) for t, n, s, i in zip(tick, sp.Security, sp["GICS Sector"], sp["GICS Sub-Industry"])}

    start = day - dt.timedelta(days=14)
    end = day + dt.timedelta(days=1)
    px = yf.download(tick, start=str(start), end=str(end), progress=False, auto_adjust=True, threads=True)["Close"]
    px = px.dropna(how="all")
    if px.empty or px.index[-1].date() != day:
        print(f"no session on {day} (last bar {px.index[-1].date() if not px.empty else None}) - market closed")
        return 3
    have = px.iloc[-1].notna().sum()
    if have < 450:
        print(f"only {have} prices for {day} - data incomplete, refusing")
        return 1

    ch = (px.iloc[-1] / px.iloc[-2] - 1).dropna() * 100
    sect = pd.Series({t: meta[t][1] for t in ch.index})
    sub = pd.Series({t: meta[t][2] for t in ch.index})

    def row(t):
        peers = [p for p in sub[sub == sub[t]].index if p != t]
        peer_moves = {p: round(float(ch[p]), 2) for p in sorted(peers, key=lambda p: -abs(ch[p]))[:4]}
        news = []
        try:
            for n in (yf.Ticker(t).news or [])[:6]:
                c = n.get("content", n)
                news.append({"title": c.get("title"), "publisher": (c.get("provider") or {}).get("displayName") if isinstance(c.get("provider"), dict) else c.get("publisher"),
                             "date": c.get("pubDate") or c.get("providerPublishTime"),
                             "url": ((c.get("canonicalUrl") or {}).get("url") if isinstance(c.get("canonicalUrl"), dict) else c.get("link"))})
        except Exception:
            news = []  # headlines are only a starting point for research
        return dict(ticker=t, name=meta[t][0], sector=meta[t][1], sub_industry=meta[t][2],
                    close=round(float(px[t].iloc[-1]), 2), chg=round(float(ch[t]), 2),
                    sub_industry_peers=peer_moves, yahoo_headlines=news)

    idx = {}
    for sym, label in [("^GSPC", "S&P 500"), ("^IXIC", "Nasdaq"), ("^DJI", "Dow")]:
        s = yf.download(sym, start=str(start), end=str(end), progress=False, auto_adjust=True)["Close"].squeeze().dropna()
        if s.index[-1].date() == day:
            idx[label] = dict(close=round(float(s.iloc[-1]), 2), chg=round(float(s.iloc[-1] / s.iloc[-2] - 1) * 100, 2))
    if "S&P 500" not in idx:
        print("S&P 500 index level missing for", day); return 1

    order = ch.sort_values()
    sectors = ch.groupby(sect).median().sort_values(ascending=False)
    out = dict(
        date=str(day), generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        indices=idx, breadth_up=int((ch > 0).sum()), breadth_down=int((ch < 0).sum()), n=int(len(ch)),
        winners=[row(t) for t in order.index[::-1][:3]],
        losers=[row(t) for t in order.index[:3]],
        sectors=[[s, round(float(v), 2)] for s, v in sectors.items()],
        source="Yahoo Finance closing prices, S&P 500 constituents",
    )
    d = ROOT / "posts" / str(day); d.mkdir(parents=True, exist_ok=True)
    (d / "data.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"{day}: S&P {idx['S&P 500']['chg']:+.2f}%  up {out['breadth_up']} / down {out['breadth_down']}")
    for k in ("winners", "losers"):
        print(k, [(r["ticker"], r["chg"]) for r in out[k]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
