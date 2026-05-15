# rss2md Design

## Goal

Build a small Python package with tests that provides a CLI for converting an RSS or Atom feed into Markdown files.

The first version should prioritize code quality and clear structure over feature breadth. The package is intended as a learning project for AI-assisted coding and Codex workflows, so the generated code should be easy to inspect, test, and extend.

## Scope

Version one should:

- accept either a feed URL or a local RSS/XML file as input
- parse the feed into normalized internal models
- write one Markdown file per entry
- include YAML frontmatter in each file
- prefer the best available content field for the Markdown body
- overwrite existing files that resolve to the same path
- include automated tests for the core behaviors

Version one should not:

- fetch full linked articles beyond the feed payload
- support user-defined output templates
- maintain a sync database or incremental state
- perform duplicate detection beyond path overwrite
- implement aggressive content cleanup heuristics

## CLI Behavior

The package should expose one main command:

```bash
rss2md convert <source> --output <dir>
```

Behavior:

- If `<source>` starts with `http://` or `https://`, treat it as a remote feed URL.
- Otherwise, treat `<source>` as a local file path.
- Parse the input feed and normalize feed and entry data into shared internal models.
- For each entry, choose the best available body field.
- Write one Markdown file per entry into the output directory.
- Print a concise completion summary with the number of files written.

Version one should keep the CLI intentionally narrow. It should not include dry-run mode, alternate output formats, or template configuration.

## Architecture

The package should be structured around a small set of focused modules:

- `cli.py` handles argument parsing and command orchestration.
- `feed_loader.py` loads a feed from either HTTP or a local file and converts raw parser output into normalized models.
- `models.py` defines typed feed and entry models.
- `html_conversion.py` converts HTML content into readable Markdown using a deterministic library-based pass.
- `markdown_writer.py` generates frontmatter, resolves filenames, and writes files to disk.

This separation is intentional:

- feed acquisition and parsing stop at normalized models
- Markdown rendering and filesystem output start from normalized models

That boundary keeps the code easy to test and avoids mixing network, parsing, formatting, and file-writing concerns.

## Data Model

Normalized feed-level fields:

- `title`
- `link`
- `description`

Normalized entry-level fields:

- `title`
- `link`
- `author`
- `published_at`
- `guid`
- `tags`
- `summary`
- `content_html`
- `source_feed_title`

The models should be simple typed containers with no heavy behavior. Any normalization logic should live in loader/conversion code rather than inside the model definitions.

## Conversion Rules

Content selection:

- Prefer `content_html` for the Markdown body when available.
- Fall back to `summary` if full content is missing.
- If both are missing, write an empty body rather than failing the entire run.

Content conversion:

- Preserve source content faithfully in version one.
- Convert HTML to Markdown using a deterministic library-driven pass rather than custom formatting heuristics.
- Avoid speculative cleanup logic that may destroy useful structure.

Frontmatter:

- Include `title`, `link`, `author`, `published_at`, `guid`, `tags`, and `source_feed_title` when present.
- Omit fields that are genuinely missing rather than inserting placeholder strings.

Filename resolution:

- Use a slugified title when a usable title is present.
- If the title is missing, fall back to `YYYY-MM-DD-<guid>.md`.
- If the date is missing, fall back to `undated-<guid>.md`.
- If `guid` is also missing, derive a stable fallback identifier from the link when available, otherwise from a hash of the selected body content.

Overwrite behavior:

- If the resolved output path already exists, overwrite it.

## Error Handling

Version one should keep error handling straightforward and explicit.

- Invalid or unreadable local files should produce a clear CLI error.
- HTTP fetch failures should produce a clear CLI error.
- Feed parsing failures should produce a clear CLI error.
- A malformed single entry should not silently poison output for other entries if the parser still returns usable entries.
- Missing optional entry fields should be handled through fallbacks rather than exceptions.

The CLI does not need sophisticated retry behavior or partial-run recovery in version one.

## Testing

The test suite should stay small but cover the key behaviors:

- parse a local fixture feed into normalized feed and entry models
- verify body selection priority: `content_html` before `summary`
- verify filename generation from a slugified title
- verify fallback filename generation from date plus guid
- verify YAML frontmatter emission
- verify overwrite behavior when a file already exists
- verify end-to-end CLI behavior using a fixture feed and a temporary output directory

Fixtures should live under `tests/fixtures/` and should be simple enough to understand without external dependencies.

## Proposed Project Layout

```text
rss2md/
  pyproject.toml
  README.md
  docs/
    superpowers/
      specs/
        2026-05-15-rss2md-design.md
  src/
    rss2md/
      __init__.py
      cli.py
      feed_loader.py
      models.py
      markdown_writer.py
      html_conversion.py
  tests/
    fixtures/
      sample_feed.xml
    test_feed_loader.py
    test_markdown_writer.py
    test_cli.py
```

## Out Of Scope

The following are explicitly out of scope for version one:

- article scraping from entry links
- feed subscription management
- custom Markdown templates
- JSON export
- incremental sync state
- deduplication beyond overwrite-by-path
- publishing or packaging automation beyond a normal Python package layout

## Rationale

This design favors a narrow, high-quality CLI with clear seams. That makes it a better vehicle for learning AI-assisted coding than a broader but less disciplined tool. The architecture is intentionally simple, but it preserves enough structure to support future extension without forcing speculative abstraction into version one.
