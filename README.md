# rss2md

`rss2md` converts RSS or Atom feeds into Markdown files.

## Usage

```bash
rss2md convert path/to/feed.xml --output output/
rss2md convert https://example.com/feed.xml --output output/
```

Each entry becomes one Markdown file with YAML frontmatter. Existing files at the same resolved path are overwritten.
