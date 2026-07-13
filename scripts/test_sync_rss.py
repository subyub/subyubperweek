import unittest
import os
import json
import tempfile
from pathlib import Path

from sync_rss import clean_episode_title, strip_html, parse_feed, parse_pub_date, merge_episodes, sync

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


class TestParsePubDate(unittest.TestCase):
    def test_parses_named_timezone(self):
        self.assertEqual(parse_pub_date("Sat, 20 Jun 2026 13:29:28 GMT"), "2026-06-20")

    def test_parses_numeric_offset_timezone(self):
        self.assertEqual(parse_pub_date("Sat, 20 Jun 2026 13:29:28 +0000"), "2026-06-20")


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

    def test_item_with_malformed_pub_date_is_skipped_not_fatal(self):
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
<title>Test Feed</title>
<item>
<title>Good Episode One</title>
<guid isPermaLink="false">good-1</guid>
<pubDate>Sat, 20 Jun 2026 13:29:28 GMT</pubDate>
<link>https://example.com/1</link>
<enclosure url="https://example.com/1.mp3" length="1" type="audio/mpeg"/>
<itunes:season>1</itunes:season>
<itunes:episode>1</itunes:episode>
</item>
<item>
<title>Malformed Date Episode</title>
<guid isPermaLink="false">bad-date</guid>
<pubDate>not a date</pubDate>
<link>https://example.com/bad</link>
<enclosure url="https://example.com/bad.mp3" length="1" type="audio/mpeg"/>
<itunes:season>1</itunes:season>
<itunes:episode>2</itunes:episode>
</item>
<item>
<title>Good Episode Two</title>
<guid isPermaLink="false">good-2</guid>
<pubDate>Sun, 09 Jul 2023 09:14:45 GMT</pubDate>
<link>https://example.com/2</link>
<enclosure url="https://example.com/2.mp3" length="1" type="audio/mpeg"/>
<itunes:season>1</itunes:season>
<itunes:episode>3</itunes:episode>
</item>
</channel>
</rss>"""
        episodes = parse_feed(xml_text)
        self.assertEqual(len(episodes), 2)
        self.assertEqual([ep["id"] for ep in episodes], ["good-1", "good-2"])


class TestMergeEpisodes(unittest.TestCase):
    def test_new_episode_gets_empty_manual_fields(self):
        fetched = [{"id": "ep1", "pubDate": "2026-07-01", "title": "New"}]
        merged = merge_episodes(existing=[], fetched=fetched)
        self.assertEqual(merged[0]["appleUrl"], "")
        self.assertEqual(merged[0]["spotifyUrl"], "")

    def test_existing_manual_fields_are_preserved(self):
        existing = [
            {
                "id": "ep1",
                "pubDate": "2026-07-01",
                "title": "Old title",
                "appleUrl": "https://podcasts.apple.com/ep1",
                "spotifyUrl": "https://open.spotify.com/ep1",
            }
        ]
        fetched = [{"id": "ep1", "pubDate": "2026-07-01", "title": "Updated title"}]
        merged = merge_episodes(existing=existing, fetched=fetched)
        self.assertEqual(merged[0]["title"], "Updated title")
        self.assertEqual(merged[0]["appleUrl"], "https://podcasts.apple.com/ep1")
        self.assertEqual(merged[0]["spotifyUrl"], "https://open.spotify.com/ep1")

    def test_sorted_newest_first(self):
        fetched = [
            {"id": "old", "pubDate": "2020-01-01", "title": "Old"},
            {"id": "new", "pubDate": "2026-07-01", "title": "New"},
        ]
        merged = merge_episodes(existing=[], fetched=fetched)
        self.assertEqual([ep["id"] for ep in merged], ["new", "old"])

    def test_removed_from_feed_episode_is_dropped(self):
        existing = [
            {"id": "gone", "pubDate": "2020-01-01", "title": "Gone", "appleUrl": "", "spotifyUrl": ""}
        ]
        merged = merge_episodes(existing=existing, fetched=[])
        self.assertEqual(merged, [])


class TestSync(unittest.TestCase):
    def _fake_fetcher(self, xml_bytes):
        return lambda url: xml_bytes

    def test_writes_episodes_json_from_fixture(self):
        with open(FIXTURE_PATH, "rb") as f:
            xml_bytes = f.read()
        with tempfile.TemporaryDirectory() as tmp:
            episodes_path = Path(tmp) / "episodes.json"
            changed = sync(
                rss_url="unused://fixture",
                episodes_path=episodes_path,
                fetcher=self._fake_fetcher(xml_bytes),
            )
            self.assertTrue(changed)
            data = json.loads(episodes_path.read_text(encoding="utf-8"))
            self.assertEqual(len(data["episodes"]), 3)
            self.assertEqual(data["episodes"][0]["id"], "480968d5-4b0a-4424-90ac-e72082944270")

    def test_second_run_with_same_data_reports_unchanged(self):
        with open(FIXTURE_PATH, "rb") as f:
            xml_bytes = f.read()
        with tempfile.TemporaryDirectory() as tmp:
            episodes_path = Path(tmp) / "episodes.json"
            sync(
                rss_url="unused://fixture",
                episodes_path=episodes_path,
                fetcher=self._fake_fetcher(xml_bytes),
            )
            changed_again = sync(
                rss_url="unused://fixture",
                episodes_path=episodes_path,
                fetcher=self._fake_fetcher(xml_bytes),
            )
            self.assertFalse(changed_again)

    def test_preserves_manual_links_across_runs(self):
        with open(FIXTURE_PATH, "rb") as f:
            xml_bytes = f.read()
        with tempfile.TemporaryDirectory() as tmp:
            episodes_path = Path(tmp) / "episodes.json"
            sync(
                rss_url="unused://fixture",
                episodes_path=episodes_path,
                fetcher=self._fake_fetcher(xml_bytes),
            )
            data = json.loads(episodes_path.read_text(encoding="utf-8"))
            data["episodes"][0]["appleUrl"] = "https://podcasts.apple.com/manually-added"
            episodes_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            sync(
                rss_url="unused://fixture",
                episodes_path=episodes_path,
                fetcher=self._fake_fetcher(xml_bytes),
            )
            data_after = json.loads(episodes_path.read_text(encoding="utf-8"))
            self.assertEqual(
                data_after["episodes"][0]["appleUrl"],
                "https://podcasts.apple.com/manually-added",
            )


if __name__ == "__main__":
    unittest.main()
