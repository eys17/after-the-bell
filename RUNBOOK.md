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

## 0b. Is today already handled? (retries)

The schedule fires every hour from 17:03 to 22:03 New York time, so that a run that
fails (for example because of a usage limit) is retried, up to 5 times. Each run first
checks whether an earlier run already finished or is still going:

```bash
D=$(TZ=America/New_York date +%F)
git fetch -q origin main
for f in PUBLISHED APPROVED BLOCKED; do
  git cat-file -e origin/main:posts/$D/$f 2>/dev/null && { echo "$D already $f - nothing to do"; exit 0; }
done
if git cat-file -e origin/main:posts/$D/RUNNING 2>/dev/null; then
  started=$(git show origin/main:posts/$D/RUNNING)
  age=$(( $(date -u +%s) - $(date -u -d "$started" +%s) ))
  [ "$age" -lt 3000 ] && { echo "another run started ${age}s ago - leaving it alone"; exit 0; }
fi
mkdir -p posts/$D && date -u +%FT%TZ > posts/$D/RUNNING
git add posts/$D/RUNNING && git commit -qm "Run started $D" && git pull -q --rebase origin main && git push -q origin main
```

- Already PUBLISHED, APPROVED or BLOCKED: stop quietly. Never post twice.
- RUNNING less than 50 minutes old: another run is working on it. Stop quietly.
- RUNNING older than that: the earlier run died (e.g. hit a limit). Carry on and redo the day.
- If this is the 22:03 run (the last try) and it fails, send a push notification that
  today was skipped.

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
  agent. Keep going: fix, rebuild, fresh review, up to **4 reviews** in total. A FIX is
  a to-do list, not a stop sign. If a reason can't be sourced, the fix is to rewrite it
  as "No company news." with what the data shows, not to give up on the post.
- If a reviewer's fix clashes with a code check (e.g. a field format), find another way to
  meet the reviewer's point within the check (reword, move or swap the item), and say so
  to the next reviewer.
- Block only if the 4th review is still not `PASS`, or something can't be fixed at all
  (bad data, no sources for the market story). Then write `posts/<date>/BLOCKED` with the
  reasons and the exact fixes still needed, commit, push, and send a push notification
  with those fixes. Nothing gets posted.

## 5. Approve and push

Only when `checks.txt` says PASS **and** `review.json` says PASS:

```bash
date -u +%FT%TZ > posts/<date>/APPROVED
git rm -q --cached posts/<date>/RUNNING 2>/dev/null; rm -f posts/<date>/RUNNING
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
