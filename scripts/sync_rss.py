#!/usr/bin/env python3
"""Sync episodes.json from the SoundOn RSS feed."""
import html
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

TITLE_PREFIX_RE = re.compile(r"^.*】Ep\.?\d+\s*-?\s*")


def clean_episode_title(raw_title):
    raw_title = (raw_title or "").strip()
    cleaned = TITLE_PREFIX_RE.sub("", raw_title, count=1).strip()
    return cleaned if cleaned else raw_title


def strip_html(text):
    text = text or ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


LEAD_MARKERS = ("周邊商品", "formerchildclub", "全新 EP")
FOOTER_MARKERS = ("patreon 支持我們", "收聽 每集會員限定內容", "本集內容：", "instagram:", "facebook:", "hosting provided by")


SEPARATOR_CHARS = set("-_－―~～＿")


def is_separator_line(line):
    if not line:
        return False
    if len(set(line)) <= 2 and len(line) >= 5:
        return True
    return all(ch in SEPARATOR_CHARS for ch in line)


FULLWIDTH_SEP_RE = re.compile(r"＿{5,}")


def _clean_lines(text):
    return [
        line
        for line in (l.strip() for l in text.split("\n"))
        if line and not line.startswith("http") and not is_separator_line(line)
    ]


def _lines_via_marker_scan(text):
    lines = [line.strip() for line in text.split("\n")]
    content_lines = []
    started = False
    for line in lines:
        if not line:
            continue
        lower = line.lower()
        if any(marker in lower for marker in FOOTER_MARKERS):
            break
        if line.startswith("http"):
            continue
        if is_separator_line(line):
            continue
        if any(marker in line for marker in LEAD_MARKERS) or line.startswith("拾壹每週聽"):
            if started:
                break
            continue
        started = True
        content_lines.append(line)
    return content_lines


def extract_summary(description, max_length=80):
    text = description or ""

    content_lines = []
    parts = FULLWIDTH_SEP_RE.split(text)
    if len(parts) >= 3:
        content_lines = _clean_lines(parts[1])
    if not content_lines:
        content_lines = _lines_via_marker_scan(text)

    summary = " ".join(content_lines).strip()
    if not summary:
        summary = next((line.strip() for line in text.split("\n") if line.strip()), "")
    if len(summary) > max_length:
        summary = summary[:max_length].rstrip() + "…"
    return summary


ITUNES_NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}


def parse_pub_date(raw_date):
    dt = parsedate_to_datetime(raw_date.strip())
    return dt.strftime("%Y-%m-%d")


def parse_feed(xml_text):
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    episodes = []
    for item in channel.findall("item"):
        try:
            guid_el = item.find("guid")
            title_el = item.find("title")
            pub_date_el = item.find("pubDate")
            desc_el = item.find("description")
            link_el = item.find("link")
            enclosure_el = item.find("enclosure")
            season_el = item.find("itunes:season", ITUNES_NS)
            episode_el = item.find("itunes:episode", ITUNES_NS)

            description = strip_html(desc_el.text if desc_el is not None else "")
            episodes.append(
                {
                    "id": guid_el.text.strip() if guid_el is not None and guid_el.text else None,
                    "season": int(season_el.text) if season_el is not None and season_el.text else None,
                    "episodeNumber": int(episode_el.text) if episode_el is not None and episode_el.text else None,
                    "title": clean_episode_title(title_el.text if title_el is not None else ""),
                    "pubDate": parse_pub_date(pub_date_el.text) if pub_date_el is not None and pub_date_el.text else None,
                    "description": description,
                    "summary": extract_summary(description),
                    "audioUrl": enclosure_el.get("url") if enclosure_el is not None else "",
                    "soundonUrl": link_el.text.strip() if link_el is not None and link_el.text else "",
                }
            )
        except Exception as exc:
            guid_el = item.find("guid")
            title_el = item.find("title")
            identifier = (
                (guid_el.text.strip() if guid_el is not None and guid_el.text else None)
                or (title_el.text.strip() if title_el is not None and title_el.text else None)
                or "<unknown item>"
            )
            print(f"warning: skipping malformed RSS item ({identifier}): {exc}", file=sys.stderr)
    return episodes


def merge_episodes(existing, fetched):
    existing_by_id = {ep["id"]: ep for ep in existing}
    merged = []
    for fetched_ep in fetched:
        prior = existing_by_id.get(fetched_ep["id"])
        merged_ep = dict(fetched_ep)
        merged_ep["appleUrl"] = prior["appleUrl"] if prior else ""
        merged_ep["spotifyUrl"] = prior["spotifyUrl"] if prior else ""
        merged.append(merged_ep)
    merged.sort(key=lambda ep: ep["pubDate"] or "", reverse=True)
    return merged


import json
import sys
import urllib.request
from pathlib import Path

RSS_URL = "https://feeds.soundon.fm/podcasts/6caafcca-f43a-4459-8fc0-cc065723f46a.xml"
DEFAULT_EPISODES_PATH = Path(__file__).resolve().parent.parent / "episodes.json"
PODCAST_META = {
    "title": "拾壹每週聽 Subyub Per Week Listen to",
    "coverImage": "https://files.soundon.fm/1654956277505-a3a2af86-2394-49b0-9803-af0cff173092.jpeg",
    "soundonRss": RSS_URL,
}


def fetch_rss(url):
    req = urllib.request.Request(url, headers={"User-Agent": "subyubperweek-sync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def load_existing(path):
    if not path.exists():
        return {"podcast": {}, "episodes": []}
    return json.loads(path.read_text(encoding="utf-8"))


def sync(rss_url=RSS_URL, episodes_path=DEFAULT_EPISODES_PATH, fetcher=fetch_rss):
    episodes_path = Path(episodes_path)
    xml_bytes = fetcher(rss_url)
    fetched = parse_feed(xml_bytes)
    data = load_existing(episodes_path)
    data["episodes"] = merge_episodes(data.get("episodes", []), fetched)
    data["podcast"] = PODCAST_META

    new_content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    old_content = episodes_path.read_text(encoding="utf-8") if episodes_path.exists() else None
    changed = new_content != old_content
    episodes_path.write_text(new_content, encoding="utf-8")
    return changed


if __name__ == "__main__":
    did_change = sync()
    print("changed" if did_change else "unchanged")
    sys.exit(0)
