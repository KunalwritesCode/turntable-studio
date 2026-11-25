"""Shared Playwright test helpers for any page exposing the #turntable canvas hooks."""

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page


def state(page: Page) -> str:
    """Current test hooks, for readable failure messages."""
    attrs = page.evaluate(
        """() => {
            const c = document.getElementById('turntable');
            return {frame: c.dataset.frame, loaded: c.dataset.loaded};
        }"""
    )
    return f"data-frame={attrs['frame']!r}, data-loaded={attrs['loaded']!r}"


def wait_until(page: Page, js_condition: str, what: str, timeout: int = 3000) -> None:
    """Wait for a condition on the canvas `c`; fail with the player's state if it never holds."""
    try:
        page.wait_for_function(
            f"() => {{ const c = document.getElementById('turntable'); return {js_condition}; }}",
            timeout=timeout,
        )
    except PlaywrightError:
        pytest.fail(f"Timed out waiting for {what}. Player state: {state(page)}")


def wait_for_frame(page: Page, expected: int, tolerance: int = 0) -> None:
    wait_until(
        page,
        f"Math.abs(Number(c.dataset.frame) - {expected}) <= {tolerance}",
        f"data-frame within {tolerance} of {expected}",
    )


def scroll_to(page: Page, fraction: float) -> None:
    page.evaluate(
        "f => window.scrollTo(0, (document.documentElement.scrollHeight - innerHeight) * f)",
        fraction,
    )
