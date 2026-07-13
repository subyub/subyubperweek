#!/usr/bin/env python3
"""Sync episodes.json from the SoundOn RSS feed."""
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime

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


ITUNES_NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}


def parse_pub_date(raw_date):
    dt = datetime.strptime(raw_date.strip(), "%a, %d %b %Y %H:%M:%S %Z")
    return dt.strftime("%Y-%m-%d")


def parse_feed(xml_text):
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    episodes = []
    for item in channel.findall("item"):
        guid_el = item.find("guid")
        title_el = item.find("title")
        pub_date_el = item.find("pubDate")
        desc_el = item.find("description")
        link_el = item.find("link")
        enclosure_el = item.find("enclosure")
        season_el = item.find("itunes:season", ITUNES_NS)
        episode_el = item.find("itunes:episode", ITUNES_NS)

        episodes.append(
            {
                "id": guid_el.text.strip() if guid_el is not None and guid_el.text else None,
                "season": int(season_el.text) if season_el is not None and season_el.text else None,
                "episodeNumber": int(episode_el.text) if episode_el is not None and episode_el.text else None,
                "title": clean_episode_title(title_el.text if title_el is not None else ""),
                "pubDate": parse_pub_date(pub_date_el.text) if pub_date_el is not None and pub_date_el.text else None,
                "description": strip_html(desc_el.text if desc_el is not None else ""),
                "audioUrl": enclosure_el.get("url") if enclosure_el is not None else "",
                "soundonUrl": link_el.text.strip() if link_el is not None and link_el.text else "",
            }
        )
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
