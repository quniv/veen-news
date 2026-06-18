# ADR-005 — Source Configuration: YAML File in Repository

**Status**: Accepted
**Date**: 2026-06-18

---

## Context

Veen crawls a list of trusted news sources. This list needs to be: editable (add, remove, disable sources), version-controlled (diffs visible in git history), and accessible to the crawler at runtime. The system is for a single developer — no other users manage sources. No runtime source management is required (adding a source while the crawler runs is not a use case).

---

## Decision

Define all news sources in **`data/sources.yaml`** checked into this Git repository. The crawler reads this file directly at runtime (it's available in the GitHub Actions checkout). Adding, disabling, or recategorizing a source means editing the YAML, committing, and pushing — the next crawl run picks it up.

```yaml
sources:
  - name: TechCrunch
    url: https://techcrunch.com/feed/
    feed_type: rss
    category: technology
    active: true

  - name: Hugging Face Blog
    url: https://huggingface.co/blog/feed.xml
    feed_type: atom
    category: ai
    active: true

  - name: Old Source (disabled)
    url: https://example.com/feed
    feed_type: rss
    category: technology
    active: false   # kept for history, not crawled
```

---

## Consequences

### Positive

- **Version-controlled**: every source change is a git commit with a readable diff. Easy to audit ("when did I add this source?", "why was that disabled?"). Git history is the full audit log.
- **No UI to build**: editing the config is editing a file. A text editor is the "admin UI." This eliminates 2–3 days of CRUD API + form development.
- **PR as the review mechanism**: if sources are ever reviewed before adding, a pull request is the natural workflow. No custom admin roles or approval flows needed.
- **Trivial crawler access**: in GitHub Actions, the repo is checked out — `data/sources.yaml` is available at the file path, no network call needed.
- **Offline-editable**: sources can be configured without GitHub being accessible. Edit locally, push when ready.
- **Diff-friendly**: YAML is line-oriented and human-readable. `git diff` shows exactly which source was added or changed, unlike a database diff.

### Negative

- **Not real-time**: a newly committed source takes effect on the next crawl run (up to 24 hours). This is acceptable — sources are changed rarely.
- **No validation UI**: a typo in a feed URL fails silently until the crawler logs an error. Mitigation: add a `veen validate-sources` CLI command that checks all URLs in `sources.yaml` before committing.

### Risks

- **YAML syntax errors**: a malformed `sources.yaml` would cause the entire crawl to fail. Mitigation: add a YAML validation step to the GitHub Actions workflow before the crawl step.

---

## Alternatives Considered

### Database table + admin UI (CRUD API + web form)

**Pros**: Real-time changes without redeploying or waiting for the next crawl. Natural extension if Veen ever became multi-user.
**Cons**: Requires building a CRUD API (5+ endpoints: list, create, update, delete, toggle-active), an admin frontend (form, validation, error states), and authentication (the admin UI must not be publicly accessible). This is conservatively 2–3x the development effort of the entire core crawler pipeline — for a feature that serves one developer who changes sources at most a few times per month.

**Rejected**: Completely disproportionate to the need. YAML and git are sufficient and simpler.

### JSON file in repository

**Pros**: Functionally identical to YAML. JSON is natively parsed by Python without a library import.
**Cons**: JSON is less ergonomic for hand-editing a list of objects — no comments, trailing-comma errors, more punctuation. YAML is the conventional format for configuration files in the Python/DevOps ecosystem and is immediately familiar.

**Rejected**: YAML is marginally more readable for this use case. `pyyaml` is a single dependency line.

### Environment variable (comma-separated URLs)

**Pros**: Simplest possible configuration. Set one env var, restart the job.
**Cons**: No per-source metadata — no name, category, feed_type, or active flag. Unreadable for more than 3–4 entries. Impossible to represent the full source schema in a flat string. Diff is meaningless ("before: 800-character string, after: 850-character string").

**Rejected**: Does not scale beyond trivial source lists and loses all structured metadata needed by the crawler and frontend.
