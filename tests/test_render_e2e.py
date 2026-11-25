"""Proves M2's 'done when': the player shows a turntable rendered from a real .glb."""

import shutil
from pathlib import Path

from helpers import scroll_to, wait_for_frame

from turntable._localserver import serve_directory
from turntable.stages.render import render

FIXTURE = Path(__file__).parent / "fixtures" / "duck.glb"
PLAYER_DIR = Path(__file__).resolve().parent.parent / "player"


def test_player_shows_a_real_rendered_turntable(tmp_path, page, browser):
    render(FIXTURE, tmp_path, frame_count=24, width=320, height=240, browser=browser)
    for name in ("index.html", "style.css", "player.js"):
        shutil.copy2(PLAYER_DIR / name, tmp_path / name)

    with serve_directory(tmp_path) as site_url:
        page.goto(site_url)
        wait_for_frame(page, 0)
        alpha = page.evaluate(
            """() => {
                const c = document.getElementById('turntable');
                const x = c.width / 2 | 0, y = c.height / 2 | 0;
                return c.getContext('2d').getImageData(x, y, 1, 1).data[3];
            }"""
        )
        assert alpha > 0

        scroll_to(page, 1.0)
        wait_for_frame(page, 23, tolerance=1)
