# Veen — Pipeline Flow

## System Overview

```mermaid
flowchart TD
    CRON["⏰ GitHub Actions\ncron 01:00 UTC daily"] --> CHECKOUT
    MANUAL["▶ workflow_dispatch\n(manual trigger)"] --> CHECKOUT

    CHECKOUT["① Checkout repo\nactions/checkout@v4"] --> UV
    UV["② Setup uv + install deps\nastral-sh/setup-uv@v4 + uv sync"] --> CRAWL

    subgraph CRAWL_STEP ["③ veen.crawl"]
        SOURCES["data/sources.yaml\n38 active sources"] --> FETCH
        FETCH["httpx fetch each feed\n(sequential, domain-rate-limited)"] --> DEDUP
        DEDUP["Deduplicate URLs\nvs last 7 days of daily/*.json"] --> RAW
        RAW["/tmp/veen-raw.json\n~600–700 raw articles"]
    end

    CRAWL --> AI_STEP

    subgraph AI_STEP ["④ veen.ai_pipeline"]
        direction TB
        FILTER["Filter pass\n(parallel batches)\nKeep thing-centric, reject person-centric"] --> SCORE
        SCORE["Score pass\n(parallel batches)\n0.0–1.0 relevance score"] --> THRESHOLD
        THRESHOLD["Apply threshold ≥ 0.4"] --> CLUSTER
        CLUSTER["Cluster pass\nGroup same-story articles"] --> SUMMARIZE
        SUMMARIZE["Summarize\nclusters + standalone\n(parallel, Vietnamese)"] --> RECAP
        RECAP["Daily Recap\nglobal_analysis · vietnam_analysis\nwatch_list · full_summary"]
    end

    AI_STEP --> PROCESSED
    PROCESSED["/tmp/veen-processed.json"] --> EXPORT_STEP

    subgraph EXPORT_STEP ["⑤ veen.export"]
        E1["data/daily/YYYY-MM-DD.json\narticles by category + recap"]
        E2["data/latest.json\ncopy of today's output"]
        E3["data/index.json\nmaster index updated"]
    end

    EXPORT_STEP --> COMMIT

    COMMIT{"Any changes?"}
    COMMIT -- "git diff empty" --> SKIP["Skip commit\n(no new articles)"]
    COMMIT -- "new data" --> PUSH["git push\ncommit: chore: daily crawl YYYY-MM-DD"]

    PUSH --> CF["☁ Cloudflare Pages\nauto-build on push\nfrontend/build/ → CDN"]

    style CRON fill:#2d2d2d,color:#fff
    style MANUAL fill:#2d2d2d,color:#fff
    style SKIP fill:#444,color:#aaa
```

---

## AI Pipeline Detail

```mermaid
flowchart LR
    RAW["~600 raw articles"] --> FB

    subgraph FILTER ["Filter — parallel batches of 25"]
        FB["Batch 1"] & FC["Batch 2"] & FD["Batch N"] --> FP["LLM: keep / reject\nthing-centric only"]
    end

    FP --> KEPT["~150–300 kept"]

    subgraph SCORE ["Score — parallel batches of 25"]
        SB["Batch 1"] & SC["Batch 2"] & SD["Batch N"] --> SP["LLM: score 0.0–1.0\nrelevance to DevOps/AI engineer"]
    end

    KEPT --> SB & SC & SD
    SP --> TH["Threshold ≥ 0.4\n~80–150 articles"]

    TH --> CL["Cluster — single call\ngroup same-story articles"]

    CL --> CLU["Clustered articles"] & STA["Standalone articles"]

    subgraph SUMMARIZE ["Summarize — parallel"]
        CLU --> CS["Cluster summaries\n(1 call)"]
        STA --> SS1["Standalone batch 1"] & SS2["Standalone batch 2"] & SS3["Standalone batch 3"]
    end

    CS & SS1 & SS2 & SS3 --> BUILD["Build ProcessedArticle list\n(Vietnamese summaries)"]
    BUILD --> DR["Daily Recap\n(1 call)"]
    DR --> OUT["ProcessedOutput\narticles + clusters + daily_recap"]
```

