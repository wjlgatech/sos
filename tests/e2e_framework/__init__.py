"""
E2E Testing Framework — generic, reusable across any webapp.

from tests.e2e.framework import (
    assert_button_cycle,
    assert_form_clears,
    assert_toggle_pair,
    assert_layer_tabs,
    assert_live_update,
    poll_api_job,
    capture_console,
    screenshot_on_failure,
)
"""

from .assertions import (
    assert_button_cycle,
    assert_form_clears,
    assert_toggle_pair,
    assert_layer_tabs,
    assert_live_update,
)
from .api import poll_api_job, trigger_and_poll
from .fixtures import capture_console, screenshot_on_failure

__all__ = [
    "assert_button_cycle",
    "assert_form_clears",
    "assert_toggle_pair",
    "assert_layer_tabs",
    "assert_live_update",
    "poll_api_job",
    "trigger_and_poll",
    "capture_console",
    "screenshot_on_failure",
]
