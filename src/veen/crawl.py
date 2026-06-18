"""Fetch RSS feeds and write raw articles to /tmp/veen-raw.json."""
import json
import logging
import time
from urllib.parse import urlparse

import feedparser
import httpx
import yaml

from . import config
from .models import RawArticle

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Veen-News-Bot/1.0 (+https://github.com/qitpydev/veen-news)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}

# Minimum seconds to wait between consecutive requests to the same domain
DOMAIN_MIN_DELAY: dict[str, float] = {
    "www.reddit.com": 6.0,
}


def load_sources() -> list[dict]:
    with open(config.SOURCES_FILE) as f:
        data = yaml.safe_load(f)
    return [s for s in data.get("sources", []) if s.get("active", True)]


def seen_urls() -> set[str]:
    """Collect URLs already committed in the last 7 daily files to avoid duplicates."""
    urls: set[str] = set()
    daily_dir = config.DATA_DIR / "daily"
    if not daily_dir.exists():
        return urls
    for f in sorted(daily_dir.glob("*.json"))[-7:]:
        try:
            digest = json.loads(f.read_text())
            for articles in digest.get("categories", {}).values():
                for a in articles:
                    urls.add(a.get("url", ""))
        except Exception:
            pass
    return urls


def fetch_feed(source: dict, client: httpx.Client) -> list[RawArticle]:
    url = source["url"]
    name = source["name"]
    category = source["category"]
    try:
        resp = client.get(url, timeout=20, follow_redirects=True)
        resp.raise_for_status()
        # Pass bytes so feedparser handles charset/BOM detection itself
        feed = feedparser.parse(resp.content)
    except Exception as exc:
        log.warning("Failed to fetch %s (%s): %s", name, url, exc)
        return []

    articles: list[RawArticle] = []
    for entry in feed.entries[:30]:
        try:
            a = RawArticle.from_feed_entry(entry, name, category)
            if a.url and a.title:
                articles.append(a)
        except Exception as exc:
            log.debug("Skipping entry from %s: %s", name, exc)
    log.info("  %s → %d articles", name, len(articles))
    return articles


def crawl() -> list[RawArticle]:
    sources = load_sources()
    known = seen_urls()
    log.info("Crawling %d active sources, %d known URLs to skip", len(sources), len(known))

    all_articles: list[RawArticle] = []
    seen_in_run: set[str] = set()
    last_domain_time: dict[str, float] = {}

    with httpx.Client(headers=HEADERS) as client:
        for source in sources:
            domain = urlparse(source["url"]).netloc
            min_delay = DOMAIN_MIN_DELAY.get(domain, 0.0)
            if min_delay > 0 and domain in last_domain_time:
                elapsed = time.monotonic() - last_domain_time[domain]
                if elapsed < min_delay:
                    time.sleep(min_delay - elapsed)

            articles = fetch_feed(source, client)
            last_domain_time[domain] = time.monotonic()

            for a in articles:
                if a.url in known or a.url in seen_in_run:
                    continue
                seen_in_run.add(a.url)
                all_articles.append(a)

    log.info("Crawled %d new articles total", len(all_articles))
    return all_articles


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    articles = crawl()
    config.TMP_RAW.write_text(json.dumps([a.model_dump() for a in articles], indent=2, default=str))
    print(f"✓ Fetched {len(articles)} articles → {config.TMP_RAW}")


if __name__ == "__main__":
    main()
