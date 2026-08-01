# `sos` — Claude Code plugin

Reusable **Claude Code** artifacts bundled as an installable plugin, so they work on **any
machine** (not just where they were built). Markdown skills + a command — no Python required.
(The Python self-monitoring _patterns_ live in the repo's `src/`.)

## Install (any machine)

```bash
/plugin marketplace add wjlgatech/sos
/plugin install sos@wjlgatech-plugins
```

Then the skills are available **namespaced** under `sos:` in every project on that machine:
`/sos:goal-10x`, `/sos:ship-loop`, `/sos:lavish`, `/sos:treehouse`, `/sos:no-mistakes`,
`/sos:freellmapi`, `/sos:living-knowledge`, `/sos:living-repo`, `/sos:knowledge-graph`,
`/sos:dreammaketrue`, `/sos:free-llm`, `/sos:copilotkit`, `/sos:future-self`,
`/sos:animate-anything`, `/sos:voice`. Update with `/plugin marketplace update wjlgatech-plugins`.

To also get the **bare** `/goal-10x` (no `sos:` prefix) on every machine, run the bundled
bootstrap — it does both commands above *and* symlinks `~/.claude/commands/goal-10x.md` to the
live plugin command (idempotent; re-run per machine):

```bash
curl -fsSL https://raw.githubusercontent.com/wjlgatech/sos/main/plugins/sos/scripts/install-goal-10x.sh | sh
```

**Personal operating instructions, every session:** the plugin also carries
[`instructions/claude-instructions.md`](instructions/claude-instructions.md) — how Claude
should work *with Paul* (voice, two-rail output contract, focus protocol, hard mode), as
opposed to the skills, which teach it tasks. `install-claude-instructions.sh` copies it to
`~/.claude/instructions-paul-wu.md` and adds the `@~/.claude/instructions-paul-wu.md` import
to `~/.claude/CLAUDE.md`, which Claude Code loads at the start of every session in every
project. Idempotent; re-run per machine and after edits (edit the repo file, not the copy):

```bash
curl -fsSL https://raw.githubusercontent.com/wjlgatech/sos/main/plugins/sos/scripts/install-claude-instructions.sh | sh
```

**Other agents (Hermes, etc.), any machine:** clone this repo and run
`bash plugins/sos/scripts/install-skills-global.sh` — it symlinks these skills into Claude
Code's (`~/.claude/skills`) and Hermes's (`$HERMES_SKILLS_DIR`) global skill dirs from the
clone, so both agents discover them everywhere. `git pull` updates them in place.

> No Anthropic-cloud sync of `~/.claude` exists — this plugin (a git-backed marketplace) is
> the supported way to get the same skills across machines.

📖 **`/goal-10x` deep dive:** [`docs/goal-10x.md`](../../docs/goal-10x.md) — what it is/isn't,
when (not) to use it, correct-vs-wrong usage with examples, the first-principles mechanism,
and installing it across projects **and** computers.

## What's inside

> **★ Newest — `/voice`** (v1.9.0): push-to-talk voice for any agent, doctor-first. Record the mic →
> a WAV → text **locally, no key**; capture bundled, STT/TTS a seam you wire. Details in the table below.

| Component                     | Type      | What it does                                                                                                                                                                     |
| ----------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `skills/voice/`               | skill     | **★ `/sos:voice` — push-to-talk voice for any agent, doctor-first.** Recreated + simplified from the hermes-agent voice engine into one self-contained `scripts/voice.py` (stdlib): `doctor` (name the missing layer + the exact fix), `record` (mic → 16 kHz WAV), `transcribe` (local faster-whisper, no key). **Capture is bundled; STT/TTS are a wired seam.** Never crashes headless (audio libs lazy-imported); honors forwarded audio (SSH/Docker/WSL). |
| `commands/goal-10x.md`        | command   | `/sos:goal-10x` — **the front door** (one loop, two gears): research codebase + user intention, coach via adaptive Q&A + ADEPT, drive to green, self-improve. Sequential gear by default; escalates to the parallel gear when work is decomposable. |
| `commands/ship-loop.md`       | command   | `/sos:ship-loop` — **the parallel gear of goal-10x**: the Plan→Code→Validate fan-out composing lavish + treehouse + no-mistakes to drive a rough idea to audited PRs at volume. Agent-agnostic; invoke directly only for knowingly bulk work. |
| `skills/lavish/`              | skill     | **Plan.** Turn a rough idea into an AI-ready **HTML** spec (queryable `data-*` requirements, machine-checkable acceptance, parallelization tags). Why HTML beats Markdown for specs. + `new-spec.sh` scaffold/validator. |
| `skills/treehouse/`           | skill     | **Code.** Fan a spec out to many agents in isolated git worktrees — decompose by dependency into waves, one unit/agent/worktree/PR, agent-agnostic unit-of-work contract. + `plan-fanout.sh` wave planner (collision detection). |
| `skills/no-mistakes/`         | skill     | **Validate.** Audit AI-generated code for AI-specific failure modes (hallucinated APIs, scope creep, theater tests, security naivety) → merge/fix/reject verdict. Runs on top of unit tests, not instead. |
| `skills/freellmapi/`          | skill     | Stand up & use FreeLLMAPI — a self-hosted proxy pooling 16 providers' free tiers into one OpenAI-compatible endpoint with failover. One `base_url`+key for Claude Code, Hermes, Codex, OpenClaw. + `freellmapi.sh` up/status/test. |
| `skills/living-knowledge/`    | skill     | Explain a concept just in time, at the right depth — 4 layers (Sensation→Mechanism→Principle→Expression), real-time mode, name-the-seam, transfer-as-proof.                      |
| `skills/copilotkit/`          | skill     | Integrate CopilotKit (in-app AI copilot UI) into a Next.js app — provider + runtime route + actions, version/bundling gotchas pre-solved.                                        |
| `skills/future-self/`         | skill     | Hardy's "Be Your Future Self Now" framework, operationalized — emergent vs intended self + the gap.                                                                              |
| `skills/living-repo/`         | skill     | Transform a static awesome-list repo into a **living knowledge system**: deterministic README→typed-graph compiler (`awesome_kg.py`, stdlib-only, zero LLM tokens) + self-contained interactive force-graph HTML (GitHub Pages-ready) + weekly link-freshness GitHub Action (`check_freshness.py`). Optional NIM lineage enrichment. First deployment: [awesome-auto-ai-research](https://github.com/wjlgatech/awesome-auto-ai-research). |
| `skills/knowledge-graph/`     | skill     | Build a TOPIC or PERSONA knowledge graph from multi-source evidence with engagement-weighted confidence edges; `kg.py` dedups + renders a self-contained HTML view.              |
| `skills/dreammaketrue/`       | skill     | Drive the DreamMakeTrue Participation Engine via `dmt.py`: ingest any source, build knowledge maps + grounded avatars, `kgfy` one-shot living-knowledge artifacts.               |
| `skills/free-llm/`     | skill     | Free LLMs for any agent (formerly nvidia-free-llm): NVIDIA NIM primary + the standing fallback chain NIM → Ollama → OpenRouter → Anthropic/OpenAI; `nim.py` probes the live catalog; `nim-bridge/` CORS proxy for browser apps.                                                      |
| `skills/viral-loop/`   | skill     | **Closed-loop viral marketing** — loop engineering applied to media content: MAKE → AUTO-REVIEW (rubric ≥4/5) → 🔑 HUMAN GATE → PUBLISH+ENGAGE (drafted-never-sent replies) → MEASURE → LEARN. Backed by sos's `marketing_eval` engine when present (scores computed, never vibes); ledger fallback elsewhere. Drafts everything, sends nothing.                                                      |
| `skills/animate-anything/` | skill | **Concept → a 3Blue1Brown-style animated explainer.** Reverse-engineered Grant Sanderson's toolchain (target ManimCommunity, not ManimGL) + production style (the `#333333` warm-grey canvas, role-based palette, *morph-to-show-equivalence*, play→wait pacing). Bundled engine `scripts/animate.py` (stdlib): scaffold a 5-beat scene, lint it 0–100 against the style contract (gate slop), render locally to MP4. Two golden `examples/` (Text + LaTeX). Emit-the-composition, render-locally — no cloud video API. Home repo + ranked animation catalog: [wjlgatech/animate-anything](https://github.com/wjlgatech/animate-anything). |
| `scripts/install-goal-10x.sh` | installer | one-command cross-machine setup: add marketplace + install plugin + symlink the bare `/goal-10x` name. Idempotent; re-run per machine.                                            |
| `scripts/install-doc-sync.sh` | installer | (bundled util, run manually) drops a CHANGELOG + pre-commit docs-sync guard into any git repo.                                                                                   |
| `scripts/install-skills-global.sh` | installer | (run once per machine) symlinks these skills into Claude Code + Hermes global skill dirs from a clone — cross-agent, cross-machine availability without the marketplace.        |
| `instructions/claude-instructions.md` | config | Paul's personal operating instructions — the canonical copy of how Claude should work with him (voice, two-rail contract, focus protocol, hard mode, debug doctrine).       |
| `scripts/install-claude-instructions.sh` | installer | per-machine: copy the instructions to `~/.claude/instructions-paul-wu.md` + add the `@` import line to `~/.claude/CLAUDE.md` so every session loads them. Idempotent.  |

## Provenance

Built in the DreamMakeTrue Participation Engine and contributed here per the standing rule:
every reusable artifact is published to SOS (agent-monitoring/cost/quality _patterns_ → `src/`
modules; Claude Code _artifacts_ → this plugin) and installed globally for all projects.
