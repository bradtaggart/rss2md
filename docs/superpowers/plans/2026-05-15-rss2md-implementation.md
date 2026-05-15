# rss2md Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small Python package with a `rss2md convert <source> --output <dir>` CLI that converts RSS or Atom feeds into one Markdown file per entry with YAML frontmatter.

**Architecture:** Keep the package split across focused modules: CLI orchestration, feed loading/normalization, HTML-to-Markdown conversion, and Markdown writing. Normalize all parser output into typed models first, then perform body selection, frontmatter generation, filename resolution, and file output from those models.

**Tech Stack:** Python 3.12, `pytest`, `feedparser`, `httpx`, `markdownify`, `PyYAML`, `typer`

---

## File Structure

- `pyproject.toml`: package metadata, dependencies, console script, pytest config.
- `README.md`: short usage instructions and project purpose.
- `src/rss2md/__init__.py`: package version export.
- `src/rss2md/models.py`: typed feed and entry models.
- `src/rss2md/feed_loader.py`: local/HTTP loading, feed parsing, normalization.
- `src/rss2md/html_conversion.py`: HTML/plain-text body conversion helpers.
- `src/rss2md/markdown_writer.py`: frontmatter rendering, filename resolution, file writing.
- `src/rss2md/cli.py`: CLI entrypoint and orchestration.
- `tests/fixtures/sample_feed.xml`: readable fixture with feed metadata and multiple entry shapes.
- `tests/test_feed_loader.py`: loader normalization tests and error-path tests.
- `tests/test_markdown_writer.py`: filename, frontmatter, overwrite, and body-selection tests.
- `tests/test_cli.py`: end-to-end CLI behavior tests.

### Task 1: Bootstrap Package Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/rss2md/__init__.py`
- Create: `src/rss2md/cli.py`
- Test: `pytest -q`

- [ ] **Step 1: Write the failing CLI smoke test**

```python
# tests/test_cli.py
from typer.testing import CliRunner

from rss2md.cli import app


def test_cli_shows_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "convert" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_cli_shows_help -v`
Expected: FAIL with `ModuleNotFoundError` or import failure because package files do not exist yet.

- [ ] **Step 3: Write minimal package/bootstrap implementation**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "rss2md"
version = "0.1.0"
description = "Convert RSS or Atom feeds into Markdown files"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "feedparser>=6.0.11",
  "httpx>=0.27.0",
  "markdownify>=0.13.1",
  "PyYAML>=6.0.2",
  "typer>=0.12.3",
]

[project.optional-dependencies]
dev = ["pytest>=8.2.0"]

[project.scripts]
rss2md = "rss2md.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```python
# src/rss2md/__init__.py
__all__ = ["__version__"]

__version__ = "0.1.0"
```

```python
# src/rss2md/cli.py
import typer

app = typer.Typer(help="Convert RSS or Atom feeds into Markdown files.")


@app.command()
def convert(source: str, output: str = typer.Option(..., "--output")) -> None:
    raise typer.Exit(code=0)


def main() -> None:
    app()
```

```markdown
# README.md

`rss2md` converts RSS or Atom feeds into Markdown files.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py::test_cli_shows_help -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md src/rss2md/__init__.py src/rss2md/cli.py tests/test_cli.py
git commit -m "chore: bootstrap rss2md package"
```

### Task 2: Define Normalized Models

**Files:**
- Create: `src/rss2md/models.py`
- Modify: `tests/test_feed_loader.py`
- Test: `tests/test_feed_loader.py`

- [ ] **Step 1: Write the failing model normalization test**

```python
# tests/test_feed_loader.py
from datetime import datetime, timezone

from rss2md.models import Feed, FeedEntry


def test_feed_entry_model_holds_normalized_fields():
    entry = FeedEntry(
        title="Example",
        link="https://example.com/post",
        author="Brad",
        published_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
        guid="abc123",
        tags=["rss", "python"],
        summary="Summary",
        content_html="<p>Body</p>",
        source_feed_title="Example Feed",
    )
    feed = Feed(title="Example Feed", link="https://example.com", description="Desc")
    assert entry.guid == "abc123"
    assert feed.title == "Example Feed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_feed_loader.py::test_feed_entry_model_holds_normalized_fields -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'rss2md.models'`

- [ ] **Step 3: Write minimal typed models**

```python
# src/rss2md/models.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Feed:
    title: str | None
    link: str | None
    description: str | None


@dataclass(slots=True)
class FeedEntry:
    title: str | None
    link: str | None
    author: str | None
    published_at: datetime | None
    guid: str | None
    tags: list[str] = field(default_factory=list)
    summary: str | None = None
    content_html: str | None = None
    source_feed_title: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_feed_loader.py::test_feed_entry_model_holds_normalized_fields -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rss2md/models.py tests/test_feed_loader.py
git commit -m "feat: add normalized feed models"
```

