"""Checks for the renderer page and the local-server helper it (and conftest) share."""

import base64
import io
import shutil
import urllib.request
from pathlib import Path

from PIL import Image

from turntable._localserver import serve_directory

RENDERER_DIR = Path(__file__).resolve().parent.parent / "renderer"
FIXTURE = Path(__file__).parent / "fixtures" / "duck.glb"


def test_serve_directory_serves_a_file(tmp_path):
    (tmp_path / "hello.txt").write_text("hi")
    with serve_directory(tmp_path) as base_url:
        resp = urllib.request.urlopen(base_url + "hello.txt")
        assert resp.read() == b"hi"


def test_renders_a_transparent_frame_of_the_model(tmp_path, page):
    shutil.copy(FIXTURE, tmp_path / "model.glb")
    shutil.copy(RENDERER_DIR / "index.html", tmp_path / "index.html")
    shutil.copy(RENDERER_DIR / "render.js", tmp_path / "render.js")
    with serve_directory(tmp_path) as base_url:
        page.goto(f"{base_url}index.html?width=200&height=150")
        page.wait_for_function("window.__turntableStatus !== 'loading'", timeout=15_000)
        assert page.evaluate("window.__turntableStatus") == "ready"
        data_url = page.evaluate("window.renderAtAngle(0)")
        png_bytes = base64.b64decode(data_url.split(",", 1)[1])
        image = Image.open(io.BytesIO(png_bytes))
        assert image.size == (200, 150)
        alpha = image.getchannel("A")
        assert alpha.getextrema()[1] > 0, "the model should cover at least one opaque pixel"
