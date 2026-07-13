import unittest
import os

from sync_rss import clean_episode_title, strip_html, parse_feed

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_feed.xml")


class TestCleanEpisodeTitle(unittest.TestCase):
    def test_strips_season_prefix(self):
        raw = "【拾壹每週聽（廣東話）S3】Ep95 - 福岡美食推介（公開版）"
        self.assertEqual(clean_episode_title(raw), "福岡美食推介（公開版）")

    def test_strips_prefix_without_space_before_dash(self):
        raw = "【拾壹每週聽（廣東話）S3】Ep29- 社交媒體恐懼:又有新App啦 "
        self.assertEqual(clean_episode_title(raw), "社交媒體恐懼:又有新App啦")

    def test_strips_prefix_without_season(self):
        raw = "【拾壹每週聽】Ep10 - 2020小確幸"
        self.assertEqual(clean_episode_title(raw), "2020小確幸")

    def test_strips_prefix_with_dot_after_ep(self):
        raw = "【拾壹每週聽】Ep.1 - 年近三十的戀愛思考"
        self.assertEqual(clean_episode_title(raw), "年近三十的戀愛思考")

    def test_returns_raw_title_when_pattern_not_found(self):
        raw = "特別企劃：年終回顧"
        self.assertEqual(clean_episode_title(raw), "特別企劃：年終回顧")

    def test_handles_none(self):
        self.assertEqual(clean_episode_title(None), "")


class TestStripHtml(unittest.TestCase):
    def test_removes_tags(self):
        html_text = '<p>Hello <a href="https://x.com">link</a></p>'
        self.assertEqual(strip_html(html_text), "Hello link")

    def test_unescapes_entities(self):
        self.assertEqual(strip_html("找到最強咖啡 &amp; 豆腐店"), "找到最強咖啡 & 豆腐店")

    def test_collapses_blank_lines(self):
        html_text = "line1\n\n\n\nline2"
        self.assertEqual(strip_html(html_text), "line1\n\nline2")

    def test_handles_empty_string(self):
        self.assertEqual(strip_html(""), "")


class TestParseFeed(unittest.TestCase):
    def setUp(self):
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            self.xml_text = f.read()
        self.episodes = parse_feed(self.xml_text)

    def test_parses_all_items(self):
        self.assertEqual(len(self.episodes), 3)

    def test_first_episode_fields(self):
        ep = self.episodes[0]
        self.assertEqual(ep["id"], "480968d5-4b0a-4424-90ac-e72082944270")
        self.assertEqual(ep["season"], 3)
        self.assertEqual(ep["episodeNumber"], 95)
        self.assertEqual(ep["title"], "福岡美食推介（公開版）")
        self.assertEqual(ep["pubDate"], "2026-06-20")
        self.assertIn("福岡最強咖啡", ep["description"])
        self.assertTrue(ep["audioUrl"].startswith("https://rss.soundon.fm/"))
        self.assertTrue(ep["soundonUrl"].startswith("https://player.soundon.fm/"))

    def test_episode_without_season_marker_still_has_season_from_itunes_tag(self):
        ep = self.episodes[2]
        self.assertEqual(ep["id"], "8b0381bc-69be-4119-863e-4ccf4307b7ff")
        self.assertEqual(ep["season"], 1)
        self.assertEqual(ep["episodeNumber"], 10)
        self.assertEqual(ep["title"], "2020小確幸")

    def test_feed_order_matches_source_order(self):
        ids = [ep["id"] for ep in self.episodes]
        self.assertEqual(
            ids,
            [
                "480968d5-4b0a-4424-90ac-e72082944270",
                "bf9cefc9-8b58-4377-a465-7dd96ad2f8af",
                "8b0381bc-69be-4119-863e-4ccf4307b7ff",
            ],
        )


if __name__ == "__main__":
    unittest.main()
