# After the Bell: weekend run (Saturdays)

One Saturday run makes **two** posts:
- **Week in review**, dated Saturday: published as soon as it is approved.
- **Sunday deep dive**, dated Sunday: approved on Saturday, published by GitHub Actions on
  Sunday morning (New York time). The publish workflow refuses any post dated in the future.

It runs unattended: never ask a question. A post that can't pass every check is not posted.

## 0. Set up, and is the weekend already handled? (retries)

Setup is the same as RUNBOOK.md step 0. Then:

```bash
SAT=$(TZ=America/New_York date +%F); SUN=$(TZ=America/New_York date -d tomorrow +%F)
git fetch -q origin main
```

This task fires hourly from 09:03 to 14:03 New York time on Saturdays. For each of `$SAT`
and `$SUN`: if `posts/<date>/APPROVED`, `PUBLISHED` or `BLOCKED` exists on origin/main, that
post is done. Skip it. If both are done, stop quietly.

Lock: if `posts/$SAT/RUNNING` on origin/main holds a UTC time less than 50 minutes old,
another run is busy, so stop. Otherwise write the current UTC time there, then commit and push
it before starting, and remove it in the final commit.

If `python pipeline/weekly_data.py $SAT` exits 3 (no trading that week), write
`posts/$SAT/BLOCKED` ("no trading this week"). Still do the deep dive.

## 1. Data

```bash
python pipeline/weekly_data.py $SAT
# choose the company (prompts/writer_weekend.md, part B), then:
python pipeline/deepdive_data.py <TICKER> $SUN
```

## 2. Write

Follow `prompts/writer_weekend.md`: write `posts/$SAT/weekly_writing.json` and
`posts/$SUN/deepdive_writing.json`.

## 3. Build and check

```bash
python pipeline/build_weekly.py $SAT
python pipeline/build_deepdive.py $SUN
```

Fix whatever `checks.txt` lists and rebuild (up to 3 times). Never edit the build scripts,
their rules or the reviewer prompts to make a post pass. If the deep dive fails as a repeat,
pick a different company and rerun deepdive_data.py.

## 4. Independent review

Start a **separate agent** (Agent tool, general-purpose) and wait for it:

> You are the independent reviewer. Read /home/claude/after-the-bell/prompts/reviewer.md and
> then /home/claude/after-the-bell/prompts/reviewer_weekend.md, and review the posts in
> /home/claude/after-the-bell/posts/<SAT>/ and /home/claude/after-the-bell/posts/<SUN>/.
> Write review.json in each. Do not edit any other file.

What to do with each post's verdict:
- **PASS:** approve it.
- **FIX:** apply the fixes (unless a source shows a fix is wrong), rebuild, and run a
  **fresh** reviewer on that post once more.
- **Still not PASS:** write `posts/<date>/BLOCKED` with the reasons. Not posted.

## 5. Approve and push

For each post whose `checks.txt` is PASS and whose `review.json` verdict is PASS:

```bash
date -u +%FT%TZ > posts/<date>/APPROVED
```

Then remove `posts/$SAT/RUNNING`, run `git add posts`, commit "Weekend posts $SAT", then
`git pull --rebase -q origin main` and `git push origin main`. Saturday's post publishes
straight away. Sunday's waits for Sunday morning.

## 6. Report

Finish with a short summary: the week's headline, the fun fact, the deep-dive company and
why it was chosen, and which posts are approved or blocked. Send a push notification if
anything was blocked, or if this is the 14:03 run and a post still isn't approved.
