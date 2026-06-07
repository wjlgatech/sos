"""Local LLM fallback — keep working when the cloud brain goes dark.

Cloud LLMs fail: credits deplete, keys rate-limit, the network drops, a region 500s. This
module makes any cloud LLM call *survivable* by transparently retrying it against a local
[Ollama](https://ollama.com) model when — and only when — the failure is an availability
problem (not a bug in your request).

Zero external packages (stdlib `urllib`), matching the SOS ethos. Provider-agnostic: you
supply a `primary_call` for whatever cloud SDK you use; the fallback speaks Ollama's
OpenAI-compatible `/v1/chat/completions`.

Usage:

    from local_llm_fallback import with_local_fallback, OllamaConfig

    def cloud_call(messages, system, max_tokens):
        # ... your Anthropic/OpenAI/whatever call; raise on failure ...
        return text

    answer = with_local_fallback(
        cloud_call,
        messages=[{"role": "user", "content": "hi"}],
        system="Be terse.",
        max_tokens=256,
        ollama=OllamaConfig(model="qwen2.5:7b"),
    )

Reference implementation in a real app (Anthropic SDK → Ollama, returning an
Anthropic-shaped response so call sites need no change): DreamMakeTrue `apps/api/src/llm.py`
(`_OllamaFallbackClient`).
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Status codes that mean "the provider is unavailable / over quota", not "you sent garbage".
_AVAILABILITY_STATUS = {401, 402, 403, 408, 409, 429, 500, 502, 503, 504, 529}
# Substrings in an error message that signal an availability problem.
_AVAILABILITY_HINTS = ("credit", "quota", "insufficient", "overloaded", "rate limit", "timed out")


@dataclass
class OllamaConfig:
    """Where the local backup brain lives."""

    model: str = "qwen2.5:7b"
    base_url: str = "http://localhost:11434/v1"  # Ollama's OpenAI-compatible endpoint
    timeout: float = 300.0


@dataclass
class FallbackStats:
    """Mutable record of failovers, so a /status endpoint can show when you're on backup."""

    count: int = 0
    last_ts: float = 0.0
    last_error: str = ""
    last_model: str = ""

    def record(self, error: str, model: str) -> None:
        self.count += 1
        self.last_ts = time.time()
        self.last_error = error
        self.last_model = model

    def active(self, window_s: float = 300.0) -> bool:
        """True if a failover happened recently (i.e. you're currently leaning on local)."""
        return bool(self.last_ts) and (time.time() - self.last_ts < window_s)


# Process-wide default stats; pass your own to isolate per-tier counters.
STATS = FallbackStats()


def is_availability_error(exc: BaseException) -> bool:
    """Worth retrying locally? True for outages/quota/rate limits; False for client bugs.

    Works across SDKs by duck-typing: checks a `status_code`/`status` attribute and the
    message text, so you don't have to import any particular provider's exception classes.
    """
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if isinstance(status, int) and status in _AVAILABILITY_STATUS:
        return True
    name = type(exc).__name__.lower()
    if any(k in name for k in ("connection", "timeout", "ratelimit", "apiconnection")):
        return True
    msg = str(exc).lower()
    return any(k in msg for k in _AVAILABILITY_HINTS)


def ollama_chat(
    messages: list[dict[str, Any]],
    system: str = "",
    max_tokens: int = 1024,
    *,
    ollama: OllamaConfig | None = None,
) -> str:
    """Call a local Ollama model via its OpenAI-compatible endpoint. Stdlib only.

    `messages` are OpenAI-style ({"role", "content"}). Non-string content (e.g. image
    blocks) is coerced to its text parts — local backup models are usually not multimodal.
    """
    cfg = ollama or OllamaConfig()
    chat: list[dict[str, str]] = []
    if system:
        chat.append({"role": "system", "content": system})
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):  # OpenAI/Anthropic block lists → join text parts
            content = "\n".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("text")
            )
        chat.append({"role": m.get("role", "user"), "content": str(content)})

    payload = json.dumps(
        {"model": cfg.model, "messages": chat, "max_tokens": max_tokens, "stream": False}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{cfg.base_url.rstrip('/')}/chat/completions",
        data=payload,
        headers={"content-type": "application/json", "authorization": "Bearer ollama"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=cfg.timeout) as resp:  # noqa: S310 — localhost
        data = json.loads(resp.read().decode("utf-8"))
    return ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "") or ""


def with_local_fallback(
    primary_call: Callable[..., str],
    *,
    messages: list[dict[str, Any]],
    system: str = "",
    max_tokens: int = 1024,
    ollama: OllamaConfig | None = None,
    stats: FallbackStats | None = None,
    should_fallback: Callable[[BaseException], bool] = is_availability_error,
) -> str:
    """Run `primary_call(messages=, system=, max_tokens=)`; on an availability failure,
    retry the SAME request against a local Ollama model and return its text.

    Re-raises non-availability errors (your bug, not an outage) untouched.
    """
    try:
        return primary_call(messages=messages, system=system, max_tokens=max_tokens)
    except BaseException as exc:  # noqa: BLE001 — classify, then fall back or re-raise
        if not should_fallback(exc):
            raise
        cfg = ollama or OllamaConfig()
        (stats or STATS).record(type(exc).__name__, cfg.model)
        logger.warning(
            "cloud LLM failed (%s) — falling back to local %s", type(exc).__name__, cfg.model
        )
        return ollama_chat(messages, system=system, max_tokens=max_tokens, ollama=cfg)


def model_available(ollama: OllamaConfig | None = None) -> bool:
    """Is the configured backup model actually pulled and Ollama reachable? (for /status)."""
    cfg = ollama or OllamaConfig()
    base = cfg.base_url.rsplit("/v1", 1)[0]
    want = cfg.model.split(":")[0]
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=4.0) as r:  # noqa: S310
            models = [m.get("name", "") for m in json.loads(r.read()).get("models", [])]
        return any(want in m for m in models)
    except (urllib.error.URLError, OSError, ValueError):
        return False
