import unittest

from veen.models import RawArticle
from veen.pipeline_openrouter import _select_cluster_representatives


def article(article_id: str, *, published_at: str | None = None) -> RawArticle:
    return RawArticle(
        id=article_id,
        title=article_id,
        url=f"https://example.com/{article_id}",
        source="Test",
        category="technology",
        published_at=published_at,
    )


class SelectClusterRepresentativesTests(unittest.TestCase):
    def test_keeps_standalone_articles_and_highest_scored_cluster_member(self) -> None:
        articles = [article("standalone"), article("low"), article("high")]

        selected = _select_cluster_representatives(
            articles,
            {"low": "story", "high": "story"},
            {"standalone": 0.7, "low": 0.7, "high": 0.9},
        )

        self.assertEqual([item.id for item in selected], ["standalone", "high"])

    def test_breaks_equal_scores_by_newer_publish_time_then_id(self) -> None:
        articles = [
            article("older", published_at="2026-07-10T08:00:00+00:00"),
            article("newer", published_at="2026-07-10T09:00:00+00:00"),
            article("same-time-a", published_at="2026-07-10T10:00:00+00:00"),
            article("same-time-b", published_at="2026-07-10T10:00:00+00:00"),
        ]

        selected = _select_cluster_representatives(
            articles,
            {
                "older": "first-story",
                "newer": "first-story",
                "same-time-a": "second-story",
                "same-time-b": "second-story",
            },
            {item.id: 0.8 for item in articles},
        )

        self.assertEqual([item.id for item in selected], ["newer", "same-time-b"])


if __name__ == "__main__":
    unittest.main()
