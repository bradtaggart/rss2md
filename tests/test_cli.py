from pathlib import Path

from typer.testing import CliRunner

from rss2md.cli import app


def test_cli_shows_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "convert" in result.stdout


def test_convert_command_writes_markdown_files(tmp_path):
    runner = CliRunner()
    fixture = Path("tests/fixtures/sample_feed.xml")

    result = runner.invoke(app, ["convert", str(fixture), "--output", str(tmp_path)])

    assert result.exit_code == 0
    assert "2 files written" in result.stdout
    assert (tmp_path / "first-entry.md").exists()
    assert (tmp_path / "second-entry.md").exists()
