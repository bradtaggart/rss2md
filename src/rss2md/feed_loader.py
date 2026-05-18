from datetime import datetime, timezone
from pathlib import Path

import feedparser
import httpx

from rss2md.models import Feed, FeedEntry


class FeedLoadError(Exception):
    pass


def _fetch_remote_text(url: str) -> str:
    try:
        response = httpx.get(url, follow_redirects=True, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise FeedLoadError(f"Unable to fetch remote feed: {exc}") from exc

    return response.text


def _read_source_text(source: str) -> str:
    if source.startswith(("http://", "https://")):
        return _fetch_remote_text(source)

    try:
        return Path(source).read_text(encoding="utf-8")
    except OSError as exc:
        raise FeedLoadError(f"Unable to read local feed: {source}") from exc


def load_feed(source: str) -> tuple[Feed, list[FeedEntry]]:
    raw = feedparser.parse(_read_source_text(source))
    if raw.bozo and not raw.entries:
        raise FeedLoadError(f"Unable to parse feed: {raw.bozo_exception}")

    feed = Feed(
        title=raw.feed.get("title"),
        link=raw.feed.get("link"),
        description=raw.feed.get("description"),
    )
    entries = [
        FeedEntry(
            title=item.get("title"),
            link=item.get("link"),
            author=item.get("author"),
            published_at=(
                datetime(*item.published_parsed[:6], tzinfo=timezone.utc)
                if item.get("published_parsed")
                else None
            ),
            guid=item.get("id") or item.get("guid"),
            tags=[tag["term"] for tag in item.get("tags", []) if tag.get("term")],
            book_description=item.get("book_description"),
            summary=item.get("summary"),
            content_html=(item.get("content") or [{}])[0].get("value"),
            source_feed_title=feed.title,
        )
        for item in raw.entries
    ]
    return feed, entries
