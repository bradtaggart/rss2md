from datetime import datetime, timezone
from pathlib import Path

import pytest

from rss2md.models import Feed, FeedEntry


def test_load_feed_parses_local_fixture():
    from rss2md.feed_loader import load_feed

    fixture = Path("tests/fixtures/sample_feed.xml")

    feed, entries = load_feed(str(fixture))

    assert feed.title == "Sample Feed"
    assert len(entries) == 2
    assert entries[0].title == "First Entry"
    assert entries[0].book_description == "First book description"
    assert entries[0].source_feed_title == "Sample Feed"
    assert entries[1].book_description is None


def test_feed_entry_model_holds_normalized_fields():
    published_at = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)

    entry = FeedEntry(
        title="Example",
        link="https://example.com/post",
        author="Brad",
        published_at=published_at,
        guid="abc123",
        tags=["rss", "python"],
        book_description="Book description",
        summary="Summary",
        content_html="<p>Body</p>",
        source_feed_title="Example Feed",
    )
    feed = Feed(title="Example Feed", link="https://example.com", description="Desc")

    assert feed.title == "Example Feed"
    assert feed.link == "https://example.com"
    assert feed.description == "Desc"
    assert entry.title == "Example"
    assert entry.link == "https://example.com/post"
    assert entry.author == "Brad"
    assert entry.published_at == published_at
    assert entry.guid == "abc123"
    assert entry.tags == ["rss", "python"]
    assert entry.book_description == "Book description"
    assert entry.summary == "Summary"
    assert entry.content_html == "<p>Body</p>"
    assert entry.source_feed_title == "Example Feed"


def test_feed_entry_defaults_optional_fields():
    entry = FeedEntry(
        title=None,
        link=None,
        author=None,
        published_at=None,
        guid=None,
    )

    assert entry.tags == []
    assert entry.book_description is None
    assert entry.summary is None
    assert entry.content_html is None
    assert entry.source_feed_title is None


def test_feed_entry_tags_default_to_a_fresh_list_per_instance():
    first = FeedEntry(
        title=None,
        link=None,
        author=None,
        published_at=None,
        guid=None,
    )
    second = FeedEntry(
        title=None,
        link=None,
        author=None,
        published_at=None,
        guid=None,
    )

    first.tags.append("rss")

    assert first.tags == ["rss"]
    assert second.tags == []


def test_load_feed_raises_clear_error_for_missing_local_file(tmp_path):
    from rss2md.feed_loader import FeedLoadError, load_feed

    missing = tmp_path / "missing.xml"

    with pytest.raises(FeedLoadError, match="Unable to read local feed"):
        load_feed(str(missing))


def test_load_feed_raises_clear_error_for_http_failure(monkeypatch):
    from rss2md.feed_loader import FeedLoadError, load_feed

    def fake_fetch(_url: str) -> str:
        raise FeedLoadError("Unable to fetch remote feed: boom")

    monkeypatch.setattr("rss2md.feed_loader._fetch_remote_text", fake_fetch)

    with pytest.raises(FeedLoadError, match="Unable to fetch remote feed"):
        load_feed("https://example.com/feed.xml")


def test_parse_failure_raises_clear_error(tmp_path):
    from rss2md.feed_loader import FeedLoadError, load_feed

    bad = tmp_path / "bad.xml"
    bad.write_text("<rss><channel>", encoding="utf-8")

    with pytest.raises(FeedLoadError, match="Unable to parse feed"):
        load_feed(str(bad))


def test_load_feed_preserves_cdata_text_for_book_description():
    from rss2md.feed_loader import load_feed

    feed, entries = load_feed("tests/fixtures/sample_feed.xml")

    assert feed.title == "Sample Feed"
    assert entries[0].book_description == "First book description"
