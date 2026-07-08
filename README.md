# Veen

A personal, zero-cost news aggregator. Daily crawls trusted RSS sources, filters trash and clickbait with AI, and delivers a clean curated digest — no ads, no noise.

## How it works

1. **GitHub Actions** runs daily, crawling RSS/API feeds across 8 topic categories
2. **AI pipeline** (OpenRouter) filters, clusters, and summarizes articles
3. **Output** is committed as JSON files to this repository under `data/`
4. **SvelteKit frontend** on Cloudflare Pages fetches the JSON and renders the digest

## Topics

Technology · AI · DevOps/DevSecOps · World Trends · Vietnam · Innovations · Robotics · Open Source

## Stack

| Layer | Tool |
|-------|------|
| Compute | GitHub Actions (free tier) |
| AI | OpenRouter (DeepSeek / any model via env var) |
| Data store | JSON files in this repo |
| Frontend | SvelteKit → Cloudflare Pages |
| Source config | `data/sources.yaml` |

## Project structure

```
veen-news/
├── data/                   ← generated daily (committed by GitHub Actions)
│   ├── sources.yaml        ← RSS source configuration
│   ├── latest.json         ← most recent daily digest
│   ├── index.json          ← index of all available digests
│   ├── pagination.json     ← page-size/count metadata for index.json
│   ├── daily/              ← YYYY-MM-DD.json
│   ├── weekly/             ← YYYY-WW.json
│   └── monthly/            ← YYYY-MM.json
├── src/                    ← Python crawler + AI pipeline
├── frontend/               ← SvelteKit app
├── .github/workflows/      ← daily-crawl.yml, recaps.yml
└── docs/
    └── architecture/       ← design docs, ADRs, roadmap
```

## Documentation

- [Architecture overview](docs/architecture/README.md)
- [Tech stack decisions](docs/architecture/tech-stack.md)
- [Data model](docs/architecture/data-model.md)
- [Consuming the data from another site](docs/architecture/consuming-the-api.md)
- [GitHub Actions workflow](docs/architecture/github-actions-workflow.md)
- [Roadmap](docs/architecture/roadmap.md)
- [ADRs](docs/architecture/adr/)

## Using this data in your own frontend

Veen has no API server — everything is static JSON served straight from this
repo. Any site can fetch it over CORS-enabled raw GitHub / jsDelivr URLs with
no auth and no backend. See [Consuming the API](docs/architecture/consuming-the-api.md)
for the base URL, endpoint list, and a copy-pasteable fetch template.
