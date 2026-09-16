import json
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from veen import config
from veen.freshness import is_fresh, max_age
from veen.models import RawArticle
from veen.seen import SeenLedger, url_key

NOW = datetime(2026, 9, 16, 1, 0, tzinfo=timezone.utc)


def article(url: str, published_at: str | None = None) -> RawArticle:
    return RawArticle(
        id=url[-8:],
        title="t",
        url=url,
        source="Test",
        category="technology",
        published_at=published_at,
    )


def ago(**kwargs) -> str:
    return (NOW - timedelta(**kwargs)).isoformat()


class FreshnessTests(unittest.TestCase):
    window = timedelta(hours=72)

    def test_yesterday_evening_is_fresh(self) -> None:
        # The 01:00 UTC crawl must not reject news published hours earlier.
        self.assertTrue(is_fresh(article("u", ago(hours=7)), self.window, NOW))

    def test_within_window_is_fresh(self) -> None:
        self.assertTrue(is_fresh(article("u", ago(hours=71)), self.window, NOW))

    def test_beyond_window_is_stale(self) -> None:
        self.assertFalse(is_fresh(article("u", ago(hours=73)), self.window, NOW))
        self.assertFalse(is_fresh(article("u", ago(days=400)), self.window, NOW))

    def test_future_dates_pass(self) -> None:
        future = (NOW + timedelta(hours=5)).isoformat()
        self.assertTrue(is_fresh(article("u", future), self.window, NOW))

    def test_missing_or_unparseable_date_passes(self) -> None:
        self.assertTrue(is_fresh(article("u", None), self.window, NOW))
        self.assertTrue(is_fresh(article("u", "not-a-date"), self.window, NOW))

    def test_naive_timestamp_treated_as_utc(self) -> None:
        naive = (NOW - timedelta(hours=1)).replace(tzinfo=None).isoformat()
        self.assertTrue(is_fresh(article("u", naive), self.window, NOW))

    def test_zulu_suffix_parses(self) -> None:
        zulu = ago(hours=1).replace("+00:00", "Z")
        self.assertTrue(is_fresh(article("u", zulu), self.window, NOW))


class MaxAgeTests(unittest.TestCase):
    def test_defaults_to_global_window(self) -> None:
        self.assertEqual(max_age({"name": "x"}), timedelta(hours=config.MAX_AGE_HOURS))

    def test_per_source_override_wins(self) -> None:
        self.assertEqual(max_age({"name": "x", "max_age_days": 14}), timedelta(days=14))

    def test_bad_override_falls_back(self) -> None:
        self.assertEqual(
            max_age({"name": "x", "max_age_days": "soon"}), timedelta(hours=config.MAX_AGE_HOURS)
        )


class SeenLedgerTests(unittest.TestCase):
    def test_url_key_is_stable_and_16_chars(self) -> None:
        key = url_key("https://example.com/a")
        self.assertEqual(len(key), 16)
        self.assertEqual(key, url_key("https://example.com/a"))
        self.assertNotEqual(key, url_key("https://example.com/b"))

    def test_membership_and_add_is_idempotent(self) -> None:
        ledger = SeenLedger()
        self.assertNotIn("https://example.com/a", ledger)
        ledger.add("https://example.com/a", date(2026, 9, 16))
        ledger.add("https://example.com/a", date(2026, 9, 17))
        self.assertIn("https://example.com/a", ledger)
        self.assertEqual(ledger.added, 1)
        self.assertEqual(ledger.entries[url_key("https://example.com/a")], "2026-09-16")

    def test_prune_drops_only_entries_past_retention(self) -> None:
        today = date(2026, 9, 16)
        ledger = SeenLedger()
        ledger.add("https://example.com/old", today - timedelta(days=config.SEEN_RETENTION_DAYS + 1))
        ledger.add("https://example.com/edge", today - timedelta(days=config.SEEN_RETENTION_DAYS))
        ledger.add("https://example.com/new", today)
        self.assertEqual(ledger.prune(today), 1)
        self.assertNotIn("https://example.com/old", ledger)
        self.assertIn("https://example.com/edge", ledger)
        self.assertIn("https://example.com/new", ledger)

    def test_roundtrip_through_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state" / "seen.json"
            with mock.patch.object(config, "SEEN_FILE", path):
                ledger = SeenLedger()
                ledger.add("https://example.com/a", date(2026, 9, 16))
                ledger.save()
                reloaded = SeenLedger.load()
            self.assertIn("https://example.com/a", reloaded)
            self.assertEqual(json.loads(path.read_text())["count"], 1)

    def test_corrupt_ledger_starts_empty_instead_of_raising(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "seen.json"
            path.write_text("{not json")
            with mock.patch.object(config, "SEEN_FILE", path):
                self.assertEqual(len(SeenLedger.load()), 0)

    def test_missing_file_starts_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(config, "SEEN_FILE", Path(tmp) / "nope.json"):
                self.assertEqual(len(SeenLedger.load()), 0)


class CrawlIntegrationTests(unittest.TestCase):
    """The regression this whole change exists for: a URL must not come back."""

    def test_url_seen_on_an_earlier_day_is_not_recrawled(self) -> None:
        from veen import crawl as crawl_mod

        fresh = ago(hours=2)
        feed = [article("https://example.com/a", fresh), article("https://example.com/b", fresh)]
        ledger = SeenLedger()
        ledger.add("https://example.com/a", date(2026, 6, 18))  # 90 days back, still in window

        with (
            mock.patch.object(crawl_mod, "load_sources", return_value=[{"name": "S", "url": "https://s/f", "category": "technology"}]),
            mock.patch.object(crawl_mod, "fetch_feed", return_value=feed),
            mock.patch.object(crawl_mod, "is_fresh", return_value=True),
        ):
            result = crawl_mod.crawl(ledger)

        self.assertEqual([a.url for a in result], ["https://example.com/b"])
        self.assertIn("https://example.com/b", ledger)

    def test_stale_articles_are_not_added_to_the_ledger(self) -> None:
        from veen import crawl as crawl_mod

        feed = [article("https://example.com/old", ago(days=400))]
        ledger = SeenLedger()

        with (
            mock.patch.object(crawl_mod, "load_sources", return_value=[{"name": "S", "url": "https://s/f", "category": "technology"}]),
            mock.patch.object(crawl_mod, "fetch_feed", return_value=feed),
        ):
            result = crawl_mod.crawl(ledger)

        self.assertEqual(result, [])
        # Widening the window later must be able to pick this article up.
        self.assertNotIn("https://example.com/old", ledger)


if __name__ == "__main__":
    unittest.main()
