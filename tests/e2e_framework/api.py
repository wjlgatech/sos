"""
framework/api.py — Generic async job polling for any REST API.

poll_api_job() works with any backend that follows the pattern:
  POST /api/.../run  → {"job_id": "abc123"}
  GET  /api/.../jobs/{job_id} → {"status": "running"|"done"|"error", ...}
"""

from __future__ import annotations

import time
from typing import Callable

import requests


def poll_api_job(
    base_url: str,
    job_id: str,
    *,
    jobs_endpoint: str = "/api/pipeline/jobs/{job_id}",
    terminal_states: tuple[str, ...] = ("done", "error"),
    timeout_s: int = 120,
    poll_interval_s: float = 1.0,
    on_tick: Callable[[dict], None] | None = None,
) -> dict:
    """
    Poll a job endpoint until it reaches a terminal state.

    Works with any API where jobs follow the run→poll pattern.

    Args:
        base_url:        e.g. "http://localhost:7331"
        job_id:          The job ID returned by the trigger endpoint.
        jobs_endpoint:   URL template with {job_id}. Default: /api/pipeline/jobs/{job_id}
        terminal_states: States that mean "done, stop polling".
        timeout_s:       Give up after this many seconds.
        poll_interval_s: Seconds between polls.
        on_tick:         Optional callback(job_dict) called on each poll — use for
                         live progress display or early assertions.

    Returns:
        Final job dict (with status, output, error, etc.)

    Raises:
        TimeoutError: if job doesn't complete within timeout_s.
        AssertionError: with structured diagnosis if job ends in "error".

    Example:
        resp = requests.post(f"{BASE}/api/pipeline/run", json={"step": "ingest"})
        job = poll_api_job(BASE, resp.json()["job_id"])
        assert job["status"] == "done"

    Example with live tick:
        def show_progress(j):
            creators = [p["name"] for p in j.get("progress", [])]
            print(f"  running: {creators}")

        job = poll_api_job(BASE, job_id, on_tick=show_progress)
    """
    url = base_url.rstrip("/") + jobs_endpoint.format(job_id=job_id)
    deadline = time.time() + timeout_s
    last_status = "unknown"

    print(f"  [E2E] poll_api_job: {url}")

    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            job = resp.json()
        except Exception as e:
            print(f"  [E2E] poll_api_job: fetch error — {e}")
            time.sleep(poll_interval_s)
            continue

        last_status = job.get("status", "unknown")

        if on_tick:
            on_tick(job)

        if last_status in terminal_states:
            _print_job_summary(job)
            return job

        time.sleep(poll_interval_s)

    raise TimeoutError(
        f"\n[E2E FAIL] poll_api_job timed out after {timeout_s}s\n"
        f"  URL: {url}\n"
        f"  Last status: {last_status}\n"
        f"  Increase timeout_s or check the server process."
    )


def trigger_and_poll(
    base_url: str,
    *,
    trigger_endpoint: str,
    trigger_body: dict,
    job_id_key: str = "job_id",
    jobs_endpoint: str = "/api/pipeline/jobs/{job_id}",
    timeout_s: int = 120,
    on_tick: Callable[[dict], None] | None = None,
) -> dict:
    """
    Convenience: POST to trigger endpoint, extract job_id, then poll to completion.

    Args:
        base_url:          e.g. "http://localhost:7331"
        trigger_endpoint:  e.g. "/api/pipeline/run"
        trigger_body:      JSON body for the trigger POST.
        job_id_key:        Key in trigger response that contains the job ID.
        jobs_endpoint:     Polling URL template.
        timeout_s:         Poll timeout.
        on_tick:           Optional progress callback.

    Returns:
        Final job dict.

    Example:
        job = trigger_and_poll(
            BASE,
            trigger_endpoint="/api/pipeline/run",
            trigger_body={"step": "ingest"},
        )
        assert job["status"] == "done"
    """
    url = base_url.rstrip("/") + trigger_endpoint
    resp = requests.post(url, json=trigger_body, timeout=15)
    resp.raise_for_status()
    job_id = resp.json()[job_id_key]
    print(f"  [E2E] trigger_and_poll: job_id={job_id!r} from {trigger_endpoint}")
    return poll_api_job(
        base_url, job_id,
        jobs_endpoint=jobs_endpoint,
        timeout_s=timeout_s,
        on_tick=on_tick,
    )


# ─── Internal ─────────────────────────────────────────────────────────────────

def _print_job_summary(job: dict) -> None:
    status = job.get("status", "?")
    icon = {"done": "✅", "error": "❌"}.get(status, "⏳")
    duration = ""
    if job.get("started") and job.get("finished"):
        from datetime import datetime
        try:
            s = datetime.fromisoformat(job["started"])
            f = datetime.fromisoformat(job["finished"])
            duration = f" ({(f - s).total_seconds():.1f}s)"
        except Exception:
            pass

    print(f"  [E2E] poll_api_job: {icon} {status}{duration}")

    if status == "error":
        lines = job.get("lines") or []
        err = job.get("error", "")
        # Show last 5 meaningful lines
        meaningful = [l for l in lines if l.strip() and "Traceback" not in l and "File " not in l]
        tail = meaningful[-5:] if meaningful else [err]
        for line in tail:
            print(f"    {line}")
    elif job.get("progress"):
        for p in job["progress"]:
            icon = {"done": "✅", "error": "❌", "running": "⚙️"}.get(p["status"], "⏳")
            print(f"    {icon} {p['name']}: {p['done']}/{p['total'] or '?'}")
