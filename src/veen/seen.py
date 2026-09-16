"""Persistent ledger of URLs already handed to the AI pipeline.

Replaces the old "scan the last 7 daily files" dedup, which let any URL back in
on day 8 — the entire cause of cross-day duplicates (see ADR-007).
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timedelta, timezone

from . import config

log = logging.getLogger(__name__)

SCHEMA_VERSION = 1


def url_key(url: str) -> str:
    # 16 hex chars, not the 8 of models.url_to_id: a permanent ledger holds tens
    # of thousands of keys, where 32 bits is a real collision risk.
    return hashlib.sha256(url.encode()).hexdigest()[:16]


class SeenLedger:
    """url_key → first-seen date. Pruned by age; never refreshed on re-sighting.

    Not refreshing keeps the daily git diff down to just the new lines. A URL
    that ages out of the retention window is caught by the freshness filter
    instead, since by then it is far older than VEEN_MAX_AGE_HOURS.
    """

    def __init__(self, entries: dict[str, str] | None = None) -> None:
        self.entries: dict[str, str] = entries or {}
        self.added = 0

    @classmethod
    def load(cls) -> "SeenLedger":
        path = config.SEEN_FILE
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            # A corrupt ledger must not fail the crawl; worst case is one day of
            # duplicates, which the freshness window still bounds.
            log.warning("Unreadable seen ledger %s (%s) — starting empty", path, exc)
            return cls()
        return cls(dict(data.get("entries", {})))

    def __contains__(self, url: str) -> bool:
        return url_key(url) in self.entries

    def __len__(self) -> int:
        return len(self.entries)

    def add(self, url: str, today: date | None = None) -> None:
        key = url_key(url)
        if key in self.entries:
            return
        self.entries[key] = (today or datetime.now(timezone.utc).date()).isoformat()
        self.added += 1

    def prune(self, today: date | None = None) -> int:
        today = today or datetime.now(timezone.utc).date()
        cutoff = (today - timedelta(days=config.SEEN_RETENTION_DAYS)).isoformat()
        stale = [k for k, seen in self.entries.items() if seen < cutoff]
        for key in stale:
            del self.entries[key]
        return len(stale)

    def save(self) -> None:
        path = config.SEEN_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": SCHEMA_VERSION,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "retention_days": config.SEEN_RETENTION_DAYS,
            "count": len(self.entries),
            "entries": self.entries,
        }
        # sort_keys keeps the daily diff to added/removed lines only
        path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        log.info("Seen ledger: %d entries (+%d new)", len(self.entries), self.added)
