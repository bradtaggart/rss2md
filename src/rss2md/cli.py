import typer

app = typer.Typer(help="Convert RSS or Atom feeds into Markdown files.")


@app.command()
def convert(source: str, output: str = typer.Option(..., "--output")) -> None:
    raise typer.Exit(code=0)


def main() -> None:
    app()
