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
