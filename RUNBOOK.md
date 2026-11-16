# After the Bell: daily run

This is what the scheduled session does every weekday after the US close. It runs with
no one watching, so it never stops to ask a question: it either publishes a post that
has passed every check, or publishes nothing and says why.

## 0. Set up (fresh container each run)

```bash
cd /home/claude/after-the-bell        # the repo clone
pip install --break-system-packages -q -r requirements.txt
npm ci --silent
python -m playwright install chromium 2>/dev/null || true   # skip if Chromium is preinstalled
```

## 1. Data

```bash
python pipeline/data.py            # today's New York date
```

- exit 3: the market was closed today (holiday). Stop. Nothing to post.
- exit 4: the session hasn't closed yet. Stop. (The schedule is wrong; say so.)
- exit 1: data problem. Stop, do not post, report it.

## 2. Write

Follow `prompts/writer.md` and write `posts/<date>/writing.json`.

## 3. Build and check

```bash
python pipeline/build.py <date>
```

If it prints FAIL, fix `writing.json` to satisfy each listed problem and run it again
(up to 3 times). Code checks are never skipped or edited to make a post pass.

## 4. Independent review

Start a **separate agent** (Agent tool, general-purpose) with this prompt, filling in the
date, and wait for it:

> You are the independent reviewer. Read /home/claude/after-the-bell/prompts/reviewer.md and review the post in
> /home/claude/after-the-bell/posts/<date>/. Write review.json there as it describes. Do not edit any other file.

- `PASS` → go to step 5.
- `FIX` → apply its fixes to `writing.json` (you may decide a fix is wrong, but only if
  you can show from a source that it is), re-run `build.py`, and run a **fresh** reviewer
  agent once more.
- Still not `PASS` after the second review → write `posts/<date>/BLOCKED` with the
  reasons, commit, push, and stop. Nothing gets posted.

## 5. Approve and push

Only when `checks.txt` says PASS **and** `review.json` says PASS:

```bash
date -u +%FT%TZ > posts/<date>/APPROVED
git add posts/<date> pipeline/sp500.csv
git commit -m "After the Bell <date>"
git pull --rebase -q origin main && git push origin main
```

Pushing APPROVED makes GitHub Actions post the carousel to Instagram
(`.github/workflows/publish.yml`). The workflow refuses posts without APPROVED, posts
older than 2 days, and anything already published.

## 6. Report

Finish with a short message: posted or not, the headline, and anything odd. If the post
was blocked or a step failed, send a push notification saying so.

## Rules that never bend

- Numbers come from `data.json` only. Never type a price or percentage yourself.
- A reason you can't source starts with "No company news." Never guess.
- Information, not advice. Nothing that tells anyone to buy or sell.
- When unsure, don't post. A missed day costs nothing; a wrong post costs trust.
