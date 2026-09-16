2026-09-16 13:14
Article and cluster `summary` fields now come back as bullet points (PR #12). Deliberately kept the field a **string** holding `- ` lines joined by `\n` rather than switching to an array — `data/*.json` is a public contract other sites fetch, so a type change breaks every consumer.

Added `_as_bullets()` in `pipeline_openrouter.py` because the model mixes `-`, `*`, `•` and numbered lists, and sometimes returns an array. A marker-less paragraph stays one bullet; don't try sentence-splitting Vietnamese prose. Prompt wording is unverified against the live model — no API key locally, the normalizer is the guarantee.

`daily_recap` left as prose on purpose; `full_summary` is narrative by design.

Dedup fix from earlier today is confirmed working in production: the 2026-09-16 crawl published 12 articles with **0 previously-published URLs**, all 1–2 days old except one at 13 days from a `max_age_days: 14` source. Ledger grew 1404 → 1836.

Gotcha found: `sources.yaml` has 54 entries but only **35 are active** — `_count_sources()` and `load_sources()` both filter on `active`. The dedup PR's diagram said "54 active"; corrected in #12.
