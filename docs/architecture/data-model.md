# Veen — Data Model

No database. All data is stored as JSON files in the `data/` directory of this repository. The frontend reads these files directly. No migration tooling, no connection management.

---

## Directory Layout

```
data/
├── sources.yaml              ← source config (RSS feeds + categories)
├── index.json                ← index of all available daily/weekly/monthly files
├── latest.json               ← copy of the most recent daily output
├── daily/
│   └── YYYY-MM-DD.json       ← daily digest per date
├── weekly/
│   └── YYYY-WW.json          ← weekly recap (ISO week number)
└── monthly/
    └── YYYY-MM.json          ← monthly recap
```

---

## `data/sources.yaml`

Source of truth for which RSS feeds the crawler fetches. Edited manually, committed to git.

**Schema**:
```yaml
sources:
  - name: string           # display name
    url: string            # RSS/Atom feed URL
    feed_type: rss|atom    # feedparser format hint
    category: string       # maps to a top-level category key in daily JSON
    active: boolean        # false = skip without removing from config
```

**Example**:
```yaml
sources:
  - name: TechCrunch
    url: https://techcrunch.com/feed/
    feed_type: rss
    category: technology
    active: true

  - name: Hacker News
    url: https://hnrss.org/frontpage
    feed_type: rss
    category: technology
    active: true

  - name: Hugging Face Blog
    url: https://huggingface.co/blog/feed.xml
    feed_type: atom
    category: ai
    active: true

  - name: Kubernetes Blog
    url: https://kubernetes.io/feed.xml
    feed_type: atom
    category: devops
    active: true
```

**Valid categories**: `technology`, `ai`, `devops`, `world`, `vietnam`, `innovations`, `robotics`, `open_source`

---

## Single Article Schema

Used inside daily, weekly, and monthly JSON files.

```json
{
  "id": "a3f2c1b4",
  "title": "OpenAI releases GPT-5 with extended context window",
  "url": "https://openai.com/blog/gpt-5",
  "source": "OpenAI Blog",
  "published_at": "2026-06-18T08:30:00Z",
  "category": "ai",
  "summary": "OpenAI has launched GPT-5, featuring a 1M token context window and improved reasoning. The model is available via API immediately. Pricing is similar to GPT-4o.",
  "score": 0.92,
  "cluster_id": "cluster-a1b2c3"
}
```

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Short SHA-256 of the URL (first 8 hex chars) — stable identifier |
| `title` | string | Original article title, unmodified |
| `url` | string | Link to the original article — opens in new tab |
| `source` | string | Human-readable source name (from `sources.yaml`) |
| `published_at` | ISO 8601 string | Source-reported publish time (UTC) |
| `category` | string | One of the valid category values |
| `summary` | string | AI-generated 2–3 sentence summary |
| `score` | float | Relevance score 0.0–1.0 from AI pipeline |
| `cluster_id` | string or null | Links article to a cluster; null for standalone articles |

---

## Single Cluster Schema

```json
{
  "id": "cluster-a1b2c3",
  "topic": "GPT-5 launch and benchmark comparisons",
  "summary": "OpenAI released GPT-5 with a 1M token context window. Multiple outlets benchmarked it against Claude 4 and Gemini Ultra, with GPT-5 leading in coding tasks but trailing in long-document summarization.",
  "article_ids": ["a3f2c1b4", "d9e7f6a2", "b5c4d3e1"],
  "article_count": 3
}
```

---

## `data/daily/YYYY-MM-DD.json`

The primary output of the daily crawl job.

```json
{
  "generated_at": "2026-06-18T01:07:43Z",
  "date": "2026-06-18",
  "categories": {
    "technology": [
      {
        "id": "a3f2c1b4",
        "title": "...",
        "url": "...",
        "source": "TechCrunch",
        "published_at": "2026-06-18T08:30:00Z",
        "category": "technology",
        "summary": "...",
        "score": 0.87,
        "cluster_id": "cluster-x1y2z3"
      }
    ],
    "ai": [],
    "devops": [],
    "world": [],
    "vietnam": [],
    "innovations": [],
    "robotics": [],
    "open_source": []
  },
  "clusters": [
    {
      "id": "cluster-x1y2z3",
      "topic": "...",
      "summary": "...",
      "article_ids": ["a3f2c1b4", "b5d6e7f8"],
      "article_count": 2
    }
  ],
  "stats": {
    "fetched": 120,
    "after_filter": 45,
    "published": 32,
    "clusters_formed": 8,
    "sources_crawled": 18
  }
}
```

