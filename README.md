# rss2md

`rss2md` converts RSS or Atom feeds into Markdown files.

## Usage

```bash
rss2md path/to/feed.xml output/
rss2md https://example.com/feed.xml output/
```

Each entry becomes one Markdown file with YAML frontmatter. Existing files at the same resolved path are overwritten.
