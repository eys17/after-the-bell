"""Weekend step 3b: merge words with numbers, check, render and caption the Sunday deep dive.

usage: python pipeline/build_deepdive.py <sunday>
reads  posts/<sun>/deepdive_data.json (numbers, by code) + posts/<sun>/deepdive_writing.json (words)
writes posts/<sun>/post.json, slide_1..10.jpg, caption.txt, checks.txt   -> exit 0 PASS / 1 FAIL
"""
import json, re, sys, subprocess, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from build import BANNED, STYLE

NO_REPEAT_WEEKS = 12   # a company is never deep-dived twice within this many weeks
# on top of the daily advice ban: no verdicts on whether the price is right
VERDICT = [r"\bunder-?valued\b", r"\bover-?valued\b", r"\bbargain\b", r"\bcheap\b", r"\bfair value\b",
           r"\bintrinsic value\b", r"\bmispriced\b", r"\b(buy|sell|hold|avoid) (the|this|its)? ?(stock|shares)\b", r"\bown (the|this) (stock|shares)\b",
           r"\bshould (you )?(buy|sell|own|invest)\b", r"\bgood (buy|investment)\b", r"\bupside of\b"]
LIMITS = {"title": 40, "short_name": 18, "hook": 120, "what": 115, "take": 125, "take_assumes": 170,
          "case": 125, "question": 75, "watch_title": 26, "watch_text": 80, "why_this_company": 220}


def main(sun: str) -> int:
    d = ROOT / "posts" / sun
    data = json.loads((d / "deepdive_data.json").read_text())
    w = json.loads((d / "deepdive_writing.json").read_text())
    problems = []

    def limit(name, text, key=None):
        n = LIMITS[key or name]
        if not isinstance(text, str) or not text.strip():
            problems.append(f"{name}: missing")
        elif len(text) > n:
            problems.append(f"{name}: {len(text)} chars, limit {n}")

    def sourced(name, item, url_key="source"):
        if not str(item.get(url_key, "")).startswith("http") or not item.get("source_name"):
            problems.append(f"{name}: needs a source URL and a short source_name")

    if w.get("ticker", "").upper() != data["ticker"]:
        problems.append("ticker: writing and data are for different companies")

    # never repeat a company within NO_REPEAT_WEEKS
    sund = dt.date.fromisoformat(sun)
    for prev in ROOT.glob("posts/*/deepdive_data.json"):
        pd_ = dt.date.fromisoformat(prev.parent.name)
        if prev.parent.name != sun and json.loads(prev.read_text())["ticker"] == data["ticker"] and abs((sund - pd_).days) < NO_REPEAT_WEEKS * 7:
            problems.append(f"repeat: {data['ticker']} was already the deep dive on {pd_} (rule: not within {NO_REPEAT_WEEKS} weeks)")

    for k in ("title", "short_name", "hook", "question"):
        limit(k, w.get(k))
    why = w.get("why_this_company") or {}
    limit("why_this_company", why.get("text"))
    if not any(str(s).startswith("http") for s in why.get("sources", [])):
        problems.append("why_this_company: needs a source showing the company was in this week's news")
    wid = w.get("what_it_does") or []
    if not 3 <= len(wid) <= 4:
        problems.append("what_it_does: need 3 or 4 points")
    for i, x in enumerate(wid):
        limit(f"what_it_does[{i}]", x, "what")
    seg = w.get("segments")
    if seg:
        sourced("segments", seg)
        tot = sum(float(it.get("pct", 0)) for it in seg.get("items", []))
        if not 97 <= tot <= 103 or not 2 <= len(seg.get("items", [])) <= 6:
            problems.append(f"segments: 2-6 items whose shares add to 100 (now {tot:.1f})")
        if not seg.get("period"):
            problems.append("segments: needs the period it covers, e.g. 'FY2026'")
    tk = w.get("takeaways") or {}
    for k in ("price", "growth", "margins", "health"):
        limit(f"takeaways.{k}", tk.get(k), "take")
    limit("takeaways.assumes", tk.get("assumes"), "take_assumes")
    for side in ("bull", "bear"):
        items = w.get(side) or []
        if len(items) != 3:
            problems.append(f"{side}: need exactly 3 points (bull and bear always balanced)")
        for i, x in enumerate(items):
            limit(f"{side}[{i}]", x.get("text"), "case")
            sourced(f"{side}[{i}]", x)
    watch = w.get("watch") or []
    if not 2 <= len(watch) <= 3:
        problems.append("watch: need 2 or 3 items")
    for i, it in enumerate(watch):
        limit(f"watch[{i}].title", it.get("title"), "watch_title")
        limit(f"watch[{i}].text", it.get("text"), "watch_text")
        if len(it.get("when", "")) > 7:
            problems.append(f"watch[{i}].when: short, like 'Feb 25' or 'Q1'")
        if not str(it.get("source", "")).startswith("http"):
            problems.append(f"watch[{i}]: needs a source URL")

    text = " ".join([w.get("title", ""), w.get("hook", ""), w.get("question", "")] + wid + list(tk.values())
                    + [x.get("text", "") for s in ("bull", "bear") for x in (w.get(s) or [])]
                    + [it.get("title", "") + " " + it.get("text", "") for it in watch])
    for pat in BANNED + VERDICT:
        if re.search(pat, text, re.I):
            problems.append(f"advice or verdict wording matched /{pat}/")

    asof = dt.date.fromisoformat(data["as_of_close"])
    post = {**data, "kind": "deepdive", "brand": "After the Bell", "date": sun,
            "date_label": f"{sund:%a} {sund.day} {sund:%b %Y}", "as_of_label": f"{asof.day} {asof:%b %Y} close",
            "title": w.get("title", ""), "short_name": w.get("short_name", ""), "hook": w.get("hook", ""),
            "what_it_does": wid, "segments": seg, "takeaways": tk, "bull": w.get("bull", []), "bear": w.get("bear", []),
            "watch": watch, "question": w.get("question", "")}
    post.pop("business_summary", None)
    (d / "post.json").write_text(json.dumps(post, indent=1, ensure_ascii=False))

    if not problems:
        r = subprocess.run([sys.executable, str(ROOT / "pipeline" / "render_deepdive.py"), str(d / "post.json"), str(d)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("render: " + (r.stdout + r.stderr).strip()[-600:])
        elif len(list(d.glob("slide_*.jpg"))) != 10:
            problems.append("render: expected 10 slides")

    t = data["ticker"].replace("-", "")
    caption = "\n".join([
        f"Deep dive: {post['title']} 🔍", "",
        post["hook"], "",
        "Inside: what the business does, 5 years of the share price, sales and profit, how much it keeps, "
        "what today's price is betting on, and the bull and bear case →", "",
        f"{STYLE['question_prefix']}{post['question']}", "",
        "For information only, not financial advice. Data: Yahoo Finance and company reports.", "",
        STYLE["hashtags"] + f" #deepdive #stockanalysis #{t} ${data['ticker']}",
    ])
    (d / "caption.txt").write_text(caption)
    (d / "checks.txt").write_text("PASS\n" if not problems else "FAIL\n" + "\n".join(f"- {x}" for x in problems) + "\n")
    print((d / "checks.txt").read_text().strip())
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
