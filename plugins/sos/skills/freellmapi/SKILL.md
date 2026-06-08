---
name: freellmapi
description: "Stand up and use FreeLLMAPI — a self-hosted proxy that aggregates the free tiers of 16 LLM providers (Gemini, Groq, Cerebras, Mistral, OpenRouter, GitHub Models, Cloudflare, Cohere, NVIDIA, HuggingFace, Ollama Cloud, and more) behind ONE OpenAI-compatible endpoint with automatic failover. Use when you need a free/unified LLM backend, are rate-limited or out of API credits, want one base_url + key instead of juggling provider SDKs, or want a fallback brain for any OpenAI-compatible agent (Claude Code, Hermes, Codex, OpenClaw). Triggers on 'free LLM api', 'I'm out of credits / rate limited', 'unified LLM endpoint', 'set up freellmapi', 'cheap/free model backend', 'OpenAI-compatible proxy'. NOT for production traffic — it is explicitly personal-experimentation scope."
argument-hint: "[what you want — e.g. 'set it up', 'point my agent at it', 'test the endpoint']"
allowed-tools: Read, Write, Edit, Bash(docker *), Bash(curl *), Bash(npm *), Bash(bash *), Bash(openssl *), WebFetch
metadata:
  type: integration
  portable: true
  cross-agent: true
  source: "https://github.com/tashfeenahmed/freellmapi"
---

# Skill: FreeLLMAPI — one free, unified, OpenAI-compatible LLM backend

FreeLLMAPI (https://github.com/tashfeenahmed/freellmapi) is a self-hosted proxy that pools the
**free tiers of 16 providers** into a single **OpenAI-compatible** endpoint
(`/v1/chat/completions`, `/v1/embeddings`) with **automatic failover**, per-key rate-limit
tracking (RPM/RPD/TPM/TPD), encrypted key storage (AES-256-GCM), and a `model: "auto"` router.
You bring the providers' free keys once; every agent then talks to **one `base_url` + one key**.

The win for an agent fleet: any tool that speaks the OpenAI API — Claude Code (via the Agent
SDK / OpenAI-compatible mode), **Hermes**, Codex, OpenClaw — can use the *same* free backend by
setting two env vars. It's the natural companion to this repo's `local_llm_fallback` theme:
a free brain that survives credit exhaustion.

> ⚠️ **Scope:** the project states it's for *personal experimentation and learning, not
> production*. You remain bound by each upstream provider's Terms of Service. Don't point
> production traffic at it; expect variable latency and intelligence that degrades as daily
> free caps exhaust (the fallback chain activates).

## When to use
- You're rate-limited or out of credits and want to keep working for free.
- You want **one** `base_url`/key for many agents instead of N provider SDKs + N keys.
- You want a cheap/free default brain or a fallback for an OpenAI-compatible agent.
- You're experimenting and want vision / tool-calling / embeddings across providers uniformly.

Do **not** use it for production, image generation, audio, moderation, or legacy completions
(unsupported), or where stable latency/quality matters.

## Procedure — stand it up

1. **Run the proxy** (Docker is the recommended path):
   ```bash
   curl -fsSL https://tashfeenahmed.github.io/freellmapi/install.sh | bash
   ```
   Or pin it yourself (review before running anything piped to a shell):
   ```bash
   git clone https://github.com/tashfeenahmed/freellmapi.git && cd freellmapi
   ENCRYPTION_KEY="$(openssl rand -hex 32)"
   printf 'ENCRYPTION_KEY=%s\nPORT=3001\n' "$ENCRYPTION_KEY" > .env
   docker compose up -d
   ```
   The bundled `scripts/freellmapi.sh up` wraps this and waits for health.

2. **Add provider keys** in the dashboard at `http://localhost:3001` — paste the free keys you
   have (Gemini, Groq, Cerebras, Mistral, OpenRouter, GitHub Models, …). Keys are stored
   encrypted. The more you add, the longer before caps exhaust (~1.7B tokens/mo aggregate).

3. **Grab your unified key** from the dashboard (looks like `freellmapi-...`). This single
   bearer token is what every client uses.

4. **Verify** the endpoint is live: `bash scripts/freellmapi.sh status` (or the curl in
   "Test" below). Healthy keys show as `healthy`; exhausted ones flip to `rate_limited`.

## Point an agent at it (the cross-agent core)

Anything OpenAI-compatible needs just two values:

```
base_url = http://localhost:3001/v1      # or http://<host-ip>:3001/v1 across machines
api_key  = freellmapi-your-unified-key
model    = auto                          # let the proxy route + failover
```

| Agent / client | How to point it |
| --- | --- |
| **OpenAI SDK** (Python/JS) | `OpenAI(base_url="http://localhost:3001/v1", api_key="freellmapi-…")` |
| **Hermes / Codex / OpenClaw / any OpenAI-compatible agent** | set `OPENAI_BASE_URL=http://localhost:3001/v1` and `OPENAI_API_KEY=freellmapi-…` in its env/config |
| **Claude Code** | use it where an OpenAI-compatible base is accepted (Agent SDK / gateway); for native Anthropic calls keep your key — use FreeLLMAPI as the *fallback* brain |
| **curl / scripts** | `-H "Authorization: Bearer freellmapi-…"` to `…/v1/chat/completions` |

**Across computers:** start the proxy with `HOST_BIND=0.0.0.0` and point remote agents at
`http://<host-ip>:3001/v1`. Treat the unified key like any secret (LAN/VPN only — it's
single-user, no multi-tenant auth).

## Usage examples

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:3001/v1", api_key="freellmapi-your-unified-key")

# chat
resp = client.chat.completions.create(model="auto",
    messages=[{"role": "user", "content": "Summarize quantum tunneling in two lines."}])

# streaming
stream = client.chat.completions.create(model="auto", stream=True,
    messages=[{"role": "user", "content": "..."}])
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)

