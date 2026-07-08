"""Generate weekly and monthly recaps from existing daily data."""
import json
import logging
from datetime import datetime, timedelta, timezone

from . import config
from .export import write_pagination

log = logging.getLogger(__name__)

CATEGORIES = [
    "technology", "ai", "devops", "world",
    "vietnam", "innovations", "robotics", "open_source",
]


def _load_daily(date_str: str) -> dict | None:
    f = config.DATA_DIR / "daily" / f"{date_str}.json"
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            pass
    return None


def _update_index_entry(key: str, entry_key: str, entry: dict) -> None:
    index_file = config.DATA_DIR / "index.json"
    try:
        index = json.loads(index_file.read_text()) if index_file.exists() else {}
    except Exception:
        index = {}
    index.setdefault(key, [])
    index[key] = [e for e in index[key] if e.get(entry_key) != entry[entry_key]]
    index[key].insert(0, entry)
    index["updated_at"] = datetime.now(timezone.utc).isoformat()
    index_file.write_text(json.dumps(index, indent=2))
    write_pagination()


def generate_weekly() -> None:
    today = datetime.now(timezone.utc).date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(7)]
    digests = [d for day in days if (d := _load_daily(day))]

    if not digests:
        log.warning("No daily data found for the past 7 days — skipping weekly recap")
        return

    week = today.strftime("%Y-%W")
    period_start = min(d["date"] for d in digests)
    period_end = max(d["date"] for d in digests)

    all_articles = []
    all_clusters = []
    for digest in digests:
        for articles in digest.get("categories", {}).values():
            all_articles.extend(articles)
        all_clusters.extend(digest.get("clusters", []))

    categories: dict[str, dict] = {}
    for cat in CATEGORIES:
        cat_articles = sorted(
            [a for a in all_articles if a.get("category") == cat],
            key=lambda a: a.get("score", 0),
            reverse=True,
        )
        categories[cat] = {
            "article_count": len(cat_articles),
            "top_articles": cat_articles[:5],
        }

    recap = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "week": week,
        "period_start": period_start,
        "period_end": period_end,
        "top_clusters": sorted(
            all_clusters, key=lambda c: c.get("article_count", 0), reverse=True
        )[:10],
        "categories": categories,
        "stats": {
            "total_articles": len(all_articles),
            "total_clusters": len(all_clusters),
            "days_covered": len(digests),
        },
    }

    weekly_dir = config.DATA_DIR / "weekly"
    weekly_dir.mkdir(parents=True, exist_ok=True)
    out = weekly_dir / f"{week}.json"
    out.write_text(json.dumps(recap, indent=2, default=str))
    log.info("Written weekly recap: %s", out)

    _update_index_entry(
        "weekly", "week",
        {"week": week, "path": f"data/weekly/{week}.json", "article_count": len(all_articles)},
    )
    print(f"✓ Weekly recap {week} written ({len(all_articles)} articles, {len(digests)} days)")


def generate_monthly() -> None:
    today = datetime.now(timezone.utc).date()
    month_str = today.strftime("%Y-%m")
    period_start = today.replace(day=1).isoformat()

    daily_dir = config.DATA_DIR / "daily"
    digests = []
    if daily_dir.exists():
        for f in sorted(daily_dir.glob(f"{month_str}-*.json")):
            try:
                digests.append(json.loads(f.read_text()))
            except Exception:
                pass

    if not digests:
        log.warning("No daily data for %s — skipping monthly recap", month_str)
        return

    period_end = max(d["date"] for d in digests)
    all_articles = []
    all_clusters = []
    for digest in digests:
        for articles in digest.get("categories", {}).values():
            all_articles.extend(articles)
        all_clusters.extend(digest.get("clusters", []))

    categories = {
        cat: {"article_count": len([a for a in all_articles if a.get("category") == cat])}
        for cat in CATEGORIES
    }

    recap = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "month": month_str,
        "period_start": period_start,
        "period_end": period_end,
        "headline": "",
        "top_clusters": sorted(
            all_clusters, key=lambda c: c.get("article_count", 0), reverse=True
        )[:10],
        "categories": categories,
        "stats": {
            "total_articles": len(all_articles),
            "total_clusters": len(all_clusters),
            "days_covered": len(digests),
        },
    }

    monthly_dir = config.DATA_DIR / "monthly"
    monthly_dir.mkdir(parents=True, exist_ok=True)
    out = monthly_dir / f"{month_str}.json"
    out.write_text(json.dumps(recap, indent=2, default=str))
    log.info("Written monthly recap: %s", out)

    _update_index_entry(
        "monthly", "month",
        {"month": month_str, "path": f"data/monthly/{month_str}.json", "article_count": len(all_articles)},
    )
    print(f"✓ Monthly recap {month_str} written ({len(all_articles)} articles, {len(digests)} days)")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    today = datetime.now(timezone.utc).date()
    if today.weekday() == 0:
        generate_weekly()
    if today.day == 1:
        generate_monthly()
    if today.weekday() != 0 and today.day != 1:
        # Manual run — generate both
        generate_weekly()
        generate_monthly()


if __name__ == "__main__":
    main()
