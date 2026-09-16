"""Reject articles that are already old when crawled.

A calendar-day filter would not work here: the crawl runs at 01:00 UTC, so most
genuinely-new items carry yesterday's date. This is a rolling window instead.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from . import config
from .models import RawArticle

log = logging.getLogger(__name__)


def max_age(source: dict) -> timedelta:
    """Per-source `max_age_days` override, else the global VEEN_MAX_AGE_HOURS."""
    days = source.get("max_age_days")
    if days is not None:
        try:
            return timedelta(days=float(days))
        except (TypeError, ValueError):
            log.warning("Bad max_age_days on %s: %r — using default", source.get("name"), days)
    return timedelta(hours=config.MAX_AGE_HOURS)


def is_fresh(article: RawArticle, window: timedelta, now: datetime | None = None) -> bool:
    """Undated or unparseable articles pass — the seen ledger still dedups them."""
    if not article.published_at:
        return True
    try:
        published = datetime.fromisoformat(article.published_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    # Feeds sometimes post-date entries; treat the future as fresh, not stale.
    return published >= now - window
