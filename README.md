# SOS: Self-Optimization System

**Your AI agents forget to work. This system catches them — and fixes them automatically.**

**Your AI bills are 19x higher than they need to be. One command cuts 94.7%.**

**All three OpenClaw services monitored: base gateway (3000), enterprise bot (18789), web UI (5173). Crash at 3 AM → detected in 5 minutes.**

A zero-dependency Python framework that makes AI agent operations reliable, affordable, and self-correcting. Built for [OpenClaw](https://docs.openclaw.ai). 430 tests. Zero external packages. Runs on your machine, on your schedule.

```bash
pip install -e ".[dev]" && make install-watchdog && make cost-audit
```

> See [NEWS.md](NEWS.md) for latest updates

---

## 1. Local LLM Fallback: Survive a Cloud Outage

**The problem you're solving:** Your AI bill hits zero mid-session. Or the key rate-limits. Or the network drops at 2 AM. The cloud model goes dark and your whole app dies with it — even for a request a small local model could have answered fine.

**With this:** Wrap any cloud LLM call. When — and _only_ when — it fails for an availability reason (429, 5xx, depleted credits, dropped connection), it transparently retries against a local [Ollama](https://ollama.com) model. A 400 bad-request (your bug) still re-raises, so failures you _should_ see aren't hidden.

```python
from local_llm_fallback import with_local_fallback, OllamaConfig

answer = with_local_fallback(
    cloud_call,                       # your Anthropic/OpenAI/etc. call; raises on failure
    messages=[{"role": "user", "content": "..."}],
    system="Be terse.",
    ollama=OllamaConfig(model="qwen2.5:7b"),   # the local backup brain
)
```

- **Zero external packages** — stdlib `urllib` to Ollama's OpenAI-compatible endpoint.
- **Provider-agnostic** — duck-typed error classification (`is_availability_error`) works across SDKs without importing any of them.
- **Observable** — `FallbackStats` records failovers so a `/status` endpoint can show _"on backup"_ live; `model_available()` checks the model is pulled.

Setup: `ollama serve && ollama pull qwen2.5:7b`. Reference implementation (Anthropic SDK → Ollama, returning an Anthropic-shaped response so call sites need no change): DreamMakeTrue `apps/api/src/llm.py`.

---

## 2. Claude Code Artifacts: Reusable Skills & Commands

**The problem you're solving:** You build a genuinely good Claude Code skill or command inside one product repo, then it dies there — the next project re-invents it from scratch.

**With this:** Reusable Claude Code artifacts ship as an **installable plugin** ([`plugins/sos/`](plugins/sos/)) — this repo is also a Claude Code **plugin marketplace**, so the skills work on **any machine**, not just where they were built (there's no Anthropic-cloud sync of `~/.claude`). Markdown skills + a command — no Python required (the self-monitoring _patterns_ stay in `src/`).

```bash
/plugin marketplace add wjlgatech/sos
/plugin install sos@wjlgatech-plugins
# → /sos:goal-10x  /sos:ship-loop  /sos:lavish  /sos:treehouse  /sos:no-mistakes
#   /sos:freellmapi  /sos:living-knowledge  /sos:copilotkit  /sos:future-self   (this machine)
```

**Want the bare `/goal-10x` name too — on every machine?** One idempotent command does both steps above *and* symlinks `~/.claude/commands/goal-10x.md` to the live plugin command (so `/goal-10x` and `/sos:goal-10x` both work, and stay in sync). Re-run it on each new computer:

```bash
curl -fsSL https://raw.githubusercontent.com/wjlgatech/sos/main/plugins/sos/scripts/install-goal-10x.sh | sh
# update later:  claude plugin marketplace update wjlgatech-plugins
```

> **Other agents (Hermes, etc.) on any machine:** clone this repo and run `bash plugins/sos/scripts/install-skills-global.sh` — it symlinks the skills into Claude Code's (`~/.claude/skills`) and Hermes's (`$HERMES_SKILLS_DIR`) global skill dirs from the clone, so both agents discover them everywhere.

Headliner: **`/sos:goal-10x`** — a project-agnostic objective-driven dev loop that researches the codebase + the user's intention, coaches via adaptive Q&A + ADEPT explanations, drives every objective to green (verify → fix → loop), and self-improves each run.

**One loop, two gears.** `/sos:goal-10x` is the single front door. It drives work to green in a **sequential gear** by default, and shifts into a **parallel gear** — the `/sos:ship-loop` fan-out — when the work decomposes into many independent units. You pick the objective; `goal-10x` picks the gear (the size of the spec's independent set is the dial). The two share one verification-harness discovery and one self-improve tail, so there's a single mental model, not two competing loops.

- **Sequential gear** — start here for fuzzy, small, or coupled work (one PR's worth). `goal-10x` discovers the repo's own test/check harness and drives it green.
- **Parallel gear — `/sos:ship-loop`** — the **Plan → Code → Validate** lifecycle for high-velocity, *parallel* shipping (distilled from Kun Chen's lavish/treehouse/no-mistakes). `goal-10x` escalates here automatically when the work is parallelizable; invoke it directly only for knowingly bulk, decomposable work. It composes three **agent-agnostic** skills — usable by Claude, Codex, Hermes, or OpenClaw — that compound:

- **`/sos:lavish`** (Plan): turn a rough idea into an AI-ready **HTML** spec — a *queryable* contract (stable requirement ids, machine-checkable acceptance criteria, file maps, parallelization tags) that agents parse far more reliably than prose. HTML, not Markdown, because a spec is a typed tree, not a blob.
- **`/sos:treehouse`** (Code): fan the spec out to many agents in **isolated git worktrees** — decompose by dependency into waves (with same-wave file-collision detection), one unit per agent per worktree per PR. Produces PRs, never self-merges.
- **`/sos:no-mistakes`** (Validate): audit each PR for the mistakes *AI* makes — hallucinated APIs, silent scope creep, theater tests, security naivety — into a merge/fix/reject verdict. Runs **on top of** unit tests as the final gate, not instead of them.

<details>
<summary><b>What's included (plugin <code>sos</code>)</b></summary>

| Component                     | Type     | What it does                                                                                          |
| ----------------------------- | -------- | ----------------------------------------------------------------------------------------------------- |
| `commands/goal-10x.md`        | command  | `/sos:goal-10x` — **the front door**: research + coach + drive-to-green + self-improve. Sequential gear by default; escalates to the parallel gear when work is decomposable |
| `commands/ship-loop.md`       | command  | `/sos:ship-loop` — **the parallel gear of goal-10x**: Plan→Code→Validate fan-out composing the three skills below (rough idea → audited PRs at volume) |
| `skills/lavish/`              | skill    | Plan: rough idea → AI-ready **HTML** spec (queryable, machine-checkable, parallelizable) + scaffold/validator |
| `skills/treehouse/`           | skill    | Code: fan a spec out to parallel agents in isolated worktrees (dependency waves, collision detection) + planner |
| `skills/no-mistakes/`         | skill    | Validate: audit AI code for AI-specific failure modes → merge/fix/reject (on top of unit tests, not instead) |
| `skills/freellmapi/`          | skill    | stand up & use FreeLLMAPI — 16 free provider tiers behind one OpenAI-compatible endpoint; one base_url+key for every agent |
| `skills/living-knowledge/`    | skill    | explain a concept just in time, at the right depth (4 layers, transfer-as-proof)                      |
| `skills/copilotkit/`          | skill    | integrate CopilotKit into a Next.js app, gotchas pre-solved                                           |
| `skills/future-self/`         | skill    | "Be Your Future Self Now" framework, operationalized                                                  |
| `scripts/install-goal-10x.sh` | util     | one-command, idempotent cross-machine install: add marketplace + install plugin + symlink bare `/goal-10x` |
| `scripts/install-doc-sync.sh` | util     | CHANGELOG + docs-sync pre-commit guard for any repo (run manually)                                    |
| `scripts/install-skills-global.sh` | util | symlink the skills into Claude Code + Hermes global skill dirs from a clone (cross-agent, cross-machine) |

See [`plugins/sos/README.md`](plugins/sos/README.md) for details + provenance.

</details>

---

## 3. E2E Testing: Browser Automation for Any Webapp

**The problem you're solving:** You have a webapp. You test it manually. You ship a regression. The form doesn't clear after submit, the async button stays disabled, the live counter stops updating — and you find out from a user, not a test.

**With this:** A reusable Playwright framework at `tests/e2e_framework/` that tests user journeys, not implementation details. Output is structured for both human debugging and AI agents (Claude Code, OpenClaw).

```bash
pip install pytest-playwright && playwright install chromium
pytest tests/ -k "e2e" --base-url http://localhost:PORT --headed   # visible browser
pytest tests/ -k "e2e" --base-url http://localhost:PORT            # headless (CI)
```

**Available primitives:**

| Primitive               | Use when                                                  |
| ----------------------- | --------------------------------------------------------- |
| `assert_button_cycle`   | Async button: click → disables → work → re-enables        |
| `assert_form_clears`    | Form submit: fill → submit → success text → fields clear  |
| `assert_toggle_pair`    | Show/hide toggle: click → one panel shows, one hides      |
| `assert_layer_tabs`     | Tab switching: each tab shows exactly one layer           |
| `assert_live_update`    | Auto-refresh: element text changes within N seconds       |
| `poll_api_job`          | Poll a REST job endpoint until terminal state             |
| `trigger_and_poll`      | POST to trigger + poll in one call                        |
| `capture_console`       | Context manager: capture browser JS errors                |
| `screenshot_on_failure` | Context manager: auto-screenshot on any assertion failure |

<details>
<summary><b>Technical innovation: AI-readable failure output</b></summary>

Failure messages are formatted for grep + Read tool consumption:

```
[E2E FAIL] create_item
  Field '#item-name' not cleared after submit — still contains: 'Widget'
  Screenshot: /tmp/e2e_create_item.png
```

Claude Code / OpenClaw: grep `[E2E FAIL]` in output → read the `Screenshot:` path with the Read tool.

</details>

<details>
<summary><b>Implementation: journey-first test primitives</b></summary>

```python
from tests.e2e_framework import assert_button_cycle, assert_form_clears, screenshot_on_failure

def test_create_item(page):
    with screenshot_on_failure(page, "create_item"):
        assert_form_clears(
            page,
            fields={"#item-name": "Widget"},
            submit="#btn-create",
            success_selector="#toast",
            success_text="Created",
            label="create_item",
        )

def test_async_action(page):
    with screenshot_on_failure(page, "async_action"):
        assert_button_cycle(page, button="#btn-run", label="run_job",
                            expect_disabled_ms=2000, expect_reenabled_ms=30000)
```

See `tests/e2e_framework/README.md` for full documentation.

</details>

---

## 4. Marketing Eval: Close the Loop on Content

**The problem you're solving:** You wrote marketing content for your project — social posts, articles, launch announcements. Then you published it and never looked at it again. No impressions tracked. No engagement measured. No way to know what's working. Your optimization system optimizes everything except how you tell people about it.

**With this:** The same DISCOVER → SCORE → RECOMMEND → REPORT architecture that evaluates code quality now evaluates marketing content. Five sub-scores, channel-normalized benchmarks, six recommendation types, and GitHub Issues on grade degradation.

```bash
make marketing-discover    # scan marketing/ for content
make marketing-eval        # full evaluation report
make marketing-status      # inventory: published vs draft
```

**Scoring (weighted composite, 0-100):**

| Sub-score       | Weight | What it measures                                                        |
| --------------- | ------ | ----------------------------------------------------------------------- |
| Engagement rate | 30%    | engagements / impressions, normalized                                   |
| Reach           | 20%    | impressions vs channel benchmarks (Twitter: 5K good, LinkedIn: 2K good) |
| Conversion      | 20%    | clicks + conversions relative to engagement                             |
| Content quality | 15%    | structural: word count, CTAs, links, code blocks, hashtags              |
| Freshness       | 15%    | decay: `max(0, 100 - days_old * 2)`                                     |

Grades: A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, F < 60. Draft content scored on quality only.

<details>
<summary><b>Technical innovation: channel-normalized cross-platform comparison</b></summary>

Different platforms have wildly different reach baselines. The scoring engine normalizes using channel benchmarks — a LinkedIn post with 2,000 impressions and a tweet with 5,000 impressions both score "good" (50/100). This enables honest cross-platform comparison and surfaces channel arbitrage: where your content overperforms relative to the platform norm.

10x signal detection flags any post with 3x the average engagement for replication analysis.

</details>

<details>
<summary><b>Implementation: the closed loop</b></summary>

```
COLLECT → ANALYZE → ADVISE → EXECUTE → EVALUATE → REPEAT
  │          │         │         │          │         │
  manual    auto      auto    manual      auto     semi
```

- **COLLECT**: `marketing-discover` scans `marketing/`, parses multi-post files, SHA-256 fingerprints for drift detection
- **ANALYZE**: 5-score weighted composite with channel benchmarks
- **ADVISE**: 6 recommendation types (channel optimization, attribute correlation, cadence, underperformers, next content, 10x signals) + intervention tiers (C→refresh, D→A/B test, F→full audit)
- **EXECUTE**: Manual — human acts on recommendations (no auto-posting)
- **EVALUATE**: 90-entry FIFO history, trend tracking, GitHub Issues on grade drop
- **REPEAT**: Weekly CI (`.github/workflows/marketing-eval.yml`), daily orchestrator integration

Record metrics via CLI:

```bash
python src/__main__.py marketing-metrics \
  --content-id social-posts-post-1 \
  --impressions 5000 --engagements 200 --clicks 45

python src/__main__.py marketing-publish \
  --content-id social-posts-post-1 \
  --url https://x.com/post/1
```

</details>

---

## 5. Multi-Agent Performance Tracking: Find the Weak Link

**The problem you're solving:** You're running multiple AI agents in parallel. One is underperforming, but you can't tell which one or how badly without manual investigation.

**With this:** Per-agent performance tracking with automatic escalation. Score drops below 70%? Performance review. Below 50%? Targeted coaching. Sustained low? Full rehabilitation program.

```bash
.venv/bin/python src/__main__.py intervention --agent loopy-0
```

<details>
<summary><b>Technical innovation: weighted multi-signal scoring</b></summary>

Performance score = accuracy (40%) + efficiency (35%) + adaptability (25%). Uses first-half vs second-half comparison for trend detection (>5% = improving, <-5% = declining). Agent names normalized automatically (`loopy` -> `loopy-0`, `loopy1` -> `loopy-1`).

</details>

<details>
<summary><b>Implementation: config-driven escalation tiers</b></summary>

| Tier   | Trigger       | Duration | Actions                                       |
| ------ | ------------- | -------- | --------------------------------------------- |
| Tier 1 | Score < 70%   | 2 weeks  | Performance review, skill assessment          |
| Tier 2 | Score < 50%   | 1 month  | Targeted coaching, personalized learning plan |
| Tier 3 | Sustained low | 3 months | Comprehensive rehabilitation program          |

Thresholds configured in `config.yaml`. Falls back to sensible defaults if config is missing.

</details>

---

## 6. Daily Reviews: Automated Performance Reflections

**The problem you're solving:** "Was today productive?" You either guess, or spend 30 minutes reviewing logs and commits manually. Every day.

**With this:** At 11 PM every night, the system scans the day's work, calculates performance metrics, and writes a data-driven reflection to markdown. When you arrive next morning, the summary is already there.

```bash
.venv/bin/python src/__main__.py --agent-id loopy-0 daily-review
```

<details>
<summary><b>Technical innovation: LLM-optional analysis</b></summary>

Set `ANTHROPIC_API_KEY` to get AI-generated narrative sections via Claude Haiku (stdlib `urllib.request`, no dependencies). Without the key, everything still works using rule-based analysis. The system never depends on an API to function.

</details>

<details>
<summary><b>Implementation: scan + score + write pipeline</b></summary>

1. Scan all git repos for the day's commits
2. Count file modifications across the workspace
3. Calculate performance metrics (goal completion, task efficiency)
4. Write reflection to `~/.openclaw/workspace/memory/daily-reflections/YYYY-MM-DD-reflection.md`
5. Persist state for trend analysis

</details>

---

## 7. Idle Detection + Auto-Recovery: Agents That Fix Themselves

**The problem you're solving:** Your AI agent has been "running" for 6 hours but produced nothing. No commits, no file changes, no output. Worse — even when the system detected the idle state, it only logged it. Nothing actually happened.

**With this:** Every 2 hours, the system scans real filesystem activity AND probes all service health. Zero output triggers automatic intervention: the idle detector dispatches emergency actions directly into the self-improvement engine. Critical services down? Reported immediately alongside idle rate. Strategic analysis kicks off, skill development starts, research sprints begin — all without human intervention.

```bash
.venv/bin/python src/__main__.py --agent-id loopy-0 idle-check
```

**What you get back:**

```json
{
  "triggered": true,
  "actions_proposed": [
    "conduct_strategic_analysis",
    "explore_new_skill_development"
  ],
  "actions_executed": [
    "conduct_strategic_analysis",
    "explore_new_skill_development"
  ],
  "idle_rate": 0.97,
  "service_health": {
    "gateway": { "healthy": true, "port": 3000 },
    "enterprise": { "healthy": false, "port": 18789, "critical": true },
    "vite-ui": { "healthy": true, "port": 5173 }
  },
  "services_down": ["enterprise"]
}
```

`actions_proposed` vs `actions_executed` = no more log-only interventions. `service_health` = every idle check also verifies all OpenClaw services are up.

<details>
<summary><b>Technical innovation: handler-dispatch architecture</b></summary>

Instead of a monolithic "detect idle, then do X" pipeline, emergency actions use a **handler registry pattern**. Each action name maps to a callable. The orchestrator registers 5 handlers at init that route directly to the self-improvement protocol:

- `conduct_strategic_analysis` -> improvement execution (target: problem_solving)
- `explore_new_skill_development` -> improvement execution (target: learning)
- `start_research_sprint` -> improvement execution (target: task_execution)
- `design_experimental_prototype` -> improvement execution (target: learning)
- `initiate_user_feedback_loop` -> improvement execution (target: communication)

Handlers are isolated: one failure doesn't block others. Unhandled actions fall back to logging. New actions can be registered without modifying core detection logic.

</details>

<details>
<summary><b>Implementation: filesystem scanner + action dispatch</b></summary>

The filesystem scanner examines `~/.openclaw/workspace/`:

- `git log` across all subdirectories with `.git`
- `mtime` checks across the workspace tree
- Markdown parsing in `memory/daily-reflections/`

Detection flow:

1. Calculate idle rate from real filesystem activity
2. If above threshold: generate context-aware emergency actions (contrasts dominant activity type)
3. Dispatch each action through registered handlers
4. Track `actions_proposed` vs `actions_executed` separately
5. Persist updated capability_map to state

</details>

---

## 8. Cost Governor: Cut Your AI Bill by 94.7%

**The problem you're solving:** You're running Claude Opus at $15/M input tokens for every turn — including heartbeat inbox checks, simple Q&A, and routine tasks. Your monthly bill is 19x higher than it needs to be.

**With this:** One command audits your config, identifies waste, and applies optimized settings. Real result from our production setup:

| Metric        | Before           | After           | Change                     |
| ------------- | ---------------- | --------------- | -------------------------- |
| Model cost    | $15.00/M tokens  | $0.80/M tokens  | **-94.7%**                 |
| Compaction    | safeguard (lazy) | default (eager) | Stops token growth         |
| Heartbeat     | Opus ($15/M)     | Haiku ($0.80/M) | Trivial work, trivial cost |
| Bootstrap cap | 150K chars       | 8K chars/file   | 19x tighter                |

```bash
make cost-audit     # find waste
make cost-status    # track savings vs baseline
make cost-govern    # periodic governance cycle
```

<details>
<summary><b>Technical innovation: non-additive savings estimation</b></summary>

Multiple optimizations don't add linearly — two 50% savings compound to 75%, not 100%. The governor uses `1 - product(1 - r_i)` to calculate compound savings honestly, capped at 95%. Each recommendation shows individual impact plus the realistic combined total. No overpromising.

</details>

<details>
<summary><b>Implementation: config audit + patch + baseline tracking</b></summary>

The governor reads `~/.openclaw/openclaw.json` and detects:

- **Expensive default model**: Flags Opus/GPT-4o, recommends Haiku/mini/local
- **Heartbeat waste**: Detects heartbeat inheriting expensive model for trivial inbox checks
- **Bootstrap bloat**: Measures all auto-injected files (AGENTS.md, SOUL.md, etc.), flags oversized caps
- **Weak compaction**: Detects `safeguard` mode, recommends `default` for earlier compaction

Three strategies: `aggressive` (local Ollama, free), `balanced` (Haiku, 19x cheaper), `conservative` (keep model, trim waste). Applies via deep-merge with automatic backup.

```bash
# Preview
.venv/bin/python src/__main__.py cost-apply --strategy balanced --dry-run
# Apply (creates ~/.openclaw/openclaw.json.pre-governor.bak)
.venv/bin/python src/__main__.py cost-apply --strategy balanced
# Track over time
.venv/bin/python src/__main__.py cost-baseline && .venv/bin/python src/__main__.py cost-status
```

</details>

---

## 9. Gateway Watchdog: Sleep Through Outages

**The problem you're solving:** Your AI gateway crashes at 3 AM on a Saturday. Your Telegram bot, Discord channels, and Slack integrations all go dark. You wake up Sunday to 47 undelivered messages and an angry group chat.

**With this:** The watchdog monitors all three OpenClaw services every 5 minutes: base gateway (port 3000), enterprise gateway (port 18789), and web UI (port 5173). Services with launchd agents get auto-restarted. Services without launchd (enterprise gateway) get flagged as `critical_down` for immediate manual intervention.

```bash
make install-watchdog      # one command, handles everything
make watchdog-status       # see what's happening
make uninstall-watchdog    # clean removal
```

<details>
<summary><b>Technical innovation: sandbox-aware cron deployment</b></summary>

macOS cron can't read `~/Documents/` or access Python virtualenvs due to TCC sandboxing. The installer solves this by deploying to `~/.openclaw/scripts/` with system Python, auto-detecting the gateway port from config and Node.js path from the LaunchAgent plist. One command replaces 5 manual steps.

</details>

<details>
<summary><b>Implementation: multi-service TCP probes + launchctl restart</b></summary>

Every 5 minutes via system crontab, probes all three services:

| Service            | Port  | Auto-restart  | Critical |
| ------------------ | ----- | ------------- | -------- |
| Base gateway       | 3000  | Yes (launchd) | Yes      |
| Enterprise gateway | 18789 | No (manual)   | Yes      |
| Web UI (Vite)      | 5173  | No (manual)   | No       |

For services with launchd agents:

1. TCP socket probe to `127.0.0.1:{port}` (faster than HTTP health checks)
2. If down: `launchctl kickstart -k` (atomic kill + restart)
3. If kickstart fails: `bootout` + `bootstrap` (full service reload)
4. 3 retry attempts with 10s delays and post-restart verification

For services without launchd: detected and reported as `critical_down` or `degraded`. JSON results logged to `/tmp/openclaw-watchdog.log`.

Idempotent cron management via marker comments. Safe to run `make install-watchdog` repeatedly.

</details>

---

## Safety, Efficiency & Scalability

Independent evaluation across 13 source modules (~5,600 lines):

| Dimension       | Score  | Highlights                                                                                                                                                                                                                                                                                                                                      |
| --------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Safety**      | 7.5/10 | Input validation on all public APIs. Atomic file writes (temp + rename) across all state persistence. Exception isolation in every loop — one failing callback never blocks others. Ethical constraint framework on self-improvement proposals. API keys read from env only, never logged. Subprocess calls use list form (no shell injection). |
| **Efficiency**  | 8.0/10 | FIFO caps on activity_log (100), verification_history (1000), watchdog history (50), cost baselines (20). O(n) algorithms where n is bounded. State persistence every 2 hours, not every operation. LLM calls optional and single-shot (no retry loops).                                                                                        |
| **Scalability** | 7.0/10 | Multi-agent support via config.yaml. Handler/callback/strategy registries for extension without core modification. Daemon mode with SIGTERM handling. Config-driven thresholds and escalation tiers.                                                                                                                                            |

<details>
<summary><b>What makes this safe to run as a daemon</b></summary>

- **Atomic writes everywhere**: State files use `write-to-tmp + os.replace()` pattern — no corruption on crash
- **Per-item exception handling**: Daemon loop, callback dispatch, handler dispatch all wrap individual items in try/except
- **Bounded memory**: Activity logs capped at 100 entries, verification at 1000, watchdog at 50
- **Graceful shutdown**: SIGTERM handler sets flag, current loop finishes cleanly
- **No shell injection**: All subprocess calls use `subprocess.run([...])` list form with timeouts
- **Secrets never logged**: API keys and gateway tokens read from env/config, never appear in logs or state files

</details>

<details>
<summary><b>Known limitations (honest accounting)</b></summary>

- `improvement_history` and `performance_history` are unbounded — will accumulate ~17 MB/year in daemon mode (tracked for future cap)
- State files not scoped by agent_id — concurrent multi-agent daemons can race on writes
- Config changes require daemon restart (no hot-reload)
- Ethical constraint fields on proposals are opt-in — not enforced if proposal omits them

</details>

---

## Quickstart

```bash
cd ~/.openclaw/workspace/self-optimization
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

make install-watchdog    # gateway auto-recovery
make cost-audit          # find cost waste
```

## Scheduling

| Job              | Schedule      | Setup                        |
| ---------------- | ------------- | ---------------------------- |
| Gateway watchdog | Every 5 min   | `make install-watchdog`      |
| Idle check       | Every 2 hours | `~/.openclaw/cron/jobs.json` |
| Daily review     | 11 PM daily   | `~/.openclaw/cron/jobs.json` |
| Cost governance  | On demand     | `make cost-govern`           |

## Architecture

```
src/
├── cost_governor.py               # Token/cost optimization
├── gateway_watchdog.py            # Gateway health monitor
├── anti_idling_system.py          # Idle detection + action dispatch
├── filesystem_scanner.py          # Real activity detection
├── multi_agent_performance.py     # Performance tracking
├── recursive_self_improvement.py  # Self-improvement protocol
├── results_verification.py        # Result quality (SMARC)
├── self_eval.py                   # Discover/heal/evaluate/report (A-F grade)
├── marketing_eval.py              # Marketing content effectiveness
├── orchestrator.py                # Integration layer
├── config_loader.py               # YAML parser (no PyYAML)
├── llm_provider.py                # Anthropic API (stdlib urllib)
├── local_llm_fallback.py          # Ollama failover on cloud outage
└── __main__.py                    # CLI entry point
tests/
└── e2e_framework/                 # Reusable Playwright browser automation
```

**Zero dependencies.** Entire system runs on Python stdlib. No `requests`, no `pyyaml`, no `psutil`. Cron jobs and launchd agents start fast and work without virtualenv activation.

## Development

```bash
source .venv/bin/activate
make check   # ruff lint + mypy typecheck + pytest (430 tests, all passing)
```

See `CLAUDE.md` for design decisions, test conventions, and contributor workflow.

## License

MIT
