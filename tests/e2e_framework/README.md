# E2E Testing Framework

A thin, generic layer over Playwright for testing any webapp.
Tests describe **user journeys**, not implementation details.
Output is structured so both humans and AI agents (Claude Code, OpenClaw) can read failures and act.

---

## Install

```bash
make e2e-install
# or manually:
pip install pytest-playwright
playwright install chromium
```

---

## Run

```bash
make e2e                            # headless (CI)
make e2e-headed                     # watch the browser (debug)
pytest tests/e2e/ -k "creator"      # one journey by name
pytest tests/e2e/ --headed -x       # stop on first failure, visible
```

---

## Output — what you see

Every primitive prints structured lines so you can follow exactly what happened:

```
  [E2E] add_creator: filled '#add-name' = 'Alice'
  [E2E] add_creator: filled '#add-email' = 'alice@example.com'
  [E2E] add_creator: clicked '#btn-submit'
  [E2E] add_creator: success text appeared ok
  [E2E] add_creator: all fields cleared ok
```

On failure, you get the exact problem + a screenshot path:

```
[E2E FAIL] add_creator
  Field '#add-name' not cleared after submit — still contains: 'Alice'
  Screenshot: /tmp/e2e_add_creator.png
```

**For AI agents (Claude Code, OpenClaw):**
- Search for `[E2E FAIL]` in output — that's the failure summary
- The line after it is the exact cause
- The `Screenshot:` line gives you the image path to read with the Read tool
- All `[E2E]` prefixed lines are the step trace leading up to the failure

---

## Primitives

### `assert_button_cycle` — async trigger buttons

Tests the full lifecycle: click → disables → work happens → re-enables.

Catches:
- Buttons that never disable (double-submit risk)
- Buttons that lock permanently (broken error handler)

```python
from tests.e2e.framework import assert_button_cycle

assert_button_cycle(
    page,
    button="#btn-submit-order",
    label="submit_order",
    expect_disabled_ms=2000,    # must disable within 2s
    expect_reenabled_ms=30000,  # must re-enable within 30s
)
```

---

### `assert_form_clears` — form submission happy path

Fills fields → clicks submit → waits for success text → verifies fields cleared.

Catches:
- Submit that doesn't show success
- Fields that keep stale values after submission

```python
from tests.e2e.framework import assert_form_clears

assert_form_clears(
    page,
    fields={
        "#name":  "Alice",
        "#email": "alice@example.com",
    },
    submit="#btn-add-user",
    success_selector="#status-message",
    success_text="✅ User added",
    label="add_user",
    timeout_ms=10000,
)
```

---

### `assert_toggle_pair` — show/hide toggles

Clicks a trigger, asserts one element becomes visible and another hidden.
Uses the HTML `hidden` attribute (standard for JS dashboards).

```python
from tests.e2e.framework import assert_toggle_pair

assert_toggle_pair(
    page,
    trigger="#btn-advanced-view",
    shows="advanced-panel",   # element ID (no #)
    hides="simple-panel",
    label="advanced_toggle",
)
```

---

### `assert_layer_tabs` — tabbed panels

Cycles through all tabs, verifying exactly one layer is active at a time.
Works for any `tab-{n}` / `layer-{n}` ID pattern.

```python
from tests.e2e.framework import assert_layer_tabs

assert_layer_tabs(
    page,
    tab_pattern="tab-{n}",       # IDs: tab-1, tab-2, tab-3
    layer_pattern="panel-{n}",   # IDs: panel-1, panel-2, panel-3
    count=3,
    label="settings_tabs",
)
```

---

### `assert_live_update` — auto-refresh

Waits N seconds, asserts an element's text changed.
For: status timestamps, live counters, polling indicators.

```python
from tests.e2e.framework import assert_live_update

assert_live_update(
    page,
    selector="#last-sync-time",
    wait_seconds=15,
    label="sync_timestamp",
)
```

---

### `poll_api_job` — async job polling

Polls a REST job endpoint until it reaches a terminal state.
Works with any API that follows the `trigger → poll` pattern.

```python
from tests.e2e.framework import poll_api_job
import requests

resp = requests.post(f"{BASE}/api/jobs/run", json={"task": "process"})
job = poll_api_job(
    BASE,
    resp.json()["job_id"],
    jobs_endpoint="/api/jobs/{job_id}",   # default: /api/pipeline/jobs/{job_id}
    timeout_s=60,
    on_tick=lambda j: print(f"  status: {j['status']}"),
)
assert job["status"] == "done"
```

