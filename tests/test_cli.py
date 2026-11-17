from typer.testing import CliRunner

from turntable import __version__
from turntable.cli import app

runner = CliRunner()


def test_version_prints_installed_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_no_arguments_shows_help():
    result = runner.invoke(app, [])
    assert "Usage" in result.output
