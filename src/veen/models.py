from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel


def url_to_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:8]


class RawArticle(BaseModel):
    id: str
    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    category: str
    snippet: str = ""

    @classmethod
    def from_feed_entry(cls, entry: dict, source_name: str, category: str) -> RawArticle:
        url = entry.get("link", "")
        snippet = (entry.get("summary") or "")[:300]
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        published_at: Optional[str] = None
        if pub:
            try:
                dt = datetime(*pub[:6], tzinfo=timezone.utc)
                published_at = dt.isoformat()
            except Exception:
                pass
        return cls(
            id=url_to_id(url),
            title=(entry.get("title") or "").strip(),
            url=url,
            source=source_name,
            published_at=published_at,
            category=category,
            snippet=snippet,
        )


class ProcessedArticle(BaseModel):
    id: str
    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    category: str
    summary: str = ""
    score: float = 0.5
    cluster_id: Optional[str] = None


class Cluster(BaseModel):
    id: str
    topic: str
    summary: str
    article_ids: list[str]
    article_count: int
    representative_id: str


class DailyRecap(BaseModel):
    global_analysis: str   # Global tech landscape analysis (Vietnamese)
    vietnam_analysis: str  # Vietnam-specific analysis (Vietnamese)
    watch_list: str        # "Đáng theo dõi" personal insights (Vietnamese)
    full_summary: str      # Complete narrative paragraph (Vietnamese)


class ProcessedOutput(BaseModel):
    articles: list[ProcessedArticle]
    clusters: list[Cluster]
    daily_recap: Optional[DailyRecap] = None
