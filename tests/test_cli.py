import functools
from pathlib import Path

from typer.testing import CliRunner

import turntable.cli as cli
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


def test_render_writes_frames_and_manifest(tmp_path, browser, monkeypatch):
    # Reuses pytest-playwright's already-running sync instance (see
    # turntable/stages/render.py) instead of letting the CLI start its own,
    # which would collide if another test already activated one this session.
    monkeypatch.setattr(cli, "render_frames", functools.partial(cli.render_frames, browser=browser))
    fixture = Path(__file__).parent / "fixtures" / "duck.glb"
    result = runner.invoke(app, ["render", str(fixture), "--frames", "3", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "manifest.json").exists()
    assert len(list((tmp_path / "frames").glob("*.png"))) == 3


def test_render_reports_a_missing_model_clearly():
    result = runner.invoke(app, ["render", "no-such-file.glb"])
    assert result.exit_code != 0
    assert "no-such-file.glb" in result.output
