# ADR-004 — Frontend: SvelteKit Static Build on Cloudflare Pages

**Status**: Superseded by [ADR-007](ADR-007-remove-frontend.md)
**Date**: 2026-06-18

---

## Context

Veen needs a frontend to display daily/weekly/monthly news digests with topic filtering. The app is read-only — it displays curated articles and opens originals in new tabs. There are no writes, no user accounts, and no authentication. The frontend must: load fast, cost nothing to host, and require minimal maintenance.

Data is served as JSON files from the repository (`raw.githubusercontent.com`). No backend API server exists in the new architecture. The frontend must fetch JSON directly from GitHub.

---

## Decision

Build the frontend with **SvelteKit** using `@sveltejs/adapter-static`, producing a fully static directory of HTML/JS/CSS. Deploy to **Cloudflare Pages** connected to the GitHub repository — push to `main` triggers an automatic build and deploy in ~30 seconds.

---

## Consequences

### Positive

- **Zero hosting cost**: Cloudflare Pages free tier has no bandwidth cap and no request limit for static assets. Hosting cost is $0.
- **Fast and lean**: Svelte's compiler emits vanilla JavaScript with no virtual DOM runtime. Bundle sizes are consistently smaller than equivalent React applications — important for a page that loads on mobile on a slow connection.
- **Simple deployment**: `pnpm build` outputs to `frontend/build/`. Cloudflare Pages auto-deploys on push. No Docker images, no K8s manifests, no server configuration.
- **Zero attack surface**: a static site has no server-side code. There is nothing to exploit beyond the browser itself.
- **No CORS complexity**: JSON files on `raw.githubusercontent.com` are served with permissive CORS headers. The frontend fetches them directly — no proxy needed.
- **Preview deployments**: Cloudflare Pages automatically creates a preview URL for every pull request or branch push. Useful for testing UI changes before merging to `main`.

### Negative

- **Client-side data fetching**: articles are loaded after the page renders, not at build time. There is a brief loading state on first visit. Acceptable for a personal news reader.
- **No server-side filtering**: topic filtering is done in JavaScript on the client after loading the daily JSON. With < 200 KB files this is instantaneous — no perceptible performance impact.
- **jsDelivr CDN cache**: if using jsDelivr URLs for data delivery, aggressively cached files may serve stale data for hours. Use `raw.githubusercontent.com` for `latest.json` to ensure freshness, or bust the cache with a timestamp query parameter.

### Risks

- **Cloudflare Pages free tier changes**: if Cloudflare changes its free tier limits, migrating to Vercel or GitHub Pages requires only swapping the adapter (`@sveltejs/adapter-vercel` or `@sveltejs/adapter-static` with different output dir config) — no application code changes.

---

## Alternatives Considered

### Next.js (static export or SSR on Vercel)

**Pros**: Largest frontend ecosystem, excellent TypeScript support, first-class Vercel integration, React Server Components for server-side data fetching without CORS concerns.
**Cons**: React's virtual DOM and runtime are larger than Svelte's compiled output. For a simple read-only dashboard, the React ecosystem's complexity (hooks, context, memoization, RSC vs. client components) adds cognitive overhead without functional benefit. Vercel free tier caps bandwidth at 100 GB/month — sufficient for personal use, but Cloudflare Pages has no cap.

**Rejected**: Svelte produces smaller, faster output for equivalent UI complexity. The Next.js/Vercel combination doesn't justify the switch for a personal project.

### SvelteKit with Node SSR adapter

**Pros**: Server-side rendering eliminates loading states. No CORS issue — the Node server fetches JSON on the server side.
**Cons**: Requires running a Node.js server somewhere. The entire point of this architecture is eliminating servers. A Node.js SSR server would need to be hosted on Vercel, Render, Fly.io, or the home cluster — all of which add either cost or home-infra dependency.

**Rejected**: The static adapter + client-side fetch achieves the same result (fast news display) without any server. The brief loading state is acceptable for personal use.

### Plain HTML + vanilla JavaScript

**Pros**: Absolute minimum dependencies. No build step. Deployable as-is to any CDN. No framework to maintain.
**Cons**: Implementing topic filter tabs, dynamic recap views, responsive article cards, and async JSON fetching with error handling in vanilla JS is tedious. Code becomes unmaintainable quickly as features are added. No component model means duplicated markup for article cards, recap layouts, etc.

**Rejected**: SvelteKit with static adapter adds a minimal build step but provides component structure, reactivity, and a maintainable codebase. The bundle overhead compared to vanilla JS is negligible for a project of this scope.
