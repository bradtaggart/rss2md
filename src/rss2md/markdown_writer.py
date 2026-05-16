import hashlib
import re
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path
from urllib.parse import urlparse

import yaml

from rss2md.html_conversion import to_markdown
from rss2md.models import FeedEntry


@dataclass(slots=True)
class WriteResult:
    paths: list[Path]
    created: int
    updated: int


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _strip_cdata(value: str) -> str:
    match = re.fullmatch(r"\s*<!\[CDATA\[(.*)\]\]>\s*", value, re.DOTALL)
    if match:
        return match.group(1)

    return value


def _remove_name_line(value: str) -> str:
    value = re.sub(r"(?is)<br\s*/?>\s*name:\s*[^<]*(?=<br\s*/?>|$)", "", value)
    return re.sub(r"(?im)^[ \t]*name:\s*.*(?:\n|$)", "", value)


def _fallback_identifier(entry: FeedEntry) -> str:
    if entry.guid:
        return entry.guid

    if entry.link:
        return urlparse(entry.link).path.strip("/").replace("/", "-") or "link"

    body = entry.content_html or entry.summary or ""
    return hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]


def resolve_entry_filename(entry: FeedEntry) -> str:
    slug = _slugify(entry.title) if entry.title else ""
    if slug:
        return f"{slug}.md"

    ident = _fallback_identifier(entry)
    if entry.published_at:
        date_part = entry.published_at.astimezone(timezone.utc).date().isoformat()
        return f"{date_part}-{ident}.md"

    return f"undated-{ident}.md"


def _frontmatter(entry: FeedEntry) -> dict[str, object]:
    data: dict[str, object] = {}
    for key in ("link", "author", "guid", "source_feed_title"):
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
    body = to_markdown(_remove_name_line(body_source))
    book_description = ""
    if entry.book_description:
        book_description = to_markdown(_remove_name_line(_strip_cdata(entry.book_description)))

    sections: list[str] = []
    if entry.title:
        sections.append(f"# {entry.title}")
    if book_description:
        sections.append(book_description)
    if body:
        sections.append(body)

    rendered_body = "\n\n".join(sections)
    frontmatter = yaml.safe_dump(_frontmatter(entry), sort_keys=False).strip()
    return f"---\n{frontmatter}\n---\n\n{rendered_body}\n"


def write_entries(entries: list[FeedEntry], output_dir: Path) -> WriteResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    created = 0
    updated = 0

    for entry in entries:
        path = output_dir / resolve_entry_filename(entry)
        if path.exists():
            updated += 1
        else:
            created += 1
        path.write_text(render_entry_markdown(entry), encoding="utf-8")
        written.append(path)

    return WriteResult(paths=written, created=created, updated=updated)
