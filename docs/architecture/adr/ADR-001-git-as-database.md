# ADR-001 — Data Storage: JSON Files in Git

**Status**: Accepted
**Date**: 2026-06-18

---

## Context

Veen needs persistent storage for processed articles, story clusters, and recap digests. The data is written once per day by a GitHub Actions job and read on-demand by a static frontend. Volume is low: ~50–200 articles per day, ~200 KB of JSON per crawl. There are no concurrent writes. No query complexity beyond "fetch today's articles, optionally filtered by category."

The previous architecture used PostgreSQL on a home Kubernetes cluster. This required maintaining a running database server, managing PVC-backed storage, running Alembic migrations, and operating a FastAPI layer to expose data to the frontend. For a personal project with one user and one daily write, this overhead is disproportionate.

---

## Decision

Store all article data as **JSON files committed directly to this Git repository** under the `data/` directory. The GitHub Actions crawler writes JSON files, commits them, and pushes. The SvelteKit frontend fetches JSON directly from `raw.githubusercontent.com` or jsDelivr CDN.

---

## Consequences

### Positive

- **Zero infrastructure cost**: no database server, no PVC, no connection pool, no backup job.
- **Versioned history for free**: every day's crawl is a git commit. Rollback, diff, and audit trail come with no extra effort.
- **CDN delivery without configuration**: `raw.githubusercontent.com` serves JSON files with correct MIME types and CORS headers. jsDelivr mirrors the repo and provides global CDN caching with no setup.
- **No migrations**: changing the JSON schema is a code change in the exporter. Old files remain valid for their schema version — the frontend handles both.
- **Readable and debuggable**: JSON files can be opened in any editor. Debugging a bad crawl means reading the file, not running SQL queries against a remote database.
- **Offline-capable frontend**: JSON files can be cached by service workers, enabling the frontend to load even without network access.

### Negative

- **No query flexibility**: filtering articles by category requires loading the full daily file and filtering in JavaScript. There is no server-side WHERE clause. For small files (< 200 KB) this is imperceptible.
- **No real-time updates**: the data is updated once daily. This is a feature, not a bug — the project is a daily digest.
- **Repo size grows over time**: ~200 KB/day × 365 days/year ≈ 72 MB/year. GitHub's soft limit is 1 GB. At this rate the repo stays manageable for 10+ years without pruning.

### Risks

- **GitHub raw URL availability**: `raw.githubusercontent.com` has had occasional brief outages. Mitigation: jsDelivr CDN mirrors GitHub repos and provides redundancy. The frontend can fall back to jsDelivr URLs if raw.githubusercontent.com fails.
- **Accidental large files**: if the crawler emits unexpectedly large JSON (e.g., a bug includes full article text instead of summaries), the commit could be large. Mitigation: add a file size check in the export step (warn if > 500 KB, fail if > 2 MB).

---

## Alternatives Considered

### PostgreSQL (previous architecture)

**Pros**: Full SQL, complex aggregation queries, JSONB for flexible fields, Alembic migrations, mature tooling.
**Cons**: Requires a running server. Either a home K8s deployment (home-infra dependency — if the cluster is down, no data is written) or a paid managed database ($15–25/month for the cheapest tier). Neither fits the zero-cost, zero-ops goal. Connection management, backup jobs, and migration tracking add ongoing maintenance.

**Rejected**: The query capabilities of PostgreSQL are entirely unused at this scale. All "queries" are trivially handled by JSON parsing in the frontend. The operational overhead is unjustified.

### SQLite file in the repository

**Pros**: File-based like JSON, zero server cost, full SQL available.
**Cons**: Binary format — git diffs are meaningless, and merge conflicts are unresolvable (though this is a single-writer system). The file cannot be served directly as a CDN asset; the frontend would need a server or build-time extraction step to read it. `aiosqlite` async support is a workaround, not first-class.

**Rejected**: SQLite in git loses the key benefit of git-as-database (human-readable diffs, CDN-servable files) while adding SQL complexity that isn't needed.
