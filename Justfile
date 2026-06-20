set dotenv-load

# Show available recipes
default:
    @just --list

# ── Setup ────────────────────────────────────────────────────────────────────

# Copy .env.example → .env (skip if already exists)
setup:
    @[ -f .env ] && echo ".env already exists — skipping." || (cp .env.example .env && echo ".env created from .env.example")

# Install / sync Python dependencies
install:
    uv sync

# ── Python pipeline ───────────────────────────────────────────────────────────

# Crawl RSS feeds and cache raw articles
crawl:
    uv run python -m veen.crawl

# Run the AI filter + clustering pipeline
ai:
    uv run python -m veen.ai_pipeline

# Export processed articles to JSON files under data/
export:
    uv run python -m veen.export

# Run the weekly/monthly recap generator
recaps:
    uv run python -m veen.recaps

# Run the full pipeline: crawl → ai → export
run: crawl ai export

# ── Frontend ──────────────────────────────────────────────────────────────────

# Start the SvelteKit dev server
dev:
    cd frontend && npm run dev

# Build the frontend for production
build:
    cd frontend && npm run build

# Preview the production build locally
preview:
    cd frontend && npm run preview

# Type-check the frontend with svelte-check
check:
    cd frontend && npm run check

# Install frontend npm dependencies
frontend-install:
    cd frontend && npm install

# ── Data ─────────────────────────────────────────────────────────────────────

# Show recent daily digests
data:
    @ls -lt data/daily/ | head -10

# Show latest digest summary (article count per topic)
latest:
    #!/usr/bin/env python3
    import json, pathlib
    p = pathlib.Path("data/latest.json")
    if not p.exists():
        print("No latest.json found — run: just run")
    else:
        d = json.loads(p.read_text())
        topics = {}
        for a in d.get("articles", []):
            t = a.get("topic", "unknown")
            topics[t] = topics.get(t, 0) + 1
        print(f"Date: {d.get('date', '?')}")
        print(f"Total articles: {len(d.get('articles', []))}")
        for t, c in sorted(topics.items()):
            print(f"  {t}: {c}")
