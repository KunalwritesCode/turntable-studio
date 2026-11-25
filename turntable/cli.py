"""Command-line entry point.

Commands are added milestone by milestone (see docs/scope.md):
render (M2), make and doctor (M3), build (M4).
"""

from pathlib import Path

import typer

from turntable import __version__
from turntable.stages.render import render as render_frames

app = typer.Typer(
    help="Turn a prompt or picture into a scroll-driven 360-degree turntable page.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Turntable Studio."""


@app.command()
def version() -> None:
    """Print the installed version."""
    typer.echo(f"turntable-studio {__version__}")


@app.command()
def render(
    model: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
    frames: int = typer.Option(150, "--frames", min=1),
    out: Path = typer.Option(Path("player"), "--out"),
    width: int = typer.Option(1280, "--width"),
    height: int = typer.Option(720, "--height"),
) -> None:
    """Render model.glb into transparent PNG frames + a manifest the player can show."""
    try:
        render_frames(model, out, frames, width, height)
    except (ValueError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Wrote {frames} frames to {out}")


if __name__ == "__main__":
    app()
