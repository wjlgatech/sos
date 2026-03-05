"""
framework/fixtures.py — Reusable pytest fixtures and context managers.

Drop these into any project's conftest.py:

    from tests.e2e.framework.fixtures import capture_console, screenshot_on_failure

Or use them directly as context managers inside tests.
"""

from __future__ import annotations

import contextlib
from pathlib import Path

import pytest
from playwright.sync_api import Page


@contextlib.contextmanager
def capture_console(page: Page, *, fail_on_error: bool = False):
    """
    Context manager that captures browser console output.
    Prints errors automatically. Optionally fails the test if any JS error occurs.

    Usage:
        with capture_console(page) as console:
            page.goto(url)
            do_something(page)
        # console.errors  → list of error messages
        # console.all     → list of all (type, text) tuples

    Args:
        page:           Playwright Page.
        fail_on_error:  If True, raises AssertionError if any console error is captured.

    Example:
        with capture_console(page, fail_on_error=True):
            page.goto("http://localhost:3000")
            page.locator("#submit").click()
    """
    class _Log:
        def __init__(self):
            self.errors: list[str] = []
            self.all: list[tuple[str, str]] = []

    log = _Log()

    def _on_msg(msg):
        log.all.append((msg.type, msg.text))
        if msg.type in ("error", "warning"):
            prefix = "ERROR" if msg.type == "error" else "WARN"
            print(f"  [browser {prefix}] {msg.text}")
            if msg.type == "error":
                log.errors.append(msg.text)

    def _on_pageerror(exc):
        msg = str(exc)
        log.errors.append(f"pageerror: {msg}")
        print(f"  [browser pageerror] {msg}")

    page.on("console", _on_msg)
    page.on("pageerror", _on_pageerror)

    try:
        yield log
    finally:
        page.remove_listener("console", _on_msg)
        page.remove_listener("pageerror", _on_pageerror)

        if fail_on_error and log.errors:
            path = Path("/tmp/e2e_console_error.png")
            try:
                page.screenshot(path=str(path))
            except Exception:
                pass
            raise AssertionError(
                f"\n[E2E FAIL] {len(log.errors)} browser console error(s) captured:\n"
                + "\n".join(f"  - {e}" for e in log.errors)
                + f"\n  Screenshot: {path}"
            )


@contextlib.contextmanager
def screenshot_on_failure(page: Page, label: str):
    """
    Context manager that saves a screenshot if the wrapped block raises.

    Usage:
        with screenshot_on_failure(page, "checkout_flow"):
            do_something_that_might_fail(page)
        # On failure: /tmp/e2e_checkout_flow.png is saved automatically.

    Args:
        page:  Playwright Page.
        label: Used in the filename: /tmp/e2e_{label}.png

    Example:
        def test_checkout(page):
            with screenshot_on_failure(page, "checkout"):
                page.locator("#pay-now").click()
                expect(page.locator("#confirmation")).to_be_visible()
    """
    try:
        yield
    except Exception:
        path = Path(f"/tmp/e2e_{label.replace(' ', '_')}.png")
        try:
            page.screenshot(path=str(path))
            print(f"\n  [E2E] Screenshot saved: {path}")
        except Exception as e:
            print(f"\n  [E2E] Screenshot failed: {e}")
        raise


# ─── Shared pytest fixtures ───────────────────────────────────────────────────
# Add these to your project's conftest.py by importing and re-exporting,
# or copy-paste — pytest discovers fixtures by name, not import path.

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Standard viewport for consistent rendering."""
    return {**browser_context_args, "viewport": {"width": 1280, "height": 900}}


@pytest.fixture
def page_ready(page: Page, base_url: str):
    """
    A page that has already loaded the app and waited for network idle.
    Replaces the common pattern of page.goto + wait_for_network_idle in every test.

    Also captures console errors — prints them but does not fail.

    Usage in test:
        def test_something(page_ready):
            page_ready.locator("#btn").click()
            ...
    """
    with capture_console(page):
        page.goto(base_url, wait_until="networkidle")
    return page
