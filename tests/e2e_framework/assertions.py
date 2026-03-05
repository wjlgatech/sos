"""
framework/assertions.py — UI behaviour primitives.

Each function tests one reusable interaction pattern.
On failure: prints a structured diagnosis + saves a screenshot.

Design rules:
  1. Every function takes (page, ...) as first args — no hidden state.
  2. timeout_ms has a sane default; always overridable.
  3. Failure messages tell you WHAT was expected, WHAT was found, and WHERE to look.
  4. Screenshots saved to /tmp/e2e_{label}.png on every failure.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from playwright.sync_api import Page, expect


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _fail(page: Page, label: str, message: str) -> None:
    """Save a screenshot and raise AssertionError with a structured message."""
    path = Path(f"/tmp/e2e_{label.replace(' ', '_')}.png")
    try:
        page.screenshot(path=str(path))
        screenshot_hint = f"\n  Screenshot: {path}"
    except Exception:
        screenshot_hint = "\n  Screenshot: (could not capture)"

    raise AssertionError(
        f"\n[E2E FAIL] {label}"
        f"\n  {message}"
        f"{screenshot_hint}"
    )


def _text(page: Page, selector: str) -> str:
    return (page.locator(selector).text_content() or "").strip()


def _is_hidden(page: Page, element_id: str) -> bool:
    return page.evaluate(f"!!document.getElementById('{element_id}')?.hidden")


# ─── assert_button_cycle ──────────────────────────────────────────────────────

def assert_button_cycle(
    page: Page,
    *,
    button: str,
    label: str = "button_cycle",
    expect_disabled_ms: int = 2000,
    expect_reenabled_ms: int = 30000,
    on_click: Callable | None = None,
) -> None:
    """
    Assert the complete lifecycle of an async-trigger button:
      click → disables → (work happens) → re-enables

    Catches: buttons that never disable (double-submit risk),
             buttons that lock permanently (broken job handling).

    Args:
        page:               Playwright Page.
        button:             CSS selector for the button.
        label:              Name used in failure messages and screenshot filename.
        expect_disabled_ms: How long to wait for the button to disable (default 2s).
        expect_reenabled_ms: How long to wait for re-enable after job ends (default 30s).
        on_click:           Optional callable to run after click (e.g. to trigger the action
                            indirectly). If None, clicks `button` directly.

    Example:
        assert_button_cycle(page, button="#btn-submit", label="submit_order")
    """
    btn = page.locator(button)

    # 1. Click
    if on_click:
        on_click()
    else:
        btn.click()

    # 2. Must disable
    try:
        expect(btn).to_be_disabled(timeout=expect_disabled_ms)
    except AssertionError:
        _fail(page, label,
              f"Button '{button}' did not disable after click — double-submit risk.\n"
              f"  Current state: {'disabled' if btn.is_disabled() else 'still enabled'}")

    print(f"  [E2E] {label}: button disabled ok")

    # 3. Must re-enable
    try:
        expect(btn).not_to_be_disabled(timeout=expect_reenabled_ms)
    except AssertionError:
        _fail(page, label,
              f"Button '{button}' never re-enabled after {expect_reenabled_ms}ms — "
              f"job may be stuck or error handler is broken.")

    print(f"  [E2E] {label}: button re-enabled ok")


# ─── assert_form_clears ───────────────────────────────────────────────────────

def assert_form_clears(
    page: Page,
    *,
    fields: dict[str, str],
    submit: str,
    success_selector: str,
    success_text: str,
    label: str = "form_submit",
    timeout_ms: int = 30000,
) -> None:
    """
    Assert a form's full happy-path:
      fill fields → submit → success text appears → fields are cleared.

    Catches: submit buttons that don't clear the form, success messages that
             never appear, fields that keep stale values after submission.

    Args:
        page:             Playwright Page.
        fields:           {css_selector: value_to_fill}
        submit:           CSS selector for the submit button.
        success_selector: CSS selector for the element that shows success.
        success_text:     Text that must appear in success_selector after submit.
        label:            Name used in failure messages.
        timeout_ms:       How long to wait for success_text (default 30s).

    Example:
        assert_form_clears(
            page,
            fields={"#name": "Alice", "#email": "alice@example.com"},
            submit="#btn-submit",
            success_selector="#status",
            success_text="✅",
            label="add_user",
        )
    """
    # Fill
    for selector, value in fields.items():
        page.locator(selector).fill(value)
        print(f"  [E2E] {label}: filled {selector!r} = {value!r}")

    # Submit
    page.locator(submit).click()
    print(f"  [E2E] {label}: clicked {submit!r}")

    # Success must appear
    try:
        expect(page.locator(success_selector)).to_contain_text(
            success_text, timeout=timeout_ms
        )
    except AssertionError:
        actual = _text(page, success_selector)
        _fail(page, label,
              f"Success text {success_text!r} never appeared in '{success_selector}'.\n"
              f"  Actual text: {actual!r}")

    print(f"  [E2E] {label}: success text appeared ok")

    # Fields must clear
    for selector in fields:
        val = page.locator(selector).input_value()
        if val:
            _fail(page, label,
                  f"Field '{selector}' not cleared after submit — still contains: {val!r}")

    print(f"  [E2E] {label}: all fields cleared ok")


# ─── assert_toggle_pair ───────────────────────────────────────────────────────

def assert_toggle_pair(
    page: Page,
    *,
    trigger: str,
    shows: str,
    hides: str,
    label: str = "toggle",
    delay_ms: int = 300,
) -> None:
    """
    Assert a show/hide toggle: clicking trigger makes `shows` visible
    and `hides` hidden. Checks the HTML `hidden` attribute (standard for
    dashboards that use element.hidden = true).

    Args:
        page:     Playwright Page.
        trigger:  CSS selector for the clickable toggle.
        shows:    Element ID (no #) that should become visible.
        hides:    Element ID (no #) that should become hidden.
        label:    Name for failure messages.
        delay_ms: ms to wait after click before asserting (for CSS transitions).

    Example:
        assert_toggle_pair(page, trigger="#btn-advanced", shows="advanced-panel",
                           hides="simple-panel", label="advanced_toggle")
    """
    page.locator(trigger).click()
    page.wait_for_timeout(delay_ms)

    if _is_hidden(page, shows):
        _fail(page, label,
              f"Expected #{shows} to be visible after clicking '{trigger}', but it's hidden.")

    if not _is_hidden(page, hides):
        _fail(page, label,
              f"Expected #{hides} to be hidden after clicking '{trigger}', but it's visible.")

    print(f"  [E2E] {label}: #{shows} visible, #{hides} hidden — ok")


# ─── assert_layer_tabs ────────────────────────────────────────────────────────

def assert_layer_tabs(
    page: Page,
    *,
    tab_pattern: str,
    layer_pattern: str,
    count: int,
    label: str = "layer_tabs",
    delay_ms: int = 200,
) -> None:
    """
    Assert that a tabbed-layer UI correctly activates one layer at a time.

    Works for any pattern like: tab ids = "tab-l1","tab-l2",... and
    layer ids = "layer-1","layer-2",...

    Args:
        page:          Playwright Page.
        tab_pattern:   f-string pattern for tab IDs, e.g. "tab-l{n}"
        layer_pattern: f-string pattern for layer IDs, e.g. "layer-{n}"
        count:         Number of tabs.
        label:         Name for failure messages.
        delay_ms:      Wait after click.

    Example:
        assert_layer_tabs(page, tab_pattern="tab-l{n}", layer_pattern="layer-{n}",
                          count=4, label="technical_layers")
    """
    for n in range(1, count + 1):
        tab_id = tab_pattern.format(n=n)
        layer_id = layer_pattern.format(n=n)

        page.locator(f"#{tab_id}").click()
        page.wait_for_timeout(delay_ms)

        active_class = page.locator(f"#{layer_id}").get_attribute("class") or ""
        if "active" not in active_class:
            _fail(page, f"{label}_tab{n}",
                  f"#{layer_id} should have class 'active' after clicking #{tab_id}.\n"
                  f"  Actual class: {active_class!r}")

        # All others must NOT be active
        for other in range(1, count + 1):
            if other == n:
                continue
            other_id = layer_pattern.format(n=other)
            other_class = page.locator(f"#{other_id}").get_attribute("class") or ""
            if "active" in other_class and other_id != layer_id:
                _fail(page, f"{label}_tab{n}",
                      f"#{other_id} should not be active when #{layer_id} is selected.\n"
                      f"  Both have class 'active' — tab switching is broken.")

        print(f"  [E2E] {label}: tab {n}/{count} active ok")


# ─── assert_live_update ───────────────────────────────────────────────────────

def assert_live_update(
    page: Page,
    *,
    selector: str,
    wait_seconds: int = 12,
    label: str = "live_update",
) -> None:
    """
    Assert that an auto-refreshing element changes its text within wait_seconds.

    Useful for: status timestamps, live counters, polling indicators.

    Args:
        page:         Playwright Page.
        selector:     CSS selector for the element that should change.
        wait_seconds: How long to wait for the change.
        label:        Name for failure messages.

    Example:
        assert_live_update(page, selector="#last-update", wait_seconds=12,
                           label="auto_refresh_timestamp")
    """
    before = _text(page, selector)
    print(f"  [E2E] {label}: initial value = {before!r}")

    time.sleep(wait_seconds)

    after = _text(page, selector)
    if before == after:
        _fail(page, label,
              f"Element '{selector}' did not change after {wait_seconds}s.\n"
              f"  Value before: {before!r}\n"
              f"  Value after:  {after!r}\n"
              f"  Auto-refresh may be broken or the interval is > {wait_seconds}s.")

    print(f"  [E2E] {label}: updated {before!r} -> {after!r} ok")
