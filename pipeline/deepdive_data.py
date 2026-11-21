"""Weekend step 1b: numbers for the Sunday "Deep dive" on one company.

usage: python pipeline/deepdive_data.py <TICKER> <sunday YYYY-MM-DD>
writes posts/<sunday>/deepdive_data.json      exit 0 ok, 1 error

"What the price assumes" is a reverse discounted-cash-flow: it finds the yearly growth in
free cash flow, for 10 years, that would make the company worth exactly today's market
value, assuming investors want a 9% yearly return and growth slows to 3% after year 10.
It is a way of reading the price, not a verdict on it.
"""
import json, sys, datetime as dt
from pathlib import Path
import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import constituents

ROOT = Path(__file__).resolve().parents[1]
DISCOUNT, TERMINAL, YEARS = 0.09, 0.03, 10


def implied_growth(fcf0: float, value: float) -> float | None:
    if not fcf0 or fcf0 <= 0 or value <= 0:
        return None

    def pv(g):
        tot, f = 0.0, fcf0
        for t in range(1, YEARS + 1):
            f *= 1 + g
            tot += f / (1 + DISCOUNT) ** t
        return tot + f * (1 + TERMINAL) / (DISCOUNT - TERMINAL) / (1 + DISCOUNT) ** YEARS

    lo, hi = -0.5, 1.0
    if pv(lo) > value or pv(hi) < value:
        return None
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if pv(mid) < value else (lo, mid)
    return round(mid * 100, 1)


def row(df: pd.DataFrame, *names):
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None


