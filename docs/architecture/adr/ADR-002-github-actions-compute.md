# ADR-002 — Compute: GitHub Actions

**Status**: Accepted
**Date**: 2026-06-18

---

## Context

Veen needs to run a scheduled Python job once per day: fetch RSS feeds, process articles through an AI pipeline, and commit JSON output to the repository. The job takes ~5–10 minutes. There are no scaling requirements, no concurrent runs, and no real-time triggers. The system is personal-use only.

The previous architecture used a Kubernetes CronJob on a home cluster. This required the home cluster to be running reliably at the scheduled time, maintaining Docker images in a registry, and managing K8s manifests. A home server reboot, ISP outage, or misconfigured CronJob manifest would silently miss a day's crawl.

---

## Decision

Use **GitHub Actions** with a `schedule:` cron trigger (`0 1 * * *` — 01:00 UTC daily) to run the crawler pipeline. The workflow checks out the repo, installs dependencies with `uv`, runs the Python pipeline, and commits the JSON output back to the repo. A `workflow_dispatch:` trigger allows manual runs for testing.

---

## Consequences

### Positive

- **Truly zero cost**: GitHub Actions provides 2000 free minutes/month for private repos (unlimited for public). A daily 10-minute job uses ~300 minutes/month — well within the free tier.
- **No home infrastructure dependency**: the job runs on GitHub's hosted runners. The home server can be off, rebooted, or under maintenance without affecting the daily crawl.
- **Native secrets management**: `OPENROUTER_API_KEY` is stored in GitHub Actions Secrets. No Vault, no `.env` files in CI, no secrets in the repo.
- **Visibility**: every workflow run is logged in the GitHub Actions UI. Failed runs are visible at a glance and trigger email notifications to the repo owner.
- **`workflow_dispatch`**: one-click manual trigger from the GitHub UI for testing without waiting for the daily cron.
- **uv caching**: `astral-sh/setup-uv` caches the virtual environment between runs — subsequent runs skip reinstalling packages, saving 30–60 seconds per run.
- **Write-back is trivial**: the workflow has `permissions: contents: write` and uses the built-in `GITHUB_TOKEN` to push the JSON commit. No deploy keys or PATs needed.

### Negative

- **GitHub cron delay**: the `schedule:` trigger can be delayed up to 15 minutes during high-load periods on GitHub's infrastructure. For a daily digest this is irrelevant, but it means the job won't run at exactly 01:00 UTC every night.
- **No on-prem data residency**: article data transits through GitHub's infrastructure. For a personal news aggregator reading public RSS feeds, this is not a concern.
- **GitHub platform dependency**: if GitHub Actions is unavailable, the daily crawl is missed. Historical data remains available — the frontend serves the previous day's `latest.json`. GitHub's reliability (>99.9% uptime) is acceptable for personal use.

### Risks

- **Workflow file corruption**: a broken `.github/workflows/daily-crawl.yml` silently disables the cron. Mitigation: any push to `main` that modifies the workflow file triggers the `workflow_dispatch` path — verify the workflow is valid before committing.
- **Repository permission issues**: the `contents: write` permission is set at the workflow level. If the repo is forked or the permission is accidentally removed, the commit step fails. Mitigation: the `git diff --staged --quiet` check means a failed commit does not corrupt existing data.

---

## Alternatives Considered

### Home K8s CronJob (previous architecture)

**Pros**: Full control, no external platform dependency, runs inside the home network where the data originates.
**Cons**: The home cluster must be running reliably at the scheduled time. A reboot, ISP outage, or Kubernetes issue means a missed crawl. Docker images must be built, pushed to a registry (GHCR or local), and kept up-to-date. K8s manifests must be maintained. The operational overhead is significant for a job that runs once a day.

**Rejected**: GitHub Actions is more reliable for a scheduled job than a home server. The elimination of Docker image management alone saves meaningful time.

### Render cron jobs

**Pros**: Managed, reliable, simple setup. Render's cron jobs run on a hosted environment without home infrastructure.
**Cons**: Render's cron service starts at $7/month. For a zero-cost project this is a non-starter. The free tier does not include cron jobs.

**Rejected**: Adding monthly cost contradicts the zero-cost architecture goal. GitHub Actions provides identical functionality for free.

### Fly.io scheduled machines / Railway cron

**Pros**: Container-based, more flexible than GitHub Actions, no 2000-minute cap.
**Cons**: Both require paid plans for reliable scheduled execution. Free tiers are insufficient for a daily 10-minute Python job with external API calls. Same cost objection as Render.

**Rejected**: Same reasoning as Render.
