"""Weekend step 3a: merge words with numbers, check, render and caption the "Week in review".

usage: python pipeline/build_weekly.py <saturday>
reads  posts/<sat>/weekly_data.json (numbers, by code) + posts/<sat>/weekly_writing.json (words)
writes posts/<sat>/post.json, slide_1..7.jpg, caption.txt, checks.txt   -> exit 0 PASS / 1 FAIL
"""
import json, re, sys, subprocess, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from build import BANNED, NO_NEWS, SHORT, STYLE  # same advice ban and rules as the daily post

LIMITS = {"headline": 40, "days_title": 34, "numbers_title": 34, "day_label": 34, "why": 105,
          "fun_fact": 190, "question": 75, "watch_title": 26, "watch_text": 80, "context": 160}


def main(sat: str) -> int:
    d = ROOT / "posts" / sat
    data = json.loads((d / "weekly_data.json").read_text())
    w = json.loads((d / "weekly_writing.json").read_text())
    problems = []

    def limit(name, text, key=None):
        n = LIMITS[key or name]
        if not isinstance(text, str) or not text.strip():
            problems.append(f"{name}: missing")
        elif len(text) > n:
            problems.append(f"{name}: {len(text)} chars, limit {n}")

    for k in ("headline", "days_title", "numbers_title", "question", "context"):
        limit(k, w.get(k))
    if w.get("headline_em") and w["headline_em"] not in w.get("headline", ""):
        problems.append("headline_em: not a part of the headline")

    ff = w.get("fun_fact") or {}
    limit("fun_fact.text", ff.get("text"), "fun_fact")
    if not str(ff.get("source", "")).startswith("http") or not ff.get("source_name"):
        problems.append("fun_fact: needs a source URL and a short source_name (e.g. 'Reuters')")

    labels = w.get("day_labels") or {}
    days = []
    for x in data["spx_days"]:
        lab = labels.get(x["date"])
        limit(f"day_labels[{x['date']}]", lab, "day_label")
        days.append({**x, "label": lab or ""})
    if set(labels) - {x["date"] for x in data["spx_days"]}:
        problems.append("day_labels: dates that were not trading sessions this week")

    movers = {}
    for key in ("winners", "losers"):
        movers[key] = []
        for r in data[key]:
            ent = (w.get("why") or {}).get(r["ticker"])
            if not ent:
                problems.append(f"why[{r['ticker']}]: missing"); continue
            text, srcs = ent.get("text", ""), ent.get("sources") or []
            limit(f"why[{r['ticker']}]", text, "why")
            if not text.startswith(NO_NEWS) and not any(str(s).startswith("http") for s in srcs):
                problems.append(f"why[{r['ticker']}]: needs a source URL (or start with '{NO_NEWS}')")
            movers[key].append(dict(ticker=r["ticker"], name=r["name"], chg=r["chg"], why=text))
    extra = set(w.get("why") or {}) - {r["ticker"] for k in ("winners", "losers") for r in data[k]}
    if extra:
        problems.append(f"why: tickers that are not this week's top movers: {sorted(extra)}")

    watch = w.get("watch") or []
    if not 2 <= len(watch) <= 3:
        problems.append("watch: need 2 or 3 items")
    for i, it in enumerate(watch):
        limit(f"watch[{i}].title", it.get("title"), "watch_title")
        limit(f"watch[{i}].text", it.get("text"), "watch_text")
        if len(it.get("when", "")) > 4:
            problems.append(f"watch[{i}].when: use a short day like 'Wed'")
        if not str(it.get("source", "")).startswith("http"):
            problems.append(f"watch[{i}]: needs a source URL")

    text = " ".join([w.get("headline", ""), w.get("context", ""), w.get("question", ""), ff.get("text", ""),
                     w.get("days_title", ""), w.get("numbers_title", "")] + list(labels.values())
                    + [m["why"] for k in movers for m in movers[k]] + [it.get("title", "") + " " + it.get("text", "") for it in watch])
    for pat in BANNED:
        if re.search(pat, text, re.I):
            problems.append(f"advice-style wording matched /{pat}/")

    ws, we = dt.date.fromisoformat(data["week_start"]), dt.date.fromisoformat(data["week_end"])
    satd = dt.date.fromisoformat(sat)
    base_close = data["spx_days"][0]["close"] / (1 + data["spx_days"][0]["chg"] / 100)
    post = dict(
        kind="weekly", brand="After the Bell", date=sat, date_label=f"{satd:%a} {satd.day} {satd:%b %Y}",
        week_label=f"{ws.day}–{we.day} {we:%b}" if ws.month == we.month else f"{ws.day} {ws:%b} – {we.day} {we:%b}",
        headline=w.get("headline", ""), headline_em=w.get("headline_em", ""), context=w.get("context", ""),
        indices=data["indices"], spx_days=days, base_close=round(base_close, 2), sessions=data["sessions"],
        winners=movers["winners"], losers=movers["losers"],
        stats={**data["stats"], "best_sector": [SHORT.get(data["stats"]["best_sector"][0], data["stats"]["best_sector"][0]), data["stats"]["best_sector"][1]],
               "worst_sector": [SHORT.get(data["stats"]["worst_sector"][0], data["stats"]["worst_sector"][0]), data["stats"]["worst_sector"][1]]},
        fun_fact=ff, days_title=w.get("days_title", ""), numbers_title=w.get("numbers_title", ""),
        watch=watch, question=w.get("question", ""),
    )
    (d / "post.json").write_text(json.dumps(post, indent=1, ensure_ascii=False))

    if not problems:
        r = subprocess.run([sys.executable, str(ROOT / "pipeline" / "render_weekly.py"), str(d / "post.json"), str(d)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("render: " + (r.stdout + r.stderr).strip()[-600:])
        elif len(list(d.glob("slide_*.jpg"))) != 7:
            problems.append("render: expected 7 slides")

    def p(x):
        return f"{'+' if x > 0 else '−'}{abs(x):.2f}%"
    sp = post["indices"]["S&P 500"]
    tags = " ".join(f"#{m['ticker'].replace('-', '')}" for k in movers for m in movers[k][:3])
    caption = "\n".join([
        f"Week in review: {post['headline']} {'📈' if sp['chg'] >= 0 else '📉'}", "",
        f"S&P 500 {p(sp['chg'])} this week · " + " · ".join(f"{k} {p(v['chg'])}" for k, v in post["indices"].items() if k != "S&P 500"), "",
        post["context"], "",
        "🟢 " + " · ".join(f"${m['ticker']} {p(m['chg'])}" for m in movers["winners"][:3]),
        "🔴 " + " · ".join(f"${m['ticker']} {p(m['chg'])}" for m in movers["losers"][:3]), "",
        "Swipe for this week's fun fact 💡, the day-by-day, and what's coming next →", "",
        f"{STYLE['question_prefix']}{post['question']}", "",
        "For information only, not financial advice. Data: Yahoo Finance.", "",
        STYLE["hashtags"] + " #weekinreview " + tags,
    ])
    if len(caption) > 2100:
        problems.append(f"caption: {len(caption)} chars")
    (d / "caption.txt").write_text(caption)
    (d / "checks.txt").write_text("PASS\n" if not problems else "FAIL\n" + "\n".join(f"- {x}" for x in problems) + "\n")
    print((d / "checks.txt").read_text().strip())
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
