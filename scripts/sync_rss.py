#!/usr/bin/env python3
"""Sync episodes.json from the SoundOn RSS feed."""
import html
import re

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
