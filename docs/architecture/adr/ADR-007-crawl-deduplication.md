# ADR-007 — Crawl Deduplication: Persistent URL Ledger + Freshness Window

**Status**: Accepted
**Date**: 2026-09-16

---

## Context

The crawler deduplicated by scanning the **last 7 daily files** for URLs already
published. A URL that fell out of that window was re-admitted, re-summarized and
re-published as if new.

Measured across the first 89 days of `data/daily/` (2,053 article rows, 1,404
unique URLs):

- **649 rows (32%) were repeats** of a URL published on an earlier day
- the gap between repeat appearances was **never 1–7 days**, and **299 times exactly 8**

```
day 1   ●  published        ┌── 7-day memory ──┐
day 2-7 ·  skipped
day 8   ●  RE-PUBLISHED  ◀── memory expired
day 9-15 · skipped
day 16  ●  RE-PUBLISHED  ◀── and again, forever
```

That histogram is the diagnosis: the window length *was* the bug. The pressure
came from low-volume vendor blogs whose RSS feeds hold 30 entries spanning
months — Hugging Face (187 duplicate rows), Kubernetes (187), HashiCorp (139),
Cloudflare (100), GitLab (84), OpenAI (82). Every crawl re-read the same
back-catalogue. Supporting symptom: **41% of published articles were already
more than 7 days old** at export time, median age 2 days, maximum 1,629.

Two further problems with the old scheme:

- The skip-list was built from **published** articles only. Everything the AI
  filter rejected was invisible to it, so those articles were re-fetched and
  re-scored against OpenRouter every single day.
- It scaled with file reads: 7 JSON files parsed on every run to answer one
  membership question.

---

## Decision

Two independent mechanisms, in this order:

```
fetch feed
    │
    ▼
┌─────────────────────────────┐
│ ① Freshness window          │  published_at within VEEN_MAX_AGE_HOURS (72h)
│    per-source max_age_days  │  → stale? drop, do NOT record
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ ② Seen ledger               │  data/state/seen.json, 90-day retention
│    sha256(url)[:16] → date  │  → known? drop
└─────────────────────────────┘
    │
    ▼
record URL in ledger ──▶ /tmp/veen-raw.json ──▶ AI pipeline
```

### ① Freshness window

Reject anything whose `published_at` is older than 72h at crawl time.

A **rolling window, not a calendar-day filter.** The crawl runs at 01:00 UTC, so
only 3.6% of historical rows were same-calendar-day while 39.5% were exactly one
day old. `published_at == today` would have deleted ~96% of the digest.

Per-source `max_age_days` widens it for blogs that publish less often than once
per 72h (applied to 20 low-volume sources). This is safe precisely because the
ledger, not the window, is what prevents duplication.

Undated and unparseable entries pass; the ledger still dedups them. Future dates
are treated as fresh — some feeds post-date entries.

### ② Seen ledger

`data/state/seen.json` maps `sha256(url)[:16]` → first-seen date, pruned at 90
days. Recorded at **crawl** time, so articles the AI filter rejects are never
re-scored.

Ordering matters: stale articles are dropped *before* the ledger write, so
widening the window later can still pick them up.

---

## Consequences

### Positive

- **Duplicates end.** A URL reaches the AI pipeline at most once in 90 days;
  beyond that the freshness window catches it, since it is by then months old.
- **Lower AI spend.** The dry run sends 488 articles to OpenRouter where the old
  crawl sent ~1,600, and rejected articles are no longer re-scored daily.
- **Digest is actually news.** No more 1,629-day-old articles in today's file.
- **O(1) membership check** against one file, replacing 7 JSON parses.
- **Git is the transaction boundary.** The ledger is written by `veen.crawl`, but
  a later step failing aborts the workflow before the commit — so the ledger
  rolls back with everything else.

### Negative

- **A new committed file.** `data/state/seen.json` is ~56KB for 1,404 entries and
  grows to roughly 1MB at steady state. Keys are hashed and `sort_keys` is on, so
  the daily diff is a handful of added lines.
- **Hashes are opaque.** "Why was this URL skipped?" needs a hash lookup rather
  than a grep. Accepted for the file-size and diff-noise win.
- **Thinner categories.** `ai` and `open_source` were partly propped up by
  recycled old posts. The `max_age_days` override recovers most of this
  (`ai` 3 → 26 articles in the dry run), but some days will be genuinely light.

### Risks

- **A corrupt ledger silently disables dedup for a day.** `SeenLedger.load()`
  logs and starts empty rather than failing the crawl — the freshness window
  still bounds the damage to 72h of articles.
- **Clock/timezone skew in feeds.** Some publishers emit local time with no
  offset; those are read as UTC, which can shift an entry by hours. Immaterial
  against a 72h window.

---

## Alternatives Considered

### Crawl only articles published on the current calendar day

The originally proposed fix. Measured against real data it would drop ~96% of
content, because the 01:00 UTC crawl sees yesterday's news as "yesterday".

**Rejected**: correct instinct, wrong unit. A rolling window achieves the intent
without gutting the digest.

### Just widen the window from 7 days to 90

One-line change, no new file.

**Rejected**: moves the cliff rather than removing it, and still requires parsing
90 daily files per run. It also does nothing about re-scoring AI-rejected
articles, which is where the token waste is.

### Content-hash / title similarity dedup

Would additionally catch the same story republished under a different URL.

**Rejected for now**: the measured problem is exact-URL repetition — duplicate
titles (290) and duplicate URLs (289) track each other almost exactly, so URL
identity captures essentially all of it. The AI clustering pass already merges
genuine cross-source retellings.

### SQLite state file

Proper indexes, atomic writes, cheap pruning.

**Rejected**: a binary file in git defeats ADR-001 — no readable diff, and merge
conflicts become unresolvable. JSON at this scale is fast enough.
