from datetime import datetime, timezone

from rss2md.html_conversion import to_markdown
from rss2md.models import FeedEntry


def test_to_markdown_converts_html_paragraphs_and_links():
    html = "<p>Hello <a href='https://example.com'>world</a></p>"

    result = to_markdown(html)

    assert "Hello" in result
    assert "[world](https://example.com)" in result


def test_resolve_entry_filename_slugifies_title():
    from rss2md.markdown_writer import resolve_entry_filename

    entry = FeedEntry(
        title="Hello, World!",
        link="https://example.com/hello",
        author=None,
        published_at=None,
        guid="hello-guid",
        tags=[],
        summary=None,
        content_html=None,
        source_feed_title="Feed",
    )

    assert resolve_entry_filename(entry) == "hello-world.md"


def test_resolve_entry_filename_falls_back_to_date_and_guid():
    from rss2md.markdown_writer import resolve_entry_filename

    entry = FeedEntry(
        title=None,
        link=None,
        author=None,
        published_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
        guid="abc123",
        tags=[],
        summary=None,
        content_html=None,
        source_feed_title="Feed",
    )

    assert resolve_entry_filename(entry) == "2026-05-15-abc123.md"


def test_render_entry_markdown_emits_yaml_frontmatter():
    from rss2md.markdown_writer import render_entry_markdown

    entry = FeedEntry(
        title="Entry",
        link="https://example.com/entry",
        author="Brad",
        published_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
        guid="entry-guid",
        tags=["python"],
        book_description="<p>Book <a href='https://example.com/book'>description</a></p>",
        summary="Summary",
        content_html="<p>Body</p>",
        source_feed_title="Feed",
    )

    result = render_entry_markdown(entry)

    assert result.startswith("---\n")
    assert "guid: entry-guid" in result
    assert "source_feed_title: Feed" in result
    assert "title: Entry" not in result
    assert "book_description:" not in result
    assert "\n# Entry\n" in result
    assert "Book [description](https://example.com/book)" in result
    assert "Body" in result


def test_write_entries_overwrites_existing_file(tmp_path):
    from rss2md.markdown_writer import write_entries

    entry = FeedEntry(
        title="Entry",
        link="https://example.com/entry",
        author=None,
        published_at=None,
        guid="entry-guid",
        tags=[],
        summary="Old summary",
        content_html="<p>New body</p>",
        source_feed_title="Feed",
    )
    output = tmp_path / "entry.md"
    output.write_text("old content", encoding="utf-8")

    result = write_entries([entry], tmp_path)

    assert result.paths == [output]
    assert result.created == 0
    assert result.updated == 1
    assert output.read_text(encoding="utf-8").endswith("New body\n")


def test_write_entries_reports_created_and_updated_counts(tmp_path):
    from rss2md.markdown_writer import write_entries

    created_entry = FeedEntry(
        title="Created Entry",
        link="https://example.com/created",
        author=None,
        published_at=None,
        guid="created-guid",
        tags=[],
        summary=None,
        content_html="<p>Created body</p>",
        source_feed_title="Feed",
    )
    updated_entry = FeedEntry(
        title="Updated Entry",
        link="https://example.com/updated",
        author=None,
        published_at=None,
        guid="updated-guid",
        tags=[],
        summary=None,
        content_html="<p>Updated body</p>",
        source_feed_title="Feed",
    )

    existing_path = tmp_path / "updated-entry.md"
    existing_path.write_text("old content", encoding="utf-8")

    result = write_entries([created_entry, updated_entry], tmp_path)

    assert result.created == 1
    assert result.updated == 1
    assert result.paths == [tmp_path / "created-entry.md", existing_path]


def test_body_selection_prefers_content_html_over_summary():
    from rss2md.markdown_writer import render_entry_markdown

    entry = FeedEntry(
        title="Entry",
        link=None,
        author=None,
        published_at=None,
        guid="guid",
        tags=[],
        summary="<p>Summary body</p>",
        content_html="<p>Primary body</p>",
        source_feed_title="Feed",
    )

    result = render_entry_markdown(entry)

    assert "Primary body" in result
    assert "Summary body" not in result


def test_render_entry_markdown_converts_cdata_backed_html_body_to_markdown():
    from rss2md.markdown_writer import render_entry_markdown

    entry = FeedEntry(
        title="Entry",
        link=None,
        author=None,
        published_at=None,
        guid="guid",
        tags=[],
        summary="<![CDATA[<p>Summary body</p>]]>",
        content_html="<p>Hello <a href='https://example.com'>world</a></p>",
        source_feed_title="Feed",
    )

    result = render_entry_markdown(entry)

    assert "Hello" in result
    assert "[world](https://example.com)" in result


def test_render_entry_markdown_converts_cdata_backed_book_description_to_markdown():
    from rss2md.markdown_writer import render_entry_markdown

    entry = FeedEntry(
        title="Entry",
        link=None,
        author=None,
        published_at=None,
        guid="guid",
        tags=[],
        book_description="<![CDATA[<p>Book <a href='https://example.com/book'>description</a></p>]]>",
        summary=None,
        content_html="<p>Body</p>",
        source_feed_title="Feed",
    )

    result = render_entry_markdown(entry)

    assert "book_description:" not in result
    assert "Book [description](https://example.com/book)" in result


def test_render_entry_markdown_removes_name_line_from_book_description():
    from rss2md.markdown_writer import render_entry_markdown

    entry = FeedEntry(
        title="Entry",
        link=None,
        author=None,
        published_at=None,
        guid="guid",
        tags=[],
        book_description=(
            "author: Joseph John\n"
            "name: Brad Taggart\n"
            "average rating: 4.09\n"
            "book published: 2016\n"
            "rating: 0\n"
            "read at:\n"
            "date added: 2026/05/10\n"
            "shelves: to-read\n"
            "review:"
        ),
        summary=None,
        content_html="<p>Body</p>",
        source_feed_title="Feed",
    )

    result = render_entry_markdown(entry)

    assert "name: Brad Taggart" not in result
    assert "author: Joseph John" in result
    assert "average rating: 4.09" in result
    assert "book published: 2016" in result


def test_render_entry_markdown_removes_name_line_from_body_content():
    from rss2md.markdown_writer import render_entry_markdown

    entry = FeedEntry(
        title="Entry",
        link=None,
        author=None,
        published_at=None,
        guid="guid",
        tags=[],
        book_description=None,
        summary=(
            "author: Joseph John\n"
            "name: Brad Taggart\n"
            "average rating: 4.09\n"
            "book published: 2016\n"
        ),
        content_html=None,
        source_feed_title="Feed",
    )

    result = render_entry_markdown(entry)

    assert "name: Brad Taggart" not in result
    assert "author: Joseph John" in result
    assert "average rating: 4.09" in result
