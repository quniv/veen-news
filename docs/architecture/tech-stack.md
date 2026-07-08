# Veen — Technology Stack

Every layer lists the chosen tool, the rationale, and two alternatives with a trade-off summary.

---

## Stack Decision Table

| Layer | Chosen | Why | Alt A | Alt B |
|-------|--------|-----|-------|-------|
| Compute | GitHub Actions | Free, no infra, scheduled cron | K8s CronJob (home) | Render cron (paid) |
| Data storage | JSON files in Git | Zero cost, versioned, CDN-ready | PostgreSQL | SQLite file |
| AI gateway | OpenRouter | Model-agnostic gateway — swap model via env var; OpenAI-compatible SDK | Direct Anthropic SDK | Ollama (local) |
| RSS parsing | feedparser + httpx | Battle-tested Python libraries | Scrapy | newspaper3k |
| Data delivery | GitHub raw URLs / jsDelivr CDN | Zero cost, global CDN | GitHub Pages | Cloudflare R2 |
| Source config | YAML in repo | Git-diffable, no UI needed | JSON | Database table |
| Secrets | GitHub Actions Secrets | Native, zero setup | Vault | .env (local only) |

---

## Layer Details

### Compute — GitHub Actions

GitHub Actions provides a hosted runner with 2000 free minutes/month for private repos (unlimited for public). A daily crawl job runs ~5–10 minutes, using roughly 300 minutes/month at most. The cron trigger (`schedule:`) requires no infrastructure and the job has full internet access to fetch RSS feeds and call OpenRouter.

**Alt A — Home K8s CronJob**: Works if the cluster is running, but introduces a home-infra dependency. If the home server is rebooted, has a power cut, or the cluster is misconfigured, the crawl silently fails. GitHub's infrastructure is more reliable than a home server for a scheduled daily job.

**Alt B — Render cron (paid)**: Render's cron jobs start at $7/month. They work well, but the point of this architecture is zero cost. No functional advantage over GitHub Actions justifies the spend.

---

### Data Storage — JSON files in Git

Article data is written as structured JSON files committed to the same repository. This gives versioned history, diffs on every change, free CDN delivery via `raw.githubusercontent.com` or jsDelivr, and zero operational overhead. No connection pooling, no migrations, no backups to manage.

See [ADR-001](adr/ADR-001-git-as-database.md) for the full decision record.

**Alt A — PostgreSQL**: Powerful for complex queries and relational integrity, but requires running a server somewhere. Either a paid managed database ($15–25/month for the cheapest tier) or a home K8s deployment (home-infra dependency). No SQL aggregation is needed — all "queries" are JSON reads done by consumers.

**Alt B — SQLite file in repo**: Closer to the "file in git" approach but binary format means git diffs are meaningless, merge conflicts are unresolvable, and the file cannot be served directly as a CDN asset. JSON is human-readable, diffable, and directly consumable by any consumer without any parsing layer.

---

### AI Gateway — OpenRouter

OpenRouter is an OpenAI-compatible HTTP gateway routing to 100+ models (DeepSeek, Claude, GPT-4o, Mistral, etc.). All LLM calls use the `openai` Python SDK with `base_url` set to the OpenRouter endpoint. The active model is controlled by `VEEN_AI_MODEL` (GitHub Actions variable) — swapping models requires no code changes.

Default model: `deepseek/deepseek-v4-flash` (~$0.14/1M tokens). A daily crawl processing 50–200 articles uses well under 100K tokens — cost is negligible.

See [ADR-003](adr/ADR-003-ai-gateway.md) and [ADR-006](adr/ADR-006-ai-agent-framework.md) for the full decision records.

**Alt A — Direct Anthropic SDK**: Locks the codebase to one provider. If a cheaper or better model from another provider becomes available, all LLM-calling code must be rewritten. The `anthropic` SDK and `openai` SDK have different method signatures, authentication patterns, and error types.

**Alt B — Ollama (local)**: Runs models locally — zero AI cost. However, local GPU hardware is required for any meaningful model quality. Running Ollama on CPU for 500 articles/day would take hours. The batch crawler pattern needs fast inference; managed APIs are the right fit.

---

### RSS Parsing — feedparser + httpx

`feedparser` handles RSS 0.9x, RSS 2.0, Atom 0.3, Atom 1.0, and RDF formats in a single unified call. `httpx` provides modern async HTTP with connection pooling, timeout control, redirect following, and HTTP/2. Together they cover all feed formats encountered in practice.

**Alt A — Scrapy**: Full-featured web scraping framework with middleware, pipelines, and JS rendering support via Splash. Significant overkill for fetching structured RSS feeds. Scrapy introduces its own async model (Twisted), which does not compose well with Python's native `asyncio`.

**Alt B — newspaper3k**: Designed for scraping full article text from HTML pages, not RSS feeds. Useful if full-text extraction is needed later, but for now the feed description/snippet is sufficient for AI processing. Adds unnecessary complexity for the current scope.

---

### Frontend — removed

Veen shipped a SvelteKit static frontend early on (see [ADR-004](adr/ADR-004-static-frontend.md)), but it was never deployed and nobody used it. It was removed in favor of publishing data only — see [ADR-007](adr/ADR-007-remove-frontend.md). Third parties consuming this data bring their own frontend; see [Consuming the API](consuming-the-api.md).

---

### Data Delivery — GitHub raw URLs / jsDelivr CDN

JSON files committed to the repository are immediately available at `https://raw.githubusercontent.com/user/veen-news/main/data/latest.json`. For production use, jsDelivr mirrors GitHub releases at `https://cdn.jsdelivr.net/gh/user/veen-news@main/data/latest.json` with global CDN caching and higher rate limits.

**Alt A — GitHub Pages (separate branch)**: Serving data via a `gh-pages` branch is a common pattern but adds complexity — the crawler workflow must manage two branches. The raw.githubusercontent.com URL is simpler and already available.

**Alt B — Cloudflare R2**: Object storage with zero egress cost. More robust for large files, but requires provisioning a bucket, setting up API credentials, and managing file uploads separately from the git commit flow. The JSON files are small (< 500 KB/day) — raw GitHub URLs are sufficient without the added ops.

---

### Source Config — YAML in repo

`data/sources.yaml` lives in the git repository. Every source change is a commit with a diff. Adding, disabling, or recategorizing a source is a one-line YAML edit. The crawler reads this file directly at runtime — no database sync needed.

See [ADR-005](adr/ADR-005-source-config.md) for the full decision record.

**Alt A — JSON config**: Functionally equivalent to YAML but less human-readable for a list-of-objects structure. YAML is the conventional format for config files in the Python/DevOps ecosystem and more ergonomic to edit by hand.

**Alt B — Database table**: Requires building and maintaining a CRUD API and UI for source management. Massively disproportionate to the need — this config changes at most a few times per month, for a single developer.

---

### Secrets — GitHub Actions Secrets

`OPENROUTER_API_KEY` is stored in GitHub Actions Secrets and injected as an environment variable at runtime. The model is stored as a plain Actions Variable (`VEEN_AI_MODEL`) since it is not sensitive. No additional tooling needed — the secret is never committed to the repo and GitHub's secret masking prevents accidental exposure in logs.

**Alt A — HashiCorp Vault**: Enterprise-grade secrets management with fine-grained access control, dynamic credentials, and audit logs. Massive operational overhead for a system with one secret and one operator.

**Alt B — .env file (local only)**: Works for local development but cannot be used in CI. GitHub Actions Secrets is the natural complement — `.env` locally, Secrets in CI, zero extra tooling.