def main(ticker: str, sunday: str) -> int:
    ticker = ticker.upper().replace(".", "-")
    sp = constituents()
    members = {s.replace(".", "-"): (n, sec, sub) for s, n, sec, sub in zip(sp.Symbol, sp.Security, sp["GICS Sector"], sp["GICS Sub-Industry"])}
    if ticker not in members:
        print(ticker, "is not in the S&P 500 list"); return 1
    t = yf.Ticker(ticker)
    info = t.info or {}
    inc, q, cf, qcf = t.income_stmt, t.quarterly_income_stmt, t.cashflow, t.quarterly_cashflow

    rev, ni = row(inc, "Total Revenue"), row(inc, "Net Income", "Net Income Common Stockholders")
    gp, op = row(inc, "Gross Profit"), row(inc, "Operating Income")
    fcf = row(cf, "Free Cash Flow")
    buyb = row(cf, "Repurchase Of Capital Stock")
    divs = row(cf, "Cash Dividends Paid", "Common Stock Dividend Paid")
    if rev is None or ni is None:
        print("no income statement for", ticker); return 1
    years = [c for c in rev.index if pd.notna(rev[c])][:5][::-1]
    annual = [dict(fy=f"FY{c.year}", period_end=str(c.date()),
                   revenue=float(rev[c]), net_income=float(ni[c]) if pd.notna(ni.get(c)) else None,
                   gross_profit=float(gp[c]) if gp is not None and pd.notna(gp.get(c)) else None,
                   operating_income=float(op[c]) if op is not None and pd.notna(op.get(c)) else None,
                   fcf=float(fcf[c]) if fcf is not None and pd.notna(fcf.get(c)) else None,
                   buybacks=-float(buyb[c]) if buyb is not None and pd.notna(buyb.get(c)) else None,
                   dividends=-float(divs[c]) if divs is not None and pd.notna(divs.get(c)) else None) for c in years]
    last = annual[-1]
    margins = {k: round(last[v] / last["revenue"] * 100, 1) if last.get(v) is not None and last["revenue"] else None
               for k, v in [("gross", "gross_profit"), ("operating", "operating_income"), ("net", "net_income"), ("fcf", "fcf")]}
    cagr, fcf_cagr = None, None
    if len(annual) >= 3 and annual[0]["revenue"] > 0:
        n = len(annual) - 1
        cagr = round(((annual[-1]["revenue"] / annual[0]["revenue"]) ** (1 / n) - 1) * 100, 1)
        f0, f1 = annual[0].get("fcf"), annual[-1].get("fcf")
        if f0 and f1 and f0 > 0 and f1 > 0:
            fcf_cagr = round(((f1 / f0) ** (1 / n) - 1) * 100, 1)

    qrev = row(q, "Total Revenue")
    quarters = [dict(period_end=str(c.date()), revenue=float(qrev[c])) for c in (qrev.dropna().index[:6][::-1] if qrev is not None else [])]

    # free cash flow: last 4 reported quarters if available, else the last fiscal year
    fcf_q = row(qcf, "Free Cash Flow")
    fcf_ttm, fcf_basis = None, None
    if fcf_q is not None and fcf_q.dropna().shape[0] >= 4:
        fcf_ttm, fcf_basis = float(fcf_q.dropna().iloc[:4].sum()), "last 4 reported quarters"
    elif last.get("fcf") is not None:
        fcf_ttm, fcf_basis = last["fcf"], f"fiscal year to {last['period_end']}"

    sun = dt.date.fromisoformat(sunday)
    hist = t.history(start=str(sun - dt.timedelta(days=365 * 5 + 10)), end=str(sun), auto_adjust=True)["Close"]
    spx = yf.Ticker("^GSPC").history(start=str(sun - dt.timedelta(days=365 * 5 + 10)), end=str(sun), auto_adjust=True)["Close"]
    price = float(hist.iloc[-1])
    wk = hist.resample("W-FRI").last().dropna()
    sw = spx.resample("W-FRI").last().dropna().reindex(wk.index).ffill()
    chart = [dict(week=str(i.date()), stock=round(float(a / wk.iloc[0] * 100), 1), spx=round(float(b / sw.iloc[0] * 100), 1))
             for i, a, b in zip(wk.index, wk, sw)]

    def perf(days):
        past = hist[hist.index <= hist.index[-1] - pd.Timedelta(days=days)]
        return round((price / float(past.iloc[-1]) - 1) * 100, 1) if len(past) else None

    mcap = float(info.get("marketCap") or price * (info.get("sharesOutstanding") or 0))
    cash, debt = float(info.get("totalCash") or 0), float(info.get("totalDebt") or 0)
    ev = mcap + debt - cash
    ig = implied_growth(fcf_ttm, ev) if fcf_ttm else None

    nxt = None
    try:
        cal = t.calendar or {}
        ed = [x for x in (cal.get("Earnings Date") or []) if x >= sun]
        nxt = str(ed[0]) if ed else None
    except Exception:
        pass

    out = dict(
        ticker=ticker, name=info.get("longName") or members[ticker][0], sector=members[ticker][1], industry=members[ticker][2],
        sunday=sunday, as_of_close=str(hist.index[-1].date()), price=round(price, 2), market_cap=mcap,
        cash=cash, debt=debt, enterprise_value=ev,
        pe_trailing=round(info["trailingPE"], 1) if info.get("trailingPE") else None,
        pe_forward=round(info["forwardPE"], 1) if info.get("forwardPE") else None,
        dividend_yield=round(info["dividendYield"], 2) if info.get("dividendYield") else None,
        week52=[info.get("fiftyTwoWeekLow"), info.get("fiftyTwoWeekHigh")],
        perf_1y=perf(365), perf_5y=round(chart[-1]["stock"] - 100, 1) if chart else None,
        chart_start=chart[0]["week"] if chart else None,
        annual=annual, revenue_cagr=cagr, fcf_cagr=fcf_cagr, cagr_years=len(annual) - 1, margins=margins, quarters=quarters,
        fcf_ttm=fcf_ttm, fcf_basis=fcf_basis,
        implied_growth=ig, assumptions=dict(discount_rate=DISCOUNT * 100, terminal_growth=TERMINAL * 100, years=YEARS),
        next_earnings=nxt, price_chart=chart,
        shares_out=info.get("sharesOutstanding"), employees=info.get("fullTimeEmployees"),
        latest_quarter_in_data=quarters[-1]["period_end"] if quarters else None,
        business_summary=info.get("longBusinessSummary", ""),
        source="Yahoo Finance (company financials, prices)",
    )
    d = ROOT / "posts" / sunday; d.mkdir(parents=True, exist_ok=True)
    (d / "deepdive_data.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    print(f"{ticker} {out['name']}: price {price:.2f}, mcap {mcap/1e9:.0f}B, revenue CAGR {cagr}% over {len(annual)-1}y, "
          f"FCF {fcf_ttm and fcf_ttm/1e9:.1f}B ({fcf_basis}), implied growth {ig}%")
    print("margins", margins, "| next earnings", nxt, "| 1y", out["perf_1y"], "5y", out["perf_5y"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
