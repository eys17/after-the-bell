"""Step 5 (runs in GitHub Actions, not in the Claude session): post an approved carousel to Instagram.

usage: python pipeline/publish.py <date>
needs env: IG_USER_ID, IG_ACCESS_TOKEN, GITHUB_REPOSITORY, GITHUB_SHA
Posts only when posts/<date>/APPROVED exists and PUBLISHED does not, and the post is
at most 2 days old. Writes posts/<date>/PUBLISHED with the media id and permalink.
"""
import json, os, sys, time, datetime as dt
from pathlib import Path
import urllib.request, urllib.parse, urllib.error

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v25.0"


def api_base() -> str:
    """Facebook-login tokens (EAA...) use graph.facebook.com; Instagram-login tokens (IG...) use graph.instagram.com."""
    tok = os.environ["IG_ACCESS_TOKEN"]
    return f"https://graph.facebook.com/{VERSION}" if tok.startswith("EAA") else f"https://graph.instagram.com/{VERSION}"


def call(method: str, path: str, **params) -> dict:
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{api_base()}/{path}"
    req = urllib.request.Request(url + ("?" + data.decode() if method == "GET" else ""),
                                 data=None if method == "GET" else data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:800]
        raise SystemExit(f"Instagram API error on {path}: {e.code} {body}".replace(os.environ["IG_ACCESS_TOKEN"], "***"))


def wait_ready(cid: str) -> None:
    for _ in range(30):
        s = call("GET", cid, fields="status_code").get("status_code")
        if s == "FINISHED":
            return
        if s in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container {cid} status {s}")
        time.sleep(10)
    raise SystemExit(f"container {cid} not ready after 5 minutes")


def check() -> int:
    """Connection test: confirms the token can see the account. Posts nothing."""
    uid = os.environ["IG_USER_ID"]
    me = call("GET", uid, fields="username")
    lim = call("GET", f"{uid}/content_publishing_limit", fields="quota_usage,config")
    print(f"connected to @{me.get('username')} via {api_base().split('/')[2]}; publishing quota: {lim.get('data')}")
    return 0


def main(day: str) -> int:
    d = ROOT / "posts" / day
    if (d / "PUBLISHED").exists():
        print(day, "already published - nothing to do"); return 0
    if not (d / "APPROVED").exists():
        print(day, "not approved - refusing to post"); return 1
    age = (dt.date.today() - dt.date.fromisoformat(day)).days
    if age > 2:
        print(day, f"is {age} days old - too stale to post"); return 1
    slides = sorted(d.glob("slide_*.jpg"), key=lambda p: int(p.stem.split("_")[1]))
    if len(slides) != 5:
        print("expected 5 slides, found", len(slides)); return 1
    caption = (d / "caption.txt").read_text()
    repo, sha, uid = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_SHA"], os.environ["IG_USER_ID"]
    urls = [f"https://raw.githubusercontent.com/{repo}/{sha}/posts/{day}/{p.name}" for p in slides]

    children = []
    for u in urls:
        cid = call("POST", f"{uid}/media", image_url=u, is_carousel_item="true")["id"]
        wait_ready(cid); children.append(cid)
    carousel = call("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    wait_ready(carousel)
    media = call("POST", f"{uid}/media_publish", creation_id=carousel)["id"]
    link = call("GET", media, fields="permalink").get("permalink", "")
    (d / "PUBLISHED").write_text(json.dumps({"media_id": media, "permalink": link,
                                             "published_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}, indent=1))
    print("published", day, link)
    return 0


if __name__ == "__main__":
    sys.exit(check() if sys.argv[1] == "--check" else main(sys.argv[1]))
