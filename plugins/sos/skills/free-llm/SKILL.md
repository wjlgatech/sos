---
name: free-llm
description: "Free LLMs for any agent, with a survival chain (formerly nvidia-free-llm). Primary: NVIDIA's free NIM API (integrate.api.nvidia.com) — 120 hosted frontier models (GLM 5.1, Kimi K2.6, DeepSeek-v4, MiniMax M2.7, GPT-OSS-120B…) behind ONE OpenAI-compatible endpoint, free with a build.nvidia.com key (40 req/min, ~1 year). PLUS the standing fallback-chain rule: NIM → local Ollama → OpenRouter → Anthropic/OpenAI, so an agent never dies when a free tier throttles. Use when an agent or app needs a free/cheap cloud LLM backend: out of credits, hit a 429/rate limit, avoiding $50-200/mo API bills, wiring Hermes/Cursor/OpenCode/DreamMakeTrue to a no-cost provider. Triggers on 'free LLM API', 'NVIDIA NIM / build.nvidia.com', 'out of credits', 'rate limited / 429', 'free GLM/Kimi/DeepSeek', 'point my agent at a free model', 'fallback chain'. NOT for production SLAs (rate-limited free tier); see freellmapi for the multi-provider aggregator."
argument-hint: "[what you want — e.g. 'set up the key', 'wire DreamMakeTrue to it', 'which model for code?']"
allowed-tools: Bash, Read, Write, WebFetch
metadata:
  type: integration
  portable: true
  cross-agent: true
  source: "https://build.nvidia.com/models"
---

# Skill: free-llm — free frontier LLMs + the fallback chain that keeps agents alive

*(formerly `nvidia-free-llm`)*

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
NIM=~/.claude/skills/free-llm/scripts/nim.py
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

**Hermes:** has a NATIVE `nvidia` provider (verified in `agent/models_dev.py` — env
`NVIDIA_API_KEY`, base URL pre-baked, 94 NIM models in its registry incl. `z-ai/glm-5.1`,
`moonshotai/kimi-k2.6`). So: add `NVIDIA_API_KEY=nvapi-…` to `~/.hermes/.env` (Desktop app:
`Env` tab → Set → Save), then `Config` tab → `model.provider: nvidia` + `model` id — no
Custom/base_url needed. **Cursor / OpenCode:** Custom provider → the two fields above.
**Any OpenAI SDK:** `OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key="nvapi-…")`.

## THE FALLBACK-CHAIN RULE (standing policy — activate whenever you wire a free LLM)

Free tiers die mid-conversation: NIM throttles at 40 req/min, OpenRouter keys run dry,
local daemons stop. **Any agent wired to NIM must also get this chain, in this order:**

```
1. NVIDIA NIM        (primary, $0, frontier-class)
2. local Ollama      (http://localhost:11434/v1 — $0, offline-proof, last-resort quality)
3. OpenRouter        (paid credits; cheap models)
4. Anthropic / OpenAI (paid API keys / ChatGPT-sub OAuth)
```

**Probe each tier before trusting it** (a chain of dead links is theater):
- NIM: `python3 $NIM test moonshotai/kimi-k2.6`
- Ollama: `curl -s localhost:11434/api/tags` → pick an INSTALLED model
- OpenRouter: `curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $OPENROUTER_API_KEY"`
  → if `total_usage >= total_credits` it will 402; wire it anyway, flag for top-up
- Anthropic/OpenAI: key exists + has balance

**Hermes** — the exact working config (verified live 2026-06-10), in `~/.hermes/config.yaml`:

```yaml
fallback_providers:
- provider: custom              # local Ollama — explicit base_url/api_key are honored
  model: qwen2.5:7b             # ← whatever `ollama list` shows on THIS machine
  base_url: http://localhost:11434/v1
  api_key: ollama
- provider: openrouter
  model: openai/gpt-5-mini
- provider: anthropic
  model: claude-sonnet-4-6
- provider: openai-codex        # the "OpenAI" leg — ChatGPT-sub OAuth, $0
  model: gpt-5.5
```

Hermes gotchas (hard-won): entries MUST be dicts with both `provider` and `model` (bare
strings are silently dropped, `agent_init.py`); the gateway loads the chain at startup →
**restart after editing** (`launchctl kickstart -k gui/$UID/sh.hermes.gateway` + reopen the
desktop app); 429/billing failures auto-advance the chain (`try_activate_fallback`,
`chat_completion_helpers.py`); aux tasks + cron jobs with `provider: auto`/None FOLLOW the
main provider — pin them explicitly or a provider flip breaks them.

**Claude Code / Codex / any OpenAI-SDK agent:** same chain as a try-order wrapper —
attempt NIM, on 429/5xx retry once, then construct the next client in the list
(`OpenAI(base_url=…, api_key=…)` for NIM/Ollama/OpenRouter; native SDK for Anthropic/OpenAI).
Reference implementation: DreamMakeTrue's `llm.py` `_OllamaFallbackClient`.

**Browser apps:** NIM blocks third-party CORS — deploy `nim-bridge/` (in this skill dir),
a one-function Vercel proxy where every caller brings their own key.

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
