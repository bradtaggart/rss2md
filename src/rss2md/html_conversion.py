from markdownify import markdownify as _markdownify


def to_markdown(value: str | None) -> str:
    if not value:
        return ""

    return _markdownify(value, heading_style="ATX").strip()