---

## Step Reference

| # | Step | Input | Output | Notes |
|---|------|-------|--------|-------|
| ① | Checkout | — | repo on disk | `GITHUB_TOKEN` for push-back |
| ② | Setup + install | `uv.lock` | `.venv/` | cached between runs |
| ③ | `veen.crawl` | `data/sources.yaml` | `/tmp/veen-raw.json` | 38 active sources, ~600–700 articles; 6 s delay between reddit.com requests |
| ④ | `veen.ai_pipeline` | `/tmp/veen-raw.json` | `/tmp/veen-processed.json` | model = `VEEN_AI_MODEL` env var |
| ⑤ | `veen.export` | `/tmp/veen-processed.json` | `data/daily/`, `data/latest.json`, `data/index.json` | |
| ⑥ | Commit & push | `data/` diff | git commit | skipped if no new data |
| ⑦ | Cloudflare Pages | git push event | static site deployed | automatic, no extra config |

---

## Weekly & Monthly Recaps

A separate workflow runs after the daily crawl to generate aggregate recaps.

```mermaid
flowchart LR
    MON["Monday 02:00 UTC"] --> WK["veen.recaps → generate_weekly()\nTop articles from last 7 daily files"]
    FIRST["1st of month 02:00 UTC"] --> MO["veen.recaps → generate_monthly()\nTop articles from month's daily files"]
    WK --> WF["data/weekly/YYYY-WW.json"]
    MO --> MF["data/monthly/YYYY-MM.json"]
    WF & MF --> IDX["data/index.json updated"]
    IDX --> COMMIT2["git push"]
```

**Workflow file**: `.github/workflows/recaps.yml`

---

## Data Flow: Frontend

```mermaid
flowchart LR
    PUSH["git push to main"] --> CF_BUILD["Cloudflare Pages\nnpm run build"]
    CF_BUILD --> STATIC["frontend/build/\nstatic HTML + JS"]
    STATIC --> CDN["Global CDN edge"]

    USER["Browser"] --> CDN
    CDN --> PAGE["SvelteKit page"]
    PAGE --> API["fetchLatest()\nGET data/latest.json"]
    API --> RENDER["Render:\nTopicTabs → ArticleCard list → DailyRecap"]
```

`data/latest.json` is served directly from the repo as a static asset. No API server. No database.

---

## GitHub Secrets & Variables

| Name | Kind | Where set | Purpose |
|------|------|-----------|---------|
| `OPENROUTER_API_KEY` | Secret | Repo → Settings → Secrets | OpenRouter API key |
| `VEEN_AI_MODEL` | Variable | Repo → Settings → Variables | e.g. `deepseek/deepseek-v4-flash` |

**Variables** (not secrets) are visible in workflow logs — safe for non-sensitive config like provider names.

---

## Source Status

38 active sources across 8 categories. Sources disabled with reason:

| Source | Reason |
|--------|--------|
| Anthropic News | No public RSS feed |
| Meta AI Blog | No public RSS feed |
| AWS Blog | Request timeout |
| Netflix Tech Blog | Medium RSS timeout |
| GitLab Blog (old URL) | 404 — fixed to `about.gitlab.com/atom.xml` |
| VietnamNet | 404 — RSS URL changed |
| ICTnews | Redirects to HTML, no RSS |
| Vietnam News | Returns 0 articles |
| Reddit r/programming, r/ML, r/devops, etc. | 429 — Reddit allows only 1 RSS request per crawl run from server IPs; r/technology kept as the one working slot |

---

## Local Run

```bash
cp .env.example .env          # fill OPENROUTER_API_KEY
uv sync

uv run python -m veen.crawl        # → /tmp/veen-raw.json
uv run python -m veen.ai_pipeline  # → /tmp/veen-processed.json
uv run python -m veen.export       # → data/daily/, data/latest.json

# or all at once:
uv run python -m veen.pipeline
```
