2026-09-16 09:48
Cross-day duplicate articles were caused by `crawl.seen_urls()` scanning only the last 7 daily files — repeat gaps were never 1-7 days and exactly 8 on 299 occasions (32% of all rows were repeats). Replaced with a permanent ledger at `data/state/seen.json` (hashed URL → first-seen date, 90d retention) plus a 72h rolling freshness window in `freshness.py`.

Deliberately not a calendar-day filter: the crawl runs 01:00 UTC, so only 3.6% of historical rows were same-day and 39.5% were exactly one day old — `published_at == today` would drop ~96% of content. Ledger is written at crawl time (not export) so AI-rejected articles stop being re-scored daily; stale articles are dropped *before* the ledger write so widening the window later can still pick them up.

Added `max_age_days: 14` to 20 low-volume vendor blogs; without it the `ai` category dry-ran at 3 articles instead of 26. `robotics` stays empty — both its sources are `active: false` (403/404), pre-existing.

Blocked: push failed. Repo is `quniv/veen-news` but both local SSH keys authenticate as `stsquinn`. Commit 7cb0752 sits on branch `worktree-crawl-dedup-ledger` in the shared object store. Needs the user's own `git push` + `gh pr create`.
