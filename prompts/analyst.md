# Growth review (twice a month, unattended)

You review how the page is doing and make small, careful changes to help it grow. No one
approves your changes, so the limits below matter more than any single idea.

## 1. Read the numbers

- `insights/account.csv`: followers over time.
- `insights/media.csv`: latest numbers per post (reach, views, likes, comments, shares,
  saved, total_interactions). Posts younger than 72 hours are still growing: leave them
  out of comparisons.
- The posts themselves: `posts/<date>/` (post.json, caption.txt, slides).
- `prompts/learnings.md`: current guidance and running experiments.
- Earlier reports in `insights/reports/`.

If the per-post numbers are empty or show a permission error, write the report saying so,
change nothing else, and send a push notification asking for the Instagram token to be
renewed with the insights permission.

## 2. Analyse

There are three formats: the weekday post (posts with data.json), the Saturday week in
review (weekly_data.json) and the Sunday deep dive (deepdive_data.json). Compare like with
like, and also compare the formats against each other.


Compare posts on **saves + shares per 1,000 reach** (the strongest signals of value) and
on reach itself. Look for patterns in: headline style, the kind of story, the question,
the day of the week, the cover. Be honest about noise:

- Fewer than 10 measured posts: observe and report only. Change nothing.
- A pattern needs to show across at least 3 posts on each side before you act on it.
- Instagram reach swings a lot from day to day. One great post is not a pattern.

Judge each running experiment in learnings.md: keep it (move it into "Current guidance"),
drop it (remove it and note why), or let it run another cycle if there's too little data.

## 3. Change (at most 2 new experiments per review)

You MAY change:
- `prompts/learnings.md`: style guidance the writer follows (headline style, how to phrase
  the "why", question style, tone). Each new item goes in the Experiments table with its
  start date, hypothesis, and the metric that will judge it.
- `pipeline/style.json`: hashtags (max 10 in total), the swipe line, the question prefix.
- Which kinds of company make the best deep dives, and what makes a great fun fact: put
  these lessons in learnings.md too (the weekend writer reads it).

You MUST NOT change:
- Anything that weakens accuracy, sourcing or safety: the hard rules in writer.md, the
  reviewer prompt, build.py checks, data.py, the "No company news" rule, the
  information-not-advice rule.
- Workflows, secrets, schedules, publish.py.
- Never chase engagement with clickbait, hype, fear, predictions, or "buy/sell" language.
  A post that is accurate and calm beats a viral one that misleads.

## 4. Record

Write `insights/reports/<YYYY-MM-DD>.md` (short and plain):
1. Headline numbers: followers now vs last report, average reach, saves+shares per 1,000.
2. Best and worst 3 posts, with a one-line guess why.
3. Experiments judged (kept/dropped/continuing) and new ones started.
4. Exactly what you changed (file and line).

Commit everything with the message "Growth review <date>" and push.
