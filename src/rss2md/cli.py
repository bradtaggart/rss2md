from pathlib import Path

import typer

from rss2md.feed_loader import FeedLoadError, load_feed
from rss2md.markdown_writer import write_entries

app = typer.Typer(help="Convert RSS or Atom feeds into Markdown files.")


@app.callback()
def _app() -> None:
    pass


@app.command()
def convert(
    source: str,
    output: Path = typer.Option(..., "--output", file_okay=False, dir_okay=True),
) -> None:
    try:
        _feed, entries = load_feed(source)
        written = write_entries(entries, output)
    except FeedLoadError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"{len(written)} files written")


def main() -> None:
    app()
