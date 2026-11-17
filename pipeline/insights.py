"""Collect Instagram engagement numbers (runs in GitHub Actions).

usage: python pipeline/insights.py
needs env: IG_USER_ID, IG_ACCESS_TOKEN
writes insights/media.csv   (latest numbers for every published post, rewritten each run)
       insights/account.csv (followers over time, one row appended per run)
"""
import csv, json, sys, datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish import call  # same API helper, token redacted in errors

ROOT = Path(__file__).resolve().parents[1]
METRICS = ["reach", "views", "likes", "comments", "shares", "saved", "total_interactions"]


def main() -> int:
    uid = __import__("os").environ["IG_USER_ID"]
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    out = ROOT / "insights"; out.mkdir(exist_ok=True)

    acc = call("GET", uid, fields="followers_count,media_count")
    new = not (out / "account.csv").exists()
    with open(out / "account.csv", "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["snapshot_utc", "followers", "posts"])
        w.writerow([now, acc.get("followers_count"), acc.get("media_count")])

    rows = []
    for pub in sorted(ROOT.glob("posts/*/PUBLISHED")):
        info = json.loads(pub.read_text())
        mid = info["media_id"]
        vals = {}
        try:
            data = call("GET", f"{mid}/insights", metric=",".join(METRICS)).get("data", [])
            vals = {m["name"]: (m.get("values") or [{}])[0].get("value", m.get("total_value", {}).get("value")) for m in data}
        except SystemExit as exc:  # e.g. a metric not available for this post yet
            vals = {"error": str(exc)[:200]}
        age_h = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(info["published_utc"])).total_seconds() / 3600
        rows.append({"post_date": pub.parent.name, "media_id": mid, "published_utc": info["published_utc"],
                     "age_hours": round(age_h), **{m: vals.get(m) for m in METRICS}, "error": vals.get("error", "")})
    with open(out / "media.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["post_date", "media_id", "published_utc", "age_hours", *METRICS, "error"])
        w.writeheader(); w.writerows(rows)
    print(f"followers {acc.get('followers_count')}; {len(rows)} posts measured; errors: {sum(1 for r in rows if r['error'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
