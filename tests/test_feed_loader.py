from datetime import datetime, timezone
from pathlib import Path

from rss2md.models import Feed, FeedEntry


def test_load_feed_parses_local_fixture():
    from rss2md.feed_loader import load_feed

    fixture = Path("tests/fixtures/sample_feed.xml")

    feed, entries = load_feed(str(fixture))

    assert feed.title == "Sample Feed"
    assert len(entries) == 2
    assert entries[0].title == "First Entry"
    assert entries[0].source_feed_title == "Sample Feed"


def test_feed_entry_model_holds_normalized_fields():
    published_at = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)

    entry = FeedEntry(
        title="Example",
        link="https://example.com/post",
        author="Brad",
        published_at=published_at,
        guid="abc123",
        tags=["rss", "python"],
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