### Task 3: Add Feed Fixture And Local Feed Loading

**Files:**
- Create: `tests/fixtures/sample_feed.xml`
- Create: `src/rss2md/feed_loader.py`
- Modify: `tests/test_feed_loader.py`
- Test: `tests/test_feed_loader.py`

- [ ] **Step 1: Write the failing local-feed test**

```python
from pathlib import Path

from rss2md.feed_loader import load_feed


def test_load_feed_parses_local_fixture():
    fixture = Path("tests/fixtures/sample_feed.xml")
    feed, entries = load_feed(str(fixture))
    assert feed.title == "Sample Feed"
    assert len(entries) == 2
    assert entries[0].title == "First Entry"
    assert entries[0].source_feed_title == "Sample Feed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_feed_loader.py::test_load_feed_parses_local_fixture -v`
Expected: FAIL because `load_feed` is undefined and the fixture file does not exist yet.

- [ ] **Step 3: Add the fixture and minimal loader**

```xml
<!-- tests/fixtures/sample_feed.xml -->
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Sample Feed</title>
    <link>https://example.com</link>
    <description>Example description</description>
    <item>
      <title>First Entry</title>
      <link>https://example.com/first</link>
      <guid>first-guid</guid>
      <author>author@example.com</author>
      <pubDate>Fri, 15 May 2026 12:00:00 GMT</pubDate>
      <category>python</category>
      <description><![CDATA[<p>First summary</p>]]></description>
      <content:encoded><![CDATA[<p>First body</p>]]></content:encoded>
    </item>
    <item>
      <title>Second Entry</title>
      <link>https://example.com/second</link>
      <guid>second-guid</guid>
      <description><![CDATA[<p>Second summary</p>]]></description>
    </item>
  </channel>
</rss>
```

```python
# src/rss2md/feed_loader.py
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser

from rss2md.models import Feed, FeedEntry


def _normalize_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = parsedate_to_datetime(value)
    return parsed.astimezone(timezone.utc)


def load_feed(source: str) -> tuple[Feed, list[FeedEntry]]:
    raw = feedparser.parse(Path(source).read_text(encoding="utf-8"))
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
            published_at=_normalize_datetime(item.get("published")),
            guid=item.get("id") or item.get("guid"),
            tags=[tag["term"] for tag in item.get("tags", []) if tag.get("term")],
            summary=item.get("summary"),
            content_html=(item.get("content") or [{}])[0].get("value"),
            source_feed_title=feed.title,
        )
        for item in raw.entries
    ]
    return feed, entries
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_feed_loader.py::test_load_feed_parses_local_fixture -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/sample_feed.xml src/rss2md/feed_loader.py tests/test_feed_loader.py
git commit -m "feat: load and normalize local feed fixtures"
```

### Task 4: Cover Loader Error Paths And Remote Loading

**Files:**
- Modify: `src/rss2md/feed_loader.py`
- Modify: `tests/test_feed_loader.py`
- Test: `tests/test_feed_loader.py`

- [ ] **Step 1: Write the failing error-path tests**

```python
import pytest

from rss2md.feed_loader import FeedLoadError, load_feed


def test_load_feed_raises_clear_error_for_missing_local_file(tmp_path):
    missing = tmp_path / "missing.xml"
    with pytest.raises(FeedLoadError, match="Unable to read local feed"):
        load_feed(str(missing))


def test_load_feed_raises_clear_error_for_http_failure(monkeypatch):
    class DummyError(Exception):
        pass

    def fake_fetch(_url: str) -> str:
        raise FeedLoadError("Unable to fetch remote feed: boom")

    monkeypatch.setattr("rss2md.feed_loader._fetch_remote_text", fake_fetch)
    with pytest.raises(FeedLoadError, match="Unable to fetch remote feed"):
        load_feed("https://example.com/feed.xml")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_feed_loader.py -k "missing_local_file or http_failure" -v`
Expected: FAIL because `FeedLoadError` and remote-fetch support do not exist yet.

- [ ] **Step 3: Implement explicit load errors and remote fetching**

```python
# src/rss2md/feed_loader.py
from pathlib import Path

import httpx


class FeedLoadError(Exception):
    pass


def _fetch_remote_text(url: str) -> str:
    try:
        response = httpx.get(url, follow_redirects=True, timeout=10.0)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as exc:
        raise FeedLoadError(f"Unable to fetch remote feed: {exc}") from exc


def _read_source_text(source: str) -> str:
    if source.startswith(("http://", "https://")):
        return _fetch_remote_text(source)
    try:
        return Path(source).read_text(encoding="utf-8")
    except OSError as exc:
        raise FeedLoadError(f"Unable to read local feed: {source}") from exc
```

