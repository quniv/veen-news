# Consuming Veen's Data from Another Site

Veen has no API server — the data is static JSON committed to this repo. Any site
can fetch it directly over HTTPS via GitHub's raw CDN (or jsDelivr, which
proxies raw.githubusercontent.com with better caching). This guide is the
minimal template for wiring up a third-party frontend against it.

See [Data Model](data-model.md) for the full JSON schema of every file below.

---

## Base URL

```
https://raw.githubusercontent.com/quniv/veen-news/main
# or, for CDN caching:
https://cdn.jsdelivr.net/gh/quniv/veen-news@main
```

Both are plain static file hosts and send permissive CORS headers
(`Access-Control-Allow-Origin: *`), so `fetch()` from any origin works with no
proxy or backend needed.

## Endpoints

| File | Use |
|------|-----|
| `data/latest.json` | Today's digest — the default view |
| `data/daily/YYYY-MM-DD.json` | A specific day's digest |
| `data/weekly/YYYY-WW.json` | Weekly recap (ISO week, e.g. `2026-25`) |
| `data/monthly/YYYY-MM.json` | Monthly recap |
| `data/index.json` | List of every available daily/weekly/monthly file |
| `data/pagination.json` | Page-size/count metadata for `index.json`'s arrays |

## Minimal fetch template

```js
const BASE = 'https://cdn.jsdelivr.net/gh/quniv/veen-news@main';

async function fetchLatest() {
  const res = await fetch(`${BASE}/data/latest.json`);
  if (!res.ok) throw new Error(`Failed to fetch latest digest: ${res.status}`);
  return res.json(); // → Digest, see data-model.md
}

async function fetchHistoryPage(page = 0) {
  const [index, pagination] = await Promise.all([
    fetch(`${BASE}/data/index.json`).then((r) => r.json()),
    fetch(`${BASE}/data/pagination.json`).then((r) => r.json()),
  ]);
  const { page_size } = pagination;
  const start = page * page_size;
  return index.daily.slice(start, start + page_size);
}
```

Rendering an article is just iterating `digest.categories[<key>]` — each
category is an array of article objects (`title`, `url`, `source`, `summary`,
`score`, `published_at`, `cluster_id`). Group by `cluster_id` if you want to
show related coverage together (see [Data Model § Single Cluster
Schema](data-model.md#single-cluster-schema)).

## Freshness

`data/latest.json` and `data/daily/*.json` are rewritten once a day by the
GitHub Actions crawl (01:00 UTC). Use `cache: 'no-cache'` on the latest-digest
fetch if you need same-day updates to show up immediately; historical daily
files never change once written, so they're safe to cache indefinitely.

## Rate limits

`raw.githubusercontent.com` and jsDelivr are both CDN-backed and effectively
unlimited for read traffic at this project's scale. There is no auth, no API
key, and no request quota to manage.
