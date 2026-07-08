"""Write processed articles to data/ as daily JSON + update index."""
import json
import logging
from datetime import datetime, timezone

import yaml

from . import config
from .models import ProcessedOutput

log = logging.getLogger(__name__)

CATEGORIES = [
    "technology", "ai", "devops", "world",
    "vietnam", "innovations", "robotics", "open_source",
]

PAGE_SIZE = 30


def write_pagination(page_size: int = PAGE_SIZE) -> None:
    """Derive data/pagination.json from the current data/index.json.

    There's no server, so this only publishes counts/page-size metadata —
    consumers slice index.json's daily/weekly/monthly arrays client-side.
    """
    index_file = config.DATA_DIR / "index.json"
    try:
        index = json.loads(index_file.read_text()) if index_file.exists() else {}
    except Exception:
        index = {}

    sections = {}
    for key in ("daily", "weekly", "monthly"):
        total_items = len(index.get(key, []))
        total_pages = -(-total_items // page_size) if total_items else 0
        sections[key] = {"total_items": total_items, "total_pages": total_pages}

    pagination = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "page_size": page_size,
        "sections": sections,
    }
    (config.DATA_DIR / "pagination.json").write_text(json.dumps(pagination, indent=2))


def _count_raw() -> int:
    if config.TMP_RAW.exists():
        try:
            return len(json.loads(config.TMP_RAW.read_text()))
        except Exception:
            pass
    return 0


def _count_sources() -> int:
    try:
        with open(config.SOURCES_FILE) as f:
            data = yaml.safe_load(f)
        return sum(1 for s in data.get("sources", []) if s.get("active", True))
    except Exception:
        return 0


def _update_index(today: str, article_count: int) -> None:
    index_file = config.DATA_DIR / "index.json"
    try:
        index = json.loads(index_file.read_text()) if index_file.exists() else {}
    except Exception:
        index = {}

    for key in ("daily", "weekly", "monthly"):
        index.setdefault(key, [])

    entry = {"date": today, "path": f"data/daily/{today}.json", "article_count": article_count}
    index["daily"] = [e for e in index["daily"] if e.get("date") != today]
    index["daily"].insert(0, entry)
    index["daily"] = index["daily"][:365]

    index["updated_at"] = datetime.now(timezone.utc).isoformat()
    index["latest_date"] = today
    index_file.write_text(json.dumps(index, indent=2))


def export() -> None:
    if not config.TMP_PROCESSED.exists():
        print("✗ No processed data found. Run `python -m veen.ai_pipeline` first.")
        return

    output = ProcessedOutput.model_validate_json(config.TMP_PROCESSED.read_text())

    now = datetime.now(timezone.utc)
    today = now.date().isoformat()

    categories: dict[str, list] = {cat: [] for cat in CATEGORIES}
    for article in output.articles:
        cat = article.category if article.category in categories else "technology"
        categories[cat].append(article.model_dump())

    fetched = _count_raw()
    digest = {
        "generated_at": now.isoformat(),
        "date": today,
        "categories": categories,
        "clusters": [c.model_dump() for c in output.clusters],
        "daily_recap": output.daily_recap.model_dump() if output.daily_recap else None,
        "stats": {
            "fetched": fetched,
            "after_filter": len(output.articles),
            "published": len(output.articles),
            "clusters_formed": len(output.clusters),
            "sources_crawled": _count_sources(),
        },
    }

    daily_dir = config.DATA_DIR / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    daily_file = daily_dir / f"{today}.json"
    daily_file.write_text(json.dumps(digest, indent=2, default=str))
    log.info("Written %s", daily_file)

    latest = config.DATA_DIR / "latest.json"
    latest.write_text(json.dumps(digest, indent=2, default=str))

    _update_index(today, len(output.articles))
    write_pagination()
    print(f"✓ Exported {len(output.articles)} articles → {daily_file}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    export()


if __name__ == "__main__":
    main()