```python
# src/rss2md/feed_loader.py
def load_feed(source: str) -> tuple[Feed, list[FeedEntry]]:
    raw = feedparser.parse(_read_source_text(source))
    if raw.bozo and not raw.entries:
        raise FeedLoadError(f"Unable to parse feed: {raw.bozo_exception}")
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_feed_loader.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rss2md/feed_loader.py tests/test_feed_loader.py
git commit -m "feat: add remote loading and clear feed errors"
```

### Task 5: Add HTML Conversion Helpers

**Files:**
- Create: `src/rss2md/html_conversion.py`
- Modify: `tests/test_markdown_writer.py`
- Test: `tests/test_markdown_writer.py`

- [ ] **Step 1: Write the failing body-conversion test**

```python
from rss2md.html_conversion import to_markdown


def test_to_markdown_converts_html_paragraphs_and_links():
    html = "<p>Hello <a href='https://example.com'>world</a></p>"
    result = to_markdown(html)
    assert "Hello" in result
    assert "[world](https://example.com)" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_markdown_writer.py::test_to_markdown_converts_html_paragraphs_and_links -v`
Expected: FAIL because `html_conversion.py` does not exist yet.

- [ ] **Step 3: Implement deterministic HTML conversion**

```python
# src/rss2md/html_conversion.py
from markdownify import markdownify as _markdownify


def to_markdown(value: str | None) -> str:
    if not value:
        return ""
    return _markdownify(value, heading_style="ATX").strip()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_markdown_writer.py::test_to_markdown_converts_html_paragraphs_and_links -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rss2md/html_conversion.py tests/test_markdown_writer.py
git commit -m "feat: add html to markdown conversion helper"
```

### Task 6: Implement Markdown Writer And Filename Resolution

**Files:**
- Create: `src/rss2md/markdown_writer.py`
- Modify: `tests/test_markdown_writer.py`
- Test: `tests/test_markdown_writer.py`

- [ ] **Step 1: Write the failing writer tests**

```python
from datetime import datetime, timezone

from rss2md.markdown_writer import render_entry_markdown, resolve_entry_filename
from rss2md.models import FeedEntry


def test_resolve_entry_filename_slugifies_title():
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
    entry = FeedEntry(
        title="Entry",
        link="https://example.com/entry",
        author="Brad",
        published_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
        guid="entry-guid",
        tags=["python"],
        summary="Summary",
        content_html="<p>Body</p>",
        source_feed_title="Feed",
    )
    result = render_entry_markdown(entry)
    assert result.startswith("---\n")
    assert "title: Entry" in result
    assert "guid: entry-guid" in result
    assert "source_feed_title: Feed" in result
    assert "Body" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_markdown_writer.py -k "slugifies_title or falls_back_to_date_and_guid or emits_yaml_frontmatter" -v`
Expected: FAIL because writer functions do not exist yet.

- [ ] **Step 3: Implement filename resolution and frontmatter rendering**

```python
# src/rss2md/markdown_writer.py
from datetime import timezone
import hashlib
import re
from urllib.parse import urlparse

import yaml

from rss2md.html_conversion import to_markdown
from rss2md.models import FeedEntry


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug


def _fallback_identifier(entry: FeedEntry) -> str:
    if entry.guid:
        return entry.guid
    if entry.link:
        return urlparse(entry.link).path.strip("/").replace("/", "-") or "link"
    body = entry.content_html or entry.summary or ""
    return hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]


def resolve_entry_filename(entry: FeedEntry) -> str:
    if entry.title and _slugify(entry.title):
        return f"{_slugify(entry.title)}.md"
    ident = _fallback_identifier(entry)
    if entry.published_at:
        date_part = entry.published_at.astimezone(timezone.utc).date().isoformat()
        return f"{date_part}-{ident}.md"
    return f"undated-{ident}.md"


def _frontmatter(entry: FeedEntry) -> dict[str, object]:
    data: dict[str, object] = {}
    for key in ("title", "link", "author", "guid", "source_feed_title"):
        value = getattr(entry, key)
        if value:
            data[key] = value
    if entry.published_at:
        data["published_at"] = entry.published_at.astimezone(timezone.utc).isoformat()
    if entry.tags:
        data["tags"] = entry.tags
    return data


def render_entry_markdown(entry: FeedEntry) -> str:
    body_source = entry.content_html or entry.summary or ""
    body = to_markdown(body_source)
    frontmatter = yaml.safe_dump(_frontmatter(entry), sort_keys=False).strip()
    return f"---\n{frontmatter}\n---\n\n{body}\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_markdown_writer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rss2md/markdown_writer.py tests/test_markdown_writer.py
git commit -m "feat: render markdown with frontmatter"
```

### Task 7: Add File Writing And Overwrite Behavior

