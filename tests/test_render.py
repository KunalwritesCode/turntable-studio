"""Checks for the render stage: drives the renderer page into PNG frames + a manifest.

Each test passes the pytest-playwright session `browser` fixture into render():
Playwright's sync API can't be started a second time in the same process, and
this session already has one running (from the page/browser fixtures other
test modules use).
"""

import json
from pathlib import Path

import pytest
from PIL import Image

from turntable.stages.render import _angles, render

FIXTURE = Path(__file__).parent / "fixtures" / "duck.glb"


def test_writes_the_requested_number_of_frames_and_a_manifest(tmp_path, browser):
    render(FIXTURE, tmp_path, frame_count=5, width=160, height=120, browser=browser)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["version"] == 1
    assert manifest["width"] == 160 and manifest["height"] == 120
    assert manifest["frames"] == [f"frames/{i:04d}.png" for i in range(1, 6)]
    assert manifest["credits"]
    for name in manifest["frames"]:
        image = Image.open(tmp_path / name)
        assert image.size == (160, 120)
        assert image.getchannel("A").getextrema()[1] > 0


def test_consecutive_frames_differ_because_the_model_rotates(tmp_path, browser):
    render(FIXTURE, tmp_path, frame_count=4, width=160, height=120, browser=browser)
    first = (tmp_path / "frames" / "0001.png").read_bytes()
    second = (tmp_path / "frames" / "0002.png").read_bytes()
    assert first != second


def test_clears_stale_frames_from_a_previous_larger_run(tmp_path, browser):
    render(FIXTURE, tmp_path, frame_count=5, width=160, height=120, browser=browser)
    render(FIXTURE, tmp_path, frame_count=2, width=160, height=120, browser=browser)
    assert sorted(p.name for p in (tmp_path / "frames").iterdir()) == ["0001.png", "0002.png"]


def test_rerender_does_not_delete_unrelated_files_in_out_dir(tmp_path, browser):
    render(FIXTURE, tmp_path, frame_count=3, width=160, height=120, browser=browser)
    keepsake = tmp_path / "frames" / "notes.txt"
    keepsake.write_text("do not delete me")
    render(FIXTURE, tmp_path, frame_count=2, width=160, height=120, browser=browser)
    assert keepsake.exists()


def test_rejects_a_frame_count_below_one(tmp_path):
    with pytest.raises(ValueError):
        render(FIXTURE, tmp_path, frame_count=0)


def test_rejects_a_missing_model_path(tmp_path):
    with pytest.raises(FileNotFoundError):
        render(tmp_path / "missing.glb", tmp_path, frame_count=1)


def test_raises_a_clear_bounded_error_when_the_cdn_is_unreachable(tmp_path, browser, monkeypatch):
    # render() creates its own page internally, so this intercepts it at the
    # browser level: every page it opens gets the CDN blocked before navigating.
    original_new_page = browser.new_page

    def blocked_new_page(*args, **kwargs):
        new_page = original_new_page(*args, **kwargs)
        new_page.route("https://cdn.jsdelivr.net/**", lambda route: route.abort())
        return new_page

    monkeypatch.setattr(browser, "new_page", blocked_new_page)
    with pytest.raises(RuntimeError, match="never finished loading"):
        render(FIXTURE, tmp_path, frame_count=1, browser=browser)


def test_raises_a_clear_error_for_an_invalid_model(tmp_path, browser):
    bad_model = tmp_path / "not-a-model.glb"
    bad_model.write_bytes(b"not a real glb file")
    with pytest.raises(RuntimeError):
        render(bad_model, tmp_path, frame_count=1, browser=browser)


def test_frames_span_a_full_turn_without_duplicating_the_first(tmp_path, browser):
    render(FIXTURE, tmp_path, frame_count=4, width=160, height=120, browser=browser)
    first = (tmp_path / "frames" / "0001.png").read_bytes()
    last = (tmp_path / "frames" / "0004.png").read_bytes()
    assert first != last


def test_angles_span_a_full_turn_evenly():
    assert _angles(4) == [0, 90, 180, 270]


def test_camera_fits_the_model_in_portrait_orientation(tmp_path, browser):
    render(FIXTURE, tmp_path, frame_count=1, width=160, height=300, browser=browser)
    image = Image.open(tmp_path / "frames" / "0001.png")
    left, top, right, bottom = image.getchannel("A").getbbox()
    assert left > 0 and right < image.width, (
        f"model touches the left/right edge in a portrait render: "
        f"bbox=({left}, {top}, {right}, {bottom}), size={image.size}"
    )
