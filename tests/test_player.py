"""End-to-end checks for the scroll player. Each test maps to a rule in docs/player-spec.md."""

import re

import pytest
from fixture_frames import DEFAULT_COUNT as COUNT
from fixture_frames import KEYFRAME_STEP
from helpers import scroll_to, state, wait_for_frame, wait_until
from playwright.sync_api import Page

FRAME_URL = re.compile(r"/frames/(\d{4})\.webp$")
KEYFRAMES = list(range(0, COUNT, KEYFRAME_STEP))


def frame_index(url: str) -> int | None:
    match = FRAME_URL.search(url)
    return int(match.group(1)) - 1 if match else None


def wait_all_loaded(page: Page) -> None:
    wait_until(page, f"c.dataset.loaded === '{COUNT}'", f"all {COUNT} frames to load", 10_000)


def test_first_frame_is_drawn(page: Page, site_url: str):
    """Spec 1, 3, 6: manifest loads and frame 0 appears on the canvas."""
    page.goto(site_url)
    wait_for_frame(page, 0)
    alpha = page.evaluate(
        """() => {
            const c = document.getElementById('turntable');
            return c.getContext('2d').getImageData(c.width / 2 | 0, c.height / 2 | 0, 1, 1).data[3];
        }"""
    )
    assert alpha > 0, "data-frame says frame 0 was drawn, but the canvas centre is empty"


def test_frames_load_keyframes_first(page: Page, site_url: str):
    """Spec 2: frame 0, then every 8th frame, then the rest, each requested once."""
    requested = []
    page.on("request", lambda request: requested.append(frame_index(request.url)))
    page.goto(site_url)
    wait_all_loaded(page)
    requested = [index for index in requested if index is not None]

    assert sorted(requested) == list(range(COUNT)), "every frame should be requested exactly once"
    assert requested[: len(KEYFRAMES)] == KEYFRAMES, (
        f"first requests should be the keyframes {KEYFRAMES}, got {requested[: len(KEYFRAMES)]}"
    )


@pytest.mark.parametrize("fraction", [0.25, 0.5, 0.75, 1.0])
def test_scroll_position_selects_frame(page: Page, site_url: str, fraction: float):
    """Spec 4: scroll progress maps to round(progress * (count - 1))."""
    page.goto(site_url)
    wait_all_loaded(page)
    scroll_to(page, fraction)
    wait_for_frame(page, round(fraction * (COUNT - 1)), tolerance=1)


def test_scrolling_back_to_top_returns_to_first_frame(page: Page, site_url: str):
    page.goto(site_url)
    wait_all_loaded(page)
    scroll_to(page, 1.0)
    wait_for_frame(page, COUNT - 1, tolerance=1)
    scroll_to(page, 0.0)
    wait_for_frame(page, 0)


def test_missing_frame_falls_back_to_nearest_loaded(page: Page, site_url: str):
    """Spec 5: only keyframes load (the rest fail); frame 6 is wanted, so 8 is the nearest."""

    def block_non_keyframes(route):
        index = frame_index(route.request.url)
        if index is not None and index % KEYFRAME_STEP:
            route.abort()
        else:
            route.continue_()

    page.route("**/frames/*.webp", block_non_keyframes)
    page.goto(site_url)
    wait_until(page, f"c.dataset.loaded === '{len(KEYFRAMES)}'", "the keyframes to load")
    scroll_to(page, 6 / (COUNT - 1))
    wait_for_frame(page, 8)


def test_canvas_matches_device_pixel_ratio(browser, site_url: str):
    """Spec 7: canvas pixels = CSS size x devicePixelRatio, updated on resize."""
    context = browser.new_context(device_scale_factor=2, viewport={"width": 800, "height": 600})
    page = context.new_page()
    try:
        page.goto(site_url)
        wait_for_frame(page, 0)

        def sizes():
            return page.evaluate(
                """() => {
                    const c = document.getElementById('turntable');
                    const r = c.getBoundingClientRect();
                    return [c.width, c.height, r.width, r.height];
                }"""
            )

        width, height, css_width, css_height = sizes()
        assert abs(width - css_width * 2) <= 1 and abs(height - css_height * 2) <= 1, sizes()

        page.set_viewport_size({"width": 1000, "height": 700})
        wait_until(page, "c.width === 2000", "the canvas to resize to 2000 px wide")
        width, height, css_width, css_height = sizes()
        assert abs(height - css_height * 2) <= 1, sizes()
    finally:
        context.close()


def test_reduced_motion_keeps_first_frame(page: Page, site_url: str):
    """Spec 9: with prefers-reduced-motion, scrolling doesn't change the frame."""
    page.emulate_media(reduced_motion="reduce")
    page.goto(site_url)
    wait_for_frame(page, 0)
    scroll_to(page, 1.0)
    page.wait_for_timeout(600)
    assert page.get_attribute("#turntable", "data-frame") == "0", state(page)


def test_no_console_errors(page: Page, site_url: str):
    """Spec 10."""
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(site_url)
    wait_all_loaded(page)
    scroll_to(page, 0.5)
    page.wait_for_timeout(300)
    assert errors == []