| Field | Notes |
|-------|-------|
| `generated_at` | UTC timestamp when the export step ran |
| `date` | Calendar date this digest covers (YYYY-MM-DD) |
| `categories` | Object keyed by category — each value is an array of article objects |
| `clusters` | Array of cluster objects referenced by articles via `cluster_id` |
| `stats` | Pipeline metrics for debugging and monitoring |

---

## `data/latest.json`

An exact copy of the most recent daily file. Written by the export step after `data/daily/YYYY-MM-DD.json`. The frontend uses this as the default data source to avoid needing to know today's date.

Schema: identical to `data/daily/YYYY-MM-DD.json`.

---

## `data/index.json`

Master index of all available data files. Updated by the export step on every run.

```json
{
  "updated_at": "2026-06-18T01:08:00Z",
  "latest_date": "2026-06-18",
  "daily": [
    { "date": "2026-06-18", "path": "data/daily/2026-06-18.json", "article_count": 32 },
    { "date": "2026-06-17", "path": "data/daily/2026-06-17.json", "article_count": 28 }
  ],
  "weekly": [
    { "week": "2026-25", "path": "data/weekly/2026-25.json", "article_count": 180 }
  ],
  "monthly": [
    { "month": "2026-06", "path": "data/monthly/2026-06.json", "article_count": 720 }
  ]
}
```

The frontend uses `index.json` to populate a date picker or history browser without needing a server-side list endpoint.

---

## `data/weekly/YYYY-WW.json`

Weekly recap generated every Monday. Aggregates the past 7 days of daily files.

```json
{
  "generated_at": "2026-06-22T02:05:00Z",
  "week": "2026-25",
  "period_start": "2026-06-16",
  "period_end": "2026-06-22",
  "top_clusters": [
    {
      "id": "cluster-a1b2c3",
      "topic": "GPT-5 launch",
      "summary": "...",
      "article_count": 12,
      "top_score": 0.95
    }
  ],
  "categories": {
    "technology": { "article_count": 85, "top_articles": [] },
    "ai": { "article_count": 42, "top_articles": [] },
    "devops": { "article_count": 28, "top_articles": [] }
  },
  "stats": {
    "total_articles": 198,
    "total_clusters": 34,
    "days_covered": 7
  }
}
```

`top_articles` inside each category is an array of up to 5 article objects (highest-scoring) — enough for the frontend to render a quick recap card without loading all daily files.

---

## `data/monthly/YYYY-MM.json`

Monthly recap generated on the 1st of each month. Aggregates all weekly recaps (or daily files if weeklies aren't available yet).

```json
{
  "generated_at": "2026-07-01T02:05:00Z",
  "month": "2026-06",
  "period_start": "2026-06-01",
  "period_end": "2026-06-30",
  "headline": "June 2026: GPT-5 launch dominated AI news; Kubernetes 2.0 released",
  "top_clusters": [
    {
      "id": "cluster-a1b2c3",
      "topic": "GPT-5 launch",
      "summary": "...",
      "article_count": 38,
      "top_score": 0.97
    }
  ],
  "categories": {
    "technology": { "article_count": 340 },
    "ai": { "article_count": 180 },
    "devops": { "article_count": 112 }
  },
  "stats": {
    "total_articles": 840,
    "total_clusters": 120,
    "days_covered": 30,
    "sources_active": 22
  }
}
```

The `headline` field is AI-generated — a single sentence summarizing the most notable themes of the month.

---

## Data Size Estimates

| File | Estimated size |
|------|---------------|
| `data/daily/YYYY-MM-DD.json` | 80–200 KB |
| `data/weekly/YYYY-WW.json` | 50–150 KB |
| `data/monthly/YYYY-MM.json` | 30–80 KB |
| `data/index.json` | < 10 KB |
| `data/latest.json` | same as daily |

After one year: ~365 daily files × 150 KB avg = ~55 MB. Well within GitHub's repo size limits (1 GB soft limit, 5 GB hard limit). The repository will remain performant for years without any pruning.
