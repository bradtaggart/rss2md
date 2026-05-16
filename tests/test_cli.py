from pathlib import Path

from typer.testing import CliRunner

from rss2md.cli import app


def test_cli_shows_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"], prog_name="rss2md")
    assert result.exit_code == 0
    assert "Usage: rss2md SOURCE OUTPUT" in result.stdout
    assert "SOURCE: Path to a local RSS/XML file or an http(s) feed URL." in result.stdout
    assert "OUTPUT: Directory where Markdown files will be written." in result.stdout


def test_cli_writes_markdown_files(tmp_path):
    runner = CliRunner()
    fixture = Path("tests/fixtures/sample_feed.xml")

    result = runner.invoke(app, [str(fixture), str(tmp_path)])

    assert result.exit_code == 0
    assert "2 files created, 0 files updated" in result.stdout
    assert (tmp_path / "first-entry.md").exists()
    assert (tmp_path / "second-entry.md").exists()


def test_convert_subcommand_is_invalid(tmp_path):
    runner = CliRunner()
    fixture = Path("tests/fixtures/sample_feed.xml")

    result = runner.invoke(app, ["convert", str(fixture), "--output", str(tmp_path)])

    assert result.exit_code != 0