**Files:**
- Modify: `src/rss2md/markdown_writer.py`
- Modify: `tests/test_markdown_writer.py`
- Test: `tests/test_markdown_writer.py`

- [ ] **Step 1: Write the failing overwrite test**

```python
from pathlib import Path

from rss2md.markdown_writer import write_entries
from rss2md.models import FeedEntry


def test_write_entries_overwrites_existing_file(tmp_path):
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
    paths = write_entries([entry], tmp_path)
    assert paths == [output]
    assert output.read_text(encoding="utf-8").endswith("New body\n")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_markdown_writer.py::test_write_entries_overwrites_existing_file -v`
Expected: FAIL because `write_entries` does not exist yet.

- [ ] **Step 3: Implement output writing**

```python
# src/rss2md/markdown_writer.py
from pathlib import Path


def write_entries(entries: list[FeedEntry], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for entry in entries:
        path = output_dir / resolve_entry_filename(entry)
        path.write_text(render_entry_markdown(entry), encoding="utf-8")
        written.append(path)
    return written
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_markdown_writer.py::test_write_entries_overwrites_existing_file -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rss2md/markdown_writer.py tests/test_markdown_writer.py
git commit -m "feat: write markdown files to disk"
```

### Task 8: Wire The CLI End To End

**Files:**
- Modify: `src/rss2md/cli.py`
- Modify: `tests/test_cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI conversion test**

```python
from pathlib import Path

from typer.testing import CliRunner

from rss2md.cli import app


def test_convert_command_writes_markdown_files(tmp_path):
    runner = CliRunner()
    fixture = Path("tests/fixtures/sample_feed.xml")
    result = runner.invoke(app, ["convert", str(fixture), "--output", str(tmp_path)])
    assert result.exit_code == 0
    assert "2 files written" in result.stdout
    assert (tmp_path / "first-entry.md").exists()
    assert (tmp_path / "second-entry.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_convert_command_writes_markdown_files -v`
Expected: FAIL because `convert` does not orchestrate loading and writing yet.

- [ ] **Step 3: Implement CLI orchestration and clear user-facing errors**

```python
# src/rss2md/cli.py
from pathlib import Path

import typer

from rss2md.feed_loader import FeedLoadError, load_feed
from rss2md.markdown_writer import write_entries

app = typer.Typer(help="Convert RSS or Atom feeds into Markdown files.")


@app.command()
def convert(source: str, output: Path = typer.Option(..., "--output", file_okay=False, dir_okay=True)) -> None:
    try:
        _feed, entries = load_feed(source)
        written = write_entries(entries, output)
    except FeedLoadError as exc:
        raise typer.Exit(message=str(exc), code=1)
    typer.echo(f"{len(written)} files written")


def main() -> None:
    app()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/rss2md/cli.py tests/test_cli.py
git commit -m "feat: add convert cli command"
```

### Task 9: Add Final Regression Coverage And Documentation

**Files:**
- Modify: `tests/test_feed_loader.py`
- Modify: `tests/test_markdown_writer.py`
- Modify: `README.md`
- Test: `pytest -q`

- [ ] **Step 1: Write the remaining failing regression tests**

```python
def test_body_selection_prefers_content_html_over_summary():
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


def test_parse_failure_raises_clear_error(tmp_path):
    bad = tmp_path / "bad.xml"
    bad.write_text("<rss><channel>", encoding="utf-8")
    with pytest.raises(FeedLoadError, match="Unable to parse feed"):
        load_feed(str(bad))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_feed_loader.py tests/test_markdown_writer.py -k "prefers_content_html or parse_failure" -v`
Expected: FAIL until parse-failure handling and body-priority behavior are confirmed.

- [ ] **Step 3: Finalize code paths and README usage**

```markdown
# README.md

## Usage

```bash
rss2md convert path/to/feed.xml --output output/
rss2md convert https://example.com/feed.xml --output output/
```

Each entry becomes one Markdown file with YAML frontmatter. Existing files at the same resolved path are overwritten.
```

- [ ] **Step 4: Run the full test suite**

Run: `pytest -q`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_feed_loader.py tests/test_markdown_writer.py
git commit -m "test: add regression coverage and usage docs"
```

## Self-Review

- Spec coverage: local and remote inputs, normalized models, body selection, frontmatter, overwrite behavior, clear load/parse errors, and end-to-end CLI flow are all mapped to Tasks 1-9.
- Gap check: the spec-review ambiguity about same-run filename collisions remains intentionally unexpanded here because the spec currently says overwrite-by-path and explicitly excludes deduplication beyond that.
- Type consistency: `published_at` is planned as `datetime | None`, serialized as UTC ISO 8601 in frontmatter, and used as UTC date for fallback filenames throughout the plan.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-15-rss2md-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
