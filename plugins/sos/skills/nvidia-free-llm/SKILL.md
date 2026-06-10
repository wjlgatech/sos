---
name: nvidia-free-llm
description: "Use NVIDIA's free NIM API (integrate.api.nvidia.com) — 120 hosted frontier models (GLM 5.1, Kimi K2.6, DeepSeek-v4, MiniMax M2.7, GPT-OSS-120B, Nemotron-3 Ultra, Qwen3 coder…) behind ONE OpenAI-compatible endpoint, free with a build.nvidia.com key (40 req/min, ~1 year). Use when an agent or app needs a free/cheap cloud LLM backend: out of credits, avoiding $50-200/mo API bills, wiring Hermes/Cursor/OpenCode/DreamMakeTrue to a no-cost provider, or wanting frontier-class quality without paying. Triggers on 'free LLM API', 'NVIDIA NIM / build.nvidia.com', 'out of credits', 'free GLM/Kimi/DeepSeek', 'point my agent at a free model'. NOT for production SLAs (rate-limited free tier) and NOT a local/offline option (that's Ollama — see freellmapi for the multi-provider aggregator)."
argument-hint: "[what you want — e.g. 'set up the key', 'wire DreamMakeTrue to it', 'which model for code?']"
allowed-tools: Bash, Read, Write, WebFetch
metadata:
  type: integration
  portable: true
  cross-agent: true
  source: "https://build.nvidia.com/models"
---

# Skill: NVIDIA free NIM API — 120 frontier models, one free OpenAI-compatible endpoint

NVIDIA hosts **120 models** (verified live 2026-06-10 via the public `/v1/models` — no key
needed to list) behind one OpenAI-compatible API, free with a registered key:

```
base_url: https://integrate.api.nvidia.com/v1
api_key:  nvapi-…            (free: build.nvidia.com/models → register → bind phone → copy)
limits:   ~40 req/min, key valid ~1 year (per NVIDIA's developer tier; re-verify on signup)
```

**Why care:** anyone paying for API access for agent experiments can point the same
OpenAI-compatible client here for $0. The catch: rate-limited, no SLA, and model ids churn —
**always verify ids against the live catalog** (this skill's probe does it in one command).

## Verified model ids (the viral post got two WRONG)

| Role             | Model id (✓ = verified live)            | Note                               |
| ---------------- | --------------------------------------- | ---------------------------------- |
| chat flagship    | `z-ai/glm-5.1` ✓                        | post said `zhipuai/glm-5.1` ✗      |
| agentic          | `moonshotai/kimi-k2.6` ✓                | post said `moonshot-ai/kimi-2.5` ✗ |
| chat fast        | `deepseek-ai/deepseek-v4-flash` ✓       | also `deepseek-v4-pro`             |
| long context     | `minimaxai/minimax-m2.7` ✓              |                                    |
| code             | `qwen/qwen3-coder-480b-a35b-instruct` ✓ |                                    |
| reasoning (huge) | `nvidia/nemotron-3-ultra-550b-a55b` ✓   |                                    |
| open weights     | `openai/gpt-oss-120b` ✓                 | and `gpt-oss-20b`                  |

```bash
NIM=~/.claude/skills/nvidia-free-llm/scripts/nim.py
python3 $NIM list kimi        # live catalog, filtered (no key needed)
python3 $NIM pick             # recommended id per role
NVIDIA_API_KEY=nvapi-… python3 $NIM test z-ai/glm-5.1   # one tiny completion → ok/latency
```

## Wire it into…

**DreamMakeTrue** (best fit: the cheap/fast tier — keeps Anthropic/quality where it matters):
Settings ⚙ → Model Provider → the **NVIDIA (free)** preset (or Custom) → paste key → Save.
Or deploy-time in `apps/api/.env`:

```
CHEAP_BASE_URL=https://integrate.api.nvidia.com/v1
CHEAP_API_KEY=nvapi-…
MODEL_CHEAP=deepseek-ai/deepseek-v4-flash
```

**Hermes:** Settings → Model Provider → Custom → base_url + key as above (Hermes speaks
OpenAI shape natively). **Cursor / OpenCode:** same two fields in their model settings.
**Any OpenAI SDK:** `OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key="nvapi-…")`.

## Agent guidance

- **Verify before you wire:** model ids churn — `nim.py list <family>` first, never trust a
  blog post's ids (two of the viral post's five were wrong on arrival).
- **Respect the 40 req/min:** fine for chat/agent turns; do NOT point a 6-agent parallel
  research fan-out at it without throttling.
- **It's a free tier, not infrastructure:** keep a fallback (local Ollama / paid key) wired —
  the pattern in DreamMakeTrue's `llm.py` (`_OllamaFallbackClient`) and this repo's
  `local_llm_fallback`.
- Pairs with **freellmapi** (the multi-provider free-tier aggregator): NIM becomes one more
  upstream there if you want failover across free providers.

## Cross-agent install (once per machine)

```bash
git clone https://github.com/wjlgatech/sos.git && cd sos
bash plugins/sos/scripts/install-skills-global.sh   # → ~/.claude/skills + ~/.hermes/skills + Codex AGENTS.md
```
