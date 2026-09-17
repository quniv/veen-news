import unittest

from veen.pipeline_openrouter import _as_bullets


class AsBulletsTests(unittest.TestCase):
    def test_already_formatted_passes_through(self) -> None:
        self.assertEqual(_as_bullets("- một\n- hai"), "- một\n- hai")

    def test_normalizes_other_bullet_chars(self) -> None:
        self.assertEqual(_as_bullets("• một\n* hai\n– ba"), "- một\n- hai\n- ba")

    def test_normalizes_numbered_lists(self) -> None:
        self.assertEqual(_as_bullets("1. một\n2) hai"), "- một\n- hai")

    def test_drops_blank_lines(self) -> None:
        self.assertEqual(_as_bullets("- một\n\n\n- hai\n  \n"), "- một\n- hai")

    def test_paragraph_without_markers_becomes_one_bullet(self) -> None:
        # Deliberate: sentence-splitting Vietnamese prose is not reliable.
        self.assertEqual(_as_bullets("GitLab vá lỗ hổng."), "- GitLab vá lỗ hổng.")

    def test_accepts_a_list_from_the_model(self) -> None:
        self.assertEqual(_as_bullets(["một", "hai"]), "- một\n- hai")

    def test_empty_inputs_are_empty(self) -> None:
        for value in ("", None, [], "   ", "\n\n"):
            self.assertEqual(_as_bullets(value), "")

    def test_negative_number_after_the_marker_survives(self) -> None:
        self.assertEqual(_as_bullets("- -5% hiệu năng"), "- -5% hiệu năng")

    def test_hyphenated_word_survives(self) -> None:
        self.assertEqual(_as_bullets("- end-to-end mã hoá"), "- end-to-end mã hoá")


class DailyRecapBulletsTests(unittest.TestCase):
    def test_every_recap_field_is_normalized_to_bullets(self) -> None:
        import json
        from unittest import mock

        from veen import pipeline_openrouter as po
        from veen.models import ProcessedArticle

        reply = json.dumps({
            "full_summary": "• Một\n• Hai",
            "global_analysis": "1. Toàn cầu\n2. Xu hướng",
            "vietnam_analysis": "Đoạn văn không có dấu đầu dòng.",
            "watch_list": ["Kỹ năng A", "Kỹ năng B"],
        })
        article = ProcessedArticle(id="a", title="t", url="u", source="s", category="ai", summary="- x")

        with mock.patch.object(po, "_chat", return_value=reply):
            recap = po._generate_daily_recap(mock.Mock(), [article])

        self.assertEqual(recap.full_summary, "- Một\n- Hai")
        self.assertEqual(recap.global_analysis, "- Toàn cầu\n- Xu hướng")
        self.assertEqual(recap.vietnam_analysis, "- Đoạn văn không có dấu đầu dòng.")
        self.assertEqual(recap.watch_list, "- Kỹ năng A\n- Kỹ năng B")


if __name__ == "__main__":
    unittest.main()
