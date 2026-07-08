# ADR-007 — Remove the Frontend: Veen Is a Data Provider, Not a Website

**Status**: Accepted
**Date**: 2026-07-08

---

## Context

Veen shipped a SvelteKit static frontend (`frontend/`, see [ADR-004](ADR-004-static-frontend.md)) intended for deployment on Cloudflare Pages. That deployment never happened — the project owner does not open the frontend themselves, and the actual use case that emerged (GitHub issue #2) was third-party sites consuming Veen's JSON directly, not a Veen-hosted UI. `docs/architecture/consuming-the-api.md` was written specifically to support that use case.

Keeping an unused, undeployed frontend around still has a cost: it's maintenance surface with no audience. Concretely, `frontend/src/routes/weekly/+page.svelte` and `monthly/+page.svelte` had drifted out of sync with the actual JSON schema `veen.recaps` emits (wrong field names, wrong "latest" selection) for an unknown period, because nobody was looking at the pages to notice.

---

## Decision

Delete `frontend/` entirely. Veen is a pure data pipeline: GitHub Actions crawls, an AI pipeline processes, and the output is committed as JSON to `data/`. There is no UI and no API server in this repository. Any consumer — a third-party frontend, script, or service — fetches the JSON directly from `raw.githubusercontent.com` or jsDelivr, per `docs/architecture/consuming-the-api.md`.

---

## Consequences

### Positive

- **No more silent drift**: there's no unused frontend code to fall out of sync with the data schema.
- **Smaller surface area**: no `npm install`, no Node toolchain, no `svelte-check`, no frontend dependency upgrades to track.
- **Matches actual usage**: the project was already being consumed as a data source, not visited as a website.

### Negative

- **No reference implementation in-repo**: third parties building against the JSON no longer have a full worked example to copy from, only the fetch template in `consuming-the-api.md`. Mitigated by keeping that doc as the canonical integration guide.
- **Re-adding a frontend later starts from zero**: the deleted code is recoverable from git history (this ADR's commit) if a personal-use viewer is wanted again.

---

## Alternatives Considered

### Keep the frontend, unmaintained

**Pros**: No work required now; frontend stays available if ever needed.
**Cons**: Exactly the failure mode that motivated this ADR — unused code silently drifts from the data it depends on and misleads anyone who stumbles on it assuming it works.

**Rejected**: A repo should not carry code nobody runs or verifies.

### Deploy the frontend (Cloudflare Pages / Vercel) instead of removing it

**Pros**: Fulfills the original ADR-004 plan; gives the project an actual public face.
**Cons**: Requires ongoing attention (DNS, deploy config, monitoring) for a UI the project owner has confirmed they don't use themselves. Doesn't address the actual request, which was a data-consumption template for other sites.

**Rejected**: Explicitly out of scope per project owner — see the discussion that produced `consuming-the-api.md` instead of a deployment.
