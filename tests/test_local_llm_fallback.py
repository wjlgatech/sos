"""Tests for local_llm_fallback — cloud→local failover classification + routing.

The classification + routing logic runs offline (no Ollama needed). One opt-in live test
exercises a real local model when Ollama is up (skipped otherwise).
"""

import contextlib
import urllib.error

import pytest

from local_llm_fallback import (
    FallbackStats,
    OllamaConfig,
    is_availability_error,
    model_available,
    with_local_fallback,
)


class _Status:
    """Fake provider exception carrying a status_code (duck-typed like real SDK errors)."""

    def __init__(self, status_code: int, msg: str = "") -> None:
        self.status_code = status_code
        self._msg = msg

    def __str__(self) -> str:
        return self._msg


class TestAvailabilityClassification:
    def test_429_is_availability(self):
        assert is_availability_error(Exception("429 rate limit")) is True

    def test_credit_message_is_availability(self):
        assert is_availability_error(ValueError("Your credit balance is too low")) is True

    def test_status_code_attr_is_availability(self):
        # status_code attribute is read even when the message is empty
        class RateLimitError(Exception):
            status_code = 402

        assert is_availability_error(RateLimitError()) is True

    def test_connection_error_name_is_availability(self):
        class APIConnectionError(Exception):
            pass

        assert is_availability_error(APIConnectionError("boom")) is True

    def test_client_bug_is_NOT_availability(self):
        # A 400 bad-request (our bug) must re-raise, not silently fall back.
        assert is_availability_error(_Status(400, "invalid request: bad field")) is False

    def test_value_error_is_NOT_availability(self):
        assert is_availability_error(ValueError("you passed a None")) is False


class TestRouting:
    def test_primary_success_skips_fallback(self):
        def primary(messages, system, max_tokens):
            return "cloud answer"

        out = with_local_fallback(primary, messages=[{"role": "user", "content": "hi"}])
        assert out == "cloud answer"

    def test_non_availability_error_reraises(self):
        def primary(messages, system, max_tokens):
            raise ValueError("client bug")

        with pytest.raises(ValueError, match="client bug"):
            with_local_fallback(primary, messages=[{"role": "user", "content": "hi"}])

    def test_availability_error_routes_to_local(self):
        stats = FallbackStats()

        class ServiceUnavailable(Exception):
            status_code = 503  # real SDK errors carry the status as an attribute

        def primary(messages, system, max_tokens):
            raise ServiceUnavailable("upstream down")

        # Inject a fake local call by monkeypatching is unnecessary — use should_fallback +
        # a primary that fails, and a custom ollama call via a stub module function.
        # Here we verify stats are recorded and the local path is attempted (it raises
        # URLError if Ollama is down, which proves we routed to it).
        with contextlib.suppress(urllib.error.URLError, OSError):
            with_local_fallback(
                primary,
                messages=[{"role": "user", "content": "hi"}],
                ollama=OllamaConfig(base_url="http://127.0.0.1:9/v1"),  # dead → URLError
                stats=stats,
            )
        assert stats.count == 1
        assert stats.last_error == "ServiceUnavailable"

    def test_stats_active_window(self):
        stats = FallbackStats()
        assert stats.active() is False
        stats.record("X", "qwen2.5:7b")
        assert stats.active() is True
        assert stats.active(window_s=0) is False  # expired immediately


@pytest.mark.skipif(not model_available(), reason="Ollama not running or backup model not pulled")
def test_live_local_model_answers():
    """Opt-in: a real local model actually answers when the cloud 'fails'."""

    def primary(messages, system, max_tokens):
        raise Exception("429 overloaded")

    out = with_local_fallback(
        primary,
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        system="You are terse.",
        max_tokens=16,
    )
    assert out.strip()  # got a non-empty local answer
