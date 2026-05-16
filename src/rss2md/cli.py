from pathlib import Path

import typer
from typer.core import TyperCommand

from rss2md.feed_loader import FeedLoadError, load_feed
from rss2md.markdown_writer import write_entries


class RootCommand(TyperCommand):
    def collect_usage_pieces(self, ctx: typer.Context) -> list[str]:
        return [
            piece
            for param in self.get_params(ctx)
            for piece in param.get_usage_pieces(ctx)
        ]


app = typer.Typer(add_completion=False)


@app.command(
    name=None,
    cls=RootCommand,
)
def convert(
    source: str = typer.Argument(..., metavar="SOURCE"),
    output: Path = typer.Argument(..., metavar="OUTPUT", file_okay=False, dir_okay=True),
) -> None:
    """Convert RSS or Atom feeds into Markdown files.

    SOURCE: Path to a local RSS/XML file or an http(s) feed URL.
    OUTPUT: Directory where Markdown files will be written.
    """
    try:
        _feed, entries = load_feed(source)
        result = write_entries(entries, output)
    except FeedLoadError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"{result.created} files created, {result.updated} files updated")


def main() -> None:
    app()
