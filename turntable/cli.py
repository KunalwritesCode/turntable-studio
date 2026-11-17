"""Command-line entry point.

Commands are added milestone by milestone (see docs/scope.md):
render (M2), make and doctor (M3), build (M4).
"""

import typer

from turntable import __version__

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


if __name__ == "__main__":
    app()
