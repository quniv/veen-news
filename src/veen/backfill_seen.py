"""One-off: seed the seen ledger from every URL already published under data/daily/.

Without this the first run after the dedup change would treat 89 days of
published articles as new. Only published URLs are recoverable — everything the
AI filter rejected is lost to history, and the freshness window covers it.

    uv run python -m veen.backfill_seen
"""
import json
import logging
from datetime import date

from . import config
from .seen import SeenLedger

log = logging.getLogger(__name__)


def backfill() -> SeenLedger:
    ledger = SeenLedger.load()
    daily_dir = config.DATA_DIR / "daily"
    if not daily_dir.exists():
        print("No data/daily/ — nothing to backfill.")
        return ledger

    files = 0
    for path in sorted(daily_dir.glob("*.json")):
        try:
            digest = json.loads(path.read_text())
        except Exception as exc:
            log.warning("Skipping unreadable %s: %s", path.name, exc)
            continue
        day = digest.get("date") or path.stem
        try:
            seen_on = date.fromisoformat(day)
        except ValueError:
            seen_on = None
        for articles in digest.get("categories", {}).values():
            for article in articles:
                url = article.get("url")
                if url:
                    ledger.add(url, seen_on)
        files += 1

    pruned = ledger.prune()
    ledger.save()
    print(f"✓ Seeded {ledger.added} URLs from {files} daily files ({pruned} pruned as too old)")
    return ledger


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    backfill()


if __name__ == "__main__":
    main()
