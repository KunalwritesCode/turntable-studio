"""Renders a .glb turntable into transparent PNG frames + a manifest the player can show."""

import base64
import contextlib
import json
import re
import shutil
import tempfile
from pathlib import Path

from playwright.sync_api import Browser, sync_playwright
from playwright.sync_api import Error as PlaywrightError

from turntable._localserver import serve_directory

RENDERER_DIR = Path(__file__).resolve().parent.parent.parent / "renderer"
FRAME_NAME = re.compile(r"\d{4}\.png$")


def _angles(frame_count: int) -> list[float]:
    """Evenly spaced angles (degrees) covering one full turn, without duplicating 0."""
    return [i * 360 / frame_count for i in range(frame_count)]


def render(
    model_path: Path,
    out_dir: Path,
    frame_count: int = 150,
    width: int = 1280,
    height: int = 720,
    browser: Browser | None = None,
) -> None:
    """Render `model_path` into `out_dir`/frames/*.png + `out_dir`/manifest.json.

    `browser` lets a caller that already has a running Playwright sync instance
    (such as a pytest-playwright fixture) reuse it; Playwright's sync API cannot
    be started a second time in the same process. When omitted, render() starts
    and closes its own.
    """
    model_path = Path(model_path)
    out_dir = Path(out_dir)
    if frame_count < 1:
        raise ValueError(f"frame_count must be >= 1, got {frame_count}")
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    with contextlib.ExitStack() as stack:
        if browser is None:
            playwright = stack.enter_context(sync_playwright())
            browser = playwright.chromium.launch()
            stack.callback(browser.close)
        _render_frames(browser, model_path, out_dir, frame_count, width, height)


def _render_frames(
    browser: Browser,
    model_path: Path,
    out_dir: Path,
    frame_count: int,
    width: int,
    height: int,
) -> None:
    with tempfile.TemporaryDirectory() as stage_dir:
        stage_dir = Path(stage_dir)
        shutil.copy(RENDERER_DIR / "index.html", stage_dir / "index.html")
        shutil.copy(RENDERER_DIR / "render.js", stage_dir / "render.js")
        shutil.copy(model_path, stage_dir / "model.glb")

        with serve_directory(stage_dir) as base_url:
            page = browser.new_page()
            try:
                page.goto(f"{base_url}index.html?width={width}&height={height}")
                status = "window.__turntableStatus"
                condition = f"{status} === 'ready' || {status} === 'error'"
                try:
                    page.wait_for_function(condition, timeout=15_000)
                except PlaywrightError:
                    raise RuntimeError(
                        f"renderer page for {model_path} never finished loading within 15s "
                        "(it loads three.js from cdn.jsdelivr.net; check that it's reachable)"
                    ) from None
                if page.evaluate("window.__turntableStatus") == "error":
                    error = page.evaluate("window.__turntableError")
                    raise RuntimeError(f"failed to load {model_path}: {error}")

                frames_dir = out_dir / "frames"
                if frames_dir.is_dir():
                    for stale in frames_dir.iterdir():
                        if stale.is_file() and FRAME_NAME.fullmatch(stale.name):
                            stale.unlink()
                frames_dir.mkdir(parents=True, exist_ok=True)

                frame_names = []
                for i, angle in enumerate(_angles(frame_count)):
                    data_url = page.evaluate("deg => window.renderAtAngle(deg)", angle)
                    png_bytes = base64.b64decode(data_url.split(",", 1)[1])
                    name = f"frames/{i + 1:04d}.png"
                    (out_dir / name).write_bytes(png_bytes)
                    frame_names.append(name)
            finally:
                page.close()

    manifest = {
        "version": 1,
        "title": "Turntable",
        "width": width,
        "height": height,
        "frames": frame_names,
        "credits": f"Rendered from {model_path.name}",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