---

### `trigger_and_poll` — one-liner for trigger + poll

POST to trigger, extract job_id, poll to completion — in one call.

```python
from tests.e2e.framework import trigger_and_poll

job = trigger_and_poll(
    BASE,
    trigger_endpoint="/api/pipeline/run",
    trigger_body={"step": "ingest"},
    timeout_s=120,
)
assert job["status"] == "done"
```

---

### `capture_console` — JS error capture

Context manager. Captures browser console errors. Optionally fails the test if any occur.

```python
from tests.e2e.framework import capture_console

with capture_console(page, fail_on_error=True):
    page.goto(url)
    page.locator("#submit").click()
# Any JS error → test fails with the error message + screenshot
```

---

### `screenshot_on_failure` — auto-screenshot

Context manager. Saves a screenshot if the wrapped block raises.
Saved to `/tmp/e2e_{label}.png`.

```python
from tests.e2e.framework import screenshot_on_failure

def test_checkout(page):
    with screenshot_on_failure(page, "checkout"):
        page.locator("#pay-now").click()
        expect(page.locator("#confirmation")).to_be_visible()
# On failure: /tmp/e2e_checkout.png is saved automatically
```

---

## Writing a new test suite for a different project

**1. Copy the framework** (3 files, no dependencies beyond playwright):

```
your-project/tests/e2e/framework/
  __init__.py
  assertions.py
  api.py
  fixtures.py
```

**2. Write a conftest.py**:

```python
# tests/e2e/conftest.py
import pytest
from playwright.sync_api import Page

BASE = "http://localhost:8080"  # your app

@pytest.fixture(autouse=True)
def go_home(page: Page):
    page.goto(BASE, wait_until="networkidle")
```

**3. Write journeys** (one function = one user scenario):

```python
# tests/e2e/test_myapp.py
from tests.e2e.framework import assert_button_cycle, assert_form_clears

def test_create_item(page):
    assert_form_clears(
        page,
        fields={"#item-name": "Widget", "#item-qty": "5"},
        submit="#btn-create",
        success_selector="#toast",
        success_text="Created",
        label="create_item",
    )

def test_delete_item(page):
    assert_button_cycle(page, button="#btn-delete-first", label="delete_item")
```

**4. Run**:

```bash
pytest tests/e2e/ --headed --base-url http://localhost:8080
```

---

## For AI agents (Claude Code, OpenClaw)

When running E2E tests on a webapp, follow this protocol:

### Step 1 — Start the server
```bash
# Start the app server first (must be running before tests)
make serve   # or: uvicorn app:server --port 8080
```

### Step 2 — Run tests
```bash
pytest tests/e2e/ --base-url http://localhost:PORT -v 2>&1 | tee /tmp/e2e_output.txt
```

### Step 3 — Parse failures
```bash
grep "\[E2E FAIL\]" /tmp/e2e_output.txt     # failure summaries
grep "Screenshot:" /tmp/e2e_output.txt       # screenshot paths
```

### Step 4 — Read screenshots
Use the `Read` tool to view any screenshot paths reported in the output.
The image shows the browser state at the moment of failure.

### Step 5 — Fix and re-run
After fixing, re-run only the failing test:
```bash
pytest tests/e2e/ -k "test_name_that_failed" --headed --base-url http://localhost:PORT
```

### Pattern: adding a test for a new feature

When asked to "add E2E coverage for feature X":

1. Identify which primitive fits:
   - Button that triggers async work → `assert_button_cycle`
   - Form submission → `assert_form_clears`
   - Show/hide panel → `assert_toggle_pair`
   - Tab switching → `assert_layer_tabs`
   - Auto-updating text → `assert_live_update`
   - Background job → `poll_api_job` or `trigger_and_poll`

2. Write a function named `test_{what_the_user_does}` — not `test_{implementation}`

3. Wrap the body in `with screenshot_on_failure(page, "test_name"):`

4. Run `make e2e-headed` to verify visually before committing

---

## File structure

```
tests/e2e/
  framework/
    __init__.py       ← public API (import from here)
    assertions.py     ← UI behaviour primitives
    api.py            ← job polling primitives
    fixtures.py       ← pytest fixtures + context managers
    README.md         ← this file
  conftest.py         ← project-specific setup (base_url, page setup)
  test_dashboard.py   ← example: dashboard user journeys
```
