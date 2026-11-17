"""Step 3: merge the writer's words with the data, run the hard checks, render, write the caption.

usage: python pipeline/build.py <date>
reads  posts/<date>/data.json      (numbers - written by data.py, never by a model)
       posts/<date>/writing.json   (words - written by the writer)
writes posts/<date>/post.json, slide_1..5.jpg, caption.txt, checks.txt
exit 0 = all checks passed, 1 = a check failed (see checks.txt)

Every number on the slides comes from data.json. The writer cannot change a price,
a percentage or the order of the movers: build.py takes them from the data.
"""
import json, re, sys, subprocess, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHORT = {"Information Technology": "Tech", "Consumer Discretionary": "Consumer Discr.",
         "Communication Services": "Communication"}
LIMITS = {"headline": 44, "context": 150, "why": 135, "chart_title": 38, "question": 75,
          "watch_title": 26, "watch_text": 80}
# advice-style wording that must never appear (the page is information, not advice)
BANNED = [r"\byou should\b", r"\bwe recommend\b", r"\bbuy now\b", r"\bsell now\b", r"\bprice target\b",
          r"\bguarantee", r"\bcan'?t lose\b", r"\bnot too late\b", r"\bload up\b", r"\bto the moon\b",
          r"\bstrong buy\b", r"\bmust[- ]own\b", r"\bfree money\b", r"\bdon'?t miss\b"]
NO_NEWS = "No company news"
STYLE = json.loads((ROOT / "pipeline" / "style.json").read_text())


def main(day: str) -> int:
    d = ROOT / "posts" / day
    data = json.loads((d / "data.json").read_text())
    w = json.loads((d / "writing.json").read_text())
    problems: list[str] = []

    def limit(name, text, key=None):
        n = LIMITS[key or name]
        if not isinstance(text, str) or not text.strip():
            problems.append(f"{name}: missing")
        elif len(text) > n:
            problems.append(f"{name}: {len(text)} chars, limit {n}")

    limit("headline", w.get("headline"))
    limit("context", w.get("context"))
    limit("chart_title", w.get("chart_title"))
    limit("question", w.get("question"))
    if w.get("headline_em") and w["headline_em"] not in w.get("headline", ""):
        problems.append("headline_em: not a part of the headline")

    movers = {}
    for key in ("winners", "losers"):
        movers[key] = []
        for r in data[key]:
            entry = (w.get("why") or {}).get(r["ticker"])
            if not entry:
                problems.append(f"why[{r['ticker']}]: missing"); continue
            text, srcs = entry.get("text", ""), entry.get("sources") or []
            limit(f"why[{r['ticker']}]", text, "why")
            if not text.startswith(NO_NEWS) and not any(str(s).startswith("http") for s in srcs):
                problems.append(f"why[{r['ticker']}]: a reason needs at least one source URL (or start with '{NO_NEWS}')")
            movers[key].append(dict(ticker=r["ticker"], name=r["name"], chg=r["chg"], why=text))
    extra = set((w.get("why") or {})) - {r["ticker"] for k in ("winners", "losers") for r in data[k]}
    if extra:
        problems.append(f"why: tickers that are not today's top movers: {sorted(extra)}")

    watch = w.get("watch") or []
    if not 1 <= len(watch) <= 2:
        problems.append("watch: need 1 or 2 items")
    for i, it in enumerate(watch):
        limit(f"watch[{i}].title", it.get("title"), "watch_title")
        limit(f"watch[{i}].text", it.get("text"), "watch_text")
        if len(it.get("when", "")) > 4:
            problems.append(f"watch[{i}].when: use a short day like 'Tue'")
        if not str(it.get("source", "")).startswith("http"):
            problems.append(f"watch[{i}]: needs a source URL")

    all_text = " ".join([w.get("headline", ""), w.get("context", ""), w.get("question", ""), w.get("chart_title", "")]
                        + [m["why"] for k in movers for m in movers[k]] + [it.get("text", "") + " " + it.get("title", "") for it in watch])
    for pat in BANNED:
        if re.search(pat, all_text, re.I):
            problems.append(f"advice-style wording matched /{pat}/")

    idx = data["indices"]
    date = dt.date.fromisoformat(day)
    post = dict(
        brand="After the Bell", date=day, date_label=f"{date:%a} {date.day} {date:%b %Y}",
        headline=w.get("headline", ""), headline_em=w.get("headline_em", ""), context=w.get("context", ""),
        spx_close=idx["S&P 500"]["close"], spx_chg=idx["S&P 500"]["chg"],
        other_indices={k: v for k, v in idx.items() if k != "S&P 500"},
        breadth_up=data["breadth_up"], breadth_down=data["breadth_down"],
        winners=movers["winners"], losers=movers["losers"],
        sectors=[[SHORT.get(s, s), v] for s, v in data["sectors"]],
        sector_note="Median move of stocks in each S&P 500 sector", chart_title=w.get("chart_title", ""),
        watch=watch, question=w.get("question", ""),
    )
    (d / "post.json").write_text(json.dumps(post, indent=1, ensure_ascii=False))

    if not problems:
        r = subprocess.run([sys.executable, str(ROOT / "pipeline" / "render.py"), str(d / "post.json"), str(d)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("render: " + (r.stdout + r.stderr).strip()[-600:])
        elif len(list(d.glob("slide_*.jpg"))) != 5:
            problems.append("render: expected 5 slides")

    def p(x):
        return f"{'+' if x > 0 else '−'}{abs(x):.2f}%"
    tags = " ".join(f"#{m['ticker'].replace('-', '')}" for k in movers for m in movers[k])
    caption = "\n".join([
        f"{post['headline']} 📉" if post["spx_chg"] < 0 else f"{post['headline']} 📈",
        "",
        f"S&P 500 {p(post['spx_chg'])} · " + " · ".join(f"{k} {p(v['chg'])}" for k, v in post["other_indices"].items()),
        "",
        "🟢 " + " · ".join(f"${m['ticker']} {p(m['chg'])}" for m in movers["winners"]),
        "🔴 " + " · ".join(f"${m['ticker']} {p(m['chg'])}" for m in movers["losers"]),
        "",
        STYLE["swipe_line"],
        "",
        f"{STYLE['question_prefix']}{post['question']}",
        "",
        "For information only, not financial advice. Data: Yahoo Finance.",
        "",
        STYLE["hashtags"] + (" " + tags if STYLE.get("add_ticker_hashtags", True) else ""),
    ])
    if len(caption) > 2100:
        problems.append(f"caption: {len(caption)} chars, Instagram allows 2200")
    if len(re.findall(r"#\w+", caption)) > 30:
        problems.append("caption: more than 30 hashtags")
    (d / "caption.txt").write_text(caption)

    (d / "checks.txt").write_text("PASS\n" if not problems else "FAIL\n" + "\n".join(f"- {x}" for x in problems) + "\n")
    print((d / "checks.txt").read_text().strip())
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
