import unittest

from sync_rss import clean_episode_title, strip_html


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


if __name__ == "__main__":
    unittest.main()
