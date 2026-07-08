# Veen — Development Roadmap

Organized into four phases, each delivering a usable increment. Effort estimates assume solo development at ~1–2 hours per evening.

> **Note (2026-07-08)**: This roadmap documents the original build plan, including the SvelteKit frontend from Phase 0/3. The frontend was later removed — see [ADR-007](adr/ADR-007-remove-frontend.md). Kept here as historical record; the frontend-related items below no longer reflect the current architecture.

---

## Phase 0 — Foundation (Week 1)

**Goal**: Repo structure is in place, dependencies are declared, GitHub Actions skeleton is wired, and the SvelteKit project scaffolds correctly. Nothing crawls yet.

### Deliverables

- [ ] Repo structure: `src/veen/`, `data/`, `.github/workflows/`, `frontend/`
- [ ] `uv init` + `pyproject.toml` with deps: `feedparser`, `httpx`, `openai`, `pyyaml`, `python-dateutil`
- [ ] `data/sources.yaml` seeded with 5–10 sources (1–2 per major category)
- [ ] `.env.example` documenting `OPENROUTER_API_KEY` and `VEEN_AI_MODEL`
- [ ] GitHub Actions workflow skeleton: checkout + `uv sync` (no crawl logic yet)
- [ ] SvelteKit project scaffold with `@sveltejs/adapter-static`
- [ ] Cloudflare Pages project connected to the repo, auto-deploy on push to `main`
- [ ] `data/index.json` placeholder file so the frontend has something to fetch

### Effort Estimate

3–5 hours. Mostly scaffolding and YAML.

### Key Risks

- Cloudflare Pages auto-deploy configuration requires a `pnpm build` command and correct output directory (`frontend/build`). Verify this before moving to Phase 1.
- GitHub Actions `schedule:` cron triggers have up to 15-minute delays during high-load periods on GitHub's infrastructure. For a daily job this is irrelevant, but worth knowing.

---

## Phase 1 — Crawler MVP (Week 2)

**Goal**: Articles are fetched daily, deduplicated, written as JSON, committed, and displayed in a minimal frontend. No AI yet.

### Deliverables

- [ ] `veen/crawl.py`: read `data/sources.yaml`, fetch each feed with `feedparser` + `httpx`, deduplicate by URL
- [ ] `veen/export.py`: write raw (unprocessed) articles to `data/daily/YYYY-MM-DD.json` and `data/latest.json`
- [ ] `veen/export.py`: update `data/index.json` with the new daily entry
- [ ] GitHub Actions workflow: run `veen.crawl` + `veen.export`, commit if diff is non-empty
- [ ] SvelteKit `+page.svelte`: fetch `data/latest.json` from `raw.githubusercontent.com`, render a flat list of article titles with links
- [ ] End-to-end test: manually trigger the workflow, confirm `data/daily/YYYY-MM-DD.json` is committed and the frontend shows articles

### Effort Estimate

5–8 hours. The feedparser + httpx fetch logic is straightforward. The git commit step in the workflow needs care to avoid issues with the `GITHUB_TOKEN` permissions.

### Key Risks

- Some feeds require a proper `User-Agent` header or redirect to a mobile/desktop page — handle both in `httpx` client config.
- `raw.githubusercontent.com` returns correct CORS headers for JSON files, but test this in a real browser to confirm before building further UI on top of it.

---

## Phase 2 — AI Pipeline (Week 3)

**Goal**: Articles are filtered, scored, clustered, and summarized via OpenRouter. Output quality improves significantly.

### Deliverables

- [ ] `veen/ai_pipeline.py`: OpenRouter integration using `openai` SDK with `base_url="https://openrouter.ai/api/v1"`
- [ ] **Filter pass**: send batches of 20–30 article titles + snippets, receive keep/reject decisions; discard rejected articles
- [ ] **Score pass**: receive relevance score (0.0–1.0) per article; articles below threshold (e.g., 0.4) are dropped
- [ ] **Cluster pass**: group articles covering the same story; each article gets a `cluster_id`
- [ ] **Summarize pass**: one AI-generated 2–3 sentence summary per cluster; standalone articles summarized individually
- [ ] `data/daily/YYYY-MM-DD.json` now includes `clusters` array and AI-generated summaries on all articles
- [ ] `VEEN_AI_MODEL` env var wired through — default `deepseek/deepseek-v4-flash`
- [ ] Pipeline stats logged to stdout: fetched count, after-filter count, published count, clusters formed

### Effort Estimate

8–12 hours. The feedparser integration is fast; prompt engineering for filtering and clustering requires iteration against real feed data.

### Key Risks

- Batching is critical — sending 200 articles one-by-one to OpenRouter would take 10+ minutes and cost more. Batch at 20–30 per call from the start.
- Clustering quality depends on prompt design. Run the first few days with a low score threshold and review results manually before tightening filters.
- Context window: 30 article titles + snippets typically fits in 4K tokens. Verify the chosen model's limit and chunk accordingly.

---

## Phase 3 — Frontend Polish + Recaps (Weeks 4–5)

**Goal**: Usable daily reading experience with topic tabs; weekly and monthly recaps generated and accessible.

### Deliverables

- [ ] **Weekly recap workflow** (`.github/workflows/recaps.yml`): runs every Monday at 02:00 UTC, writes `data/weekly/YYYY-WW.json`
- [ ] **Monthly recap workflow**: runs on the 1st of each month, writes `data/monthly/YYYY-MM.json`
- [ ] `data/index.json` updated with weekly/monthly entries
- [ ] **Frontend — topic tabs**: filter articles by category (Technology, AI, DevOps, etc.) without a page reload
- [ ] **Frontend — article card**: title, source badge, score indicator (color-coded: green/yellow/red), AI summary, "Read original" link
- [ ] **Frontend — weekly page** (`/weekly`): renders the latest weekly recap
- [ ] **Frontend — monthly page** (`/monthly`): renders the latest monthly recap
- [ ] **Frontend — history browser**: date picker or list to browse past daily/weekly/monthly digests using `data/index.json`
- [ ] Error state in frontend: if `latest.json` fetch fails, show last cached result + error banner
- [ ] GitHub Actions email notification already works on job failure — verify the repo owner email is set in GitHub account settings

### Effort Estimate

10–15 hours. The recap workflows reuse the same pattern as the daily crawl. The frontend topic tabs and history browser are the most time-consuming UI pieces.

### Key Risks

- Weekly/monthly recap prompts need to handle larger inputs (aggregating 7–30 days of data). Use hierarchical summarization — summarize daily recaps into weekly, weekly into monthly — rather than re-processing raw articles. This keeps each AI call within context limits.
- jsDelivr CDN caching: files at `cdn.jsdelivr.net/gh/...` are cached aggressively. If the frontend switches to jsDelivr URLs, use commit-hash-pinned paths for `latest.json` to avoid stale cache hits, or keep using `raw.githubusercontent.com` for freshness.

---

## Milestone Summary

| Phase | Duration | Key Output | Success Criteria |
|-------|----------|------------|-----------------|
| 0 | Week 1 | Scaffolding | GitHub Actions runs without error; Cloudflare Pages deploys the frontend |
| 1 | Week 2 | Working crawler | Daily JSON committed; frontend renders article list |
| 2 | Week 3 | AI pipeline | Articles have summaries and scores; clusters visible in JSON |
| 3 | Weeks 4–5 | Full product | Topic tabs, weekly/monthly recaps, history browser all working |