# vision
client.chat.completions.create(model="auto", messages=[{"role": "user", "content": [
    {"type": "text", "text": "What's in this image?"},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}]}])

# tools — standard OpenAI `tools` / `tool_choice`, multi-turn supported
# embeddings
client.embeddings.create(model="auto", input=["the quick brown fox"])
```

```bash
curl http://localhost:3001/v1/chat/completions \
  -H "Authorization: Bearer freellmapi-your-unified-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"hi"}]}'
```

## Key environment variables
- `ENCRYPTION_KEY` (**required**) — AES-256-GCM key for stored credentials (`openssl rand -hex 32`).
- `PORT` (default `3001`), `HOST_BIND` (default `127.0.0.1`; set `0.0.0.0` for LAN).
- `REQUEST_ANALYTICS_RETENTION_DAYS` (90), `REQUEST_ANALYTICS_MAX_ROWS` (100000), `DEV_MODE`.

## Make this skill global & cross-machine

This `SKILL.md` is plain Markdown — portable to any harness. Two distribution paths:

- **Claude Code, any machine:** install via this repo's marketplace —
  `/plugin marketplace add wjlgatech/sos` then `/plugin install sos@wjlgatech-plugins`
  → `/sos:freellmapi` is available in every project on that machine. Re-run on each computer.
- **Hermes (and other harnesses), any machine:** clone this repo once, then run
  `bash plugins/sos/scripts/install-skills-global.sh` — it symlinks the sos skills into Claude
  Code's (`~/.claude/skills`) and Hermes's (`$HERMES_SKILLS_DIR`) global skill directories, so
  both agents discover `freellmapi` everywhere. See that script's header for the dir overrides.

## Anti-patterns
1. **Production use.** It's experimentation-scope; one provider ToS change can break it. Don't
   build anything load-bearing on it.
2. **Exposing the endpoint publicly.** Single-user, no real auth — `0.0.0.0` belongs on a
   trusted LAN/VPN, never the open internet.
3. **Piping `install.sh | bash` blind.** Read it first (or use the pinned `git clone` path).
4. **Expecting frontier quality at 100% uptime.** As free caps exhaust, the router falls back to
   weaker models and latency wanders. Fine for iteration, not for a graded eval.
5. **Hardcoding a single provider model.** Use `model: "auto"` so failover actually works;
   pinning one model defeats the pooling.

## Where this fits
A free, unified backend for an agent fleet — the same "survive without paid credits" goal as
this repo's `local_llm_fallback`, but pooling *many* free cloud tiers instead of a local model.
Point Claude Code, Hermes, Codex, and OpenClaw at one `base_url` and they all share it.
