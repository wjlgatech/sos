# Changelog

All notable changes are logged here — for humans **and** agents.
Format follows [Keep a Changelog](https://keepachangelog.com/). Newest first.

## [Unreleased]

### Added

- `dreammaketrue` skill: **`view` command — visualize the living knowledge.** `dmt.py view
  <room_id>` turns a room's topic map into ONE self-contained interactive HTML artifact
  (zero deps, offline, shareable; auto-opens on macOS): force-directed canvas graph
  (drag · zoom · click; concepts/claims/evidence color-typed, labeled edges) where clicking
  a node opens its living-knowledge layers progressively — L1 jargon-free summary → L3
  principle + transfer domains → L5 the surrounding web (typed edges + verbatim evidence).
  `window.dmtSelect('name')` lets an agent driving a browser open a node's layers without
  pointer math. _Why:_ the engine's visualization lived only in the webapp; agents (and
  anyone the user shares the file with) needed a portable equivalent. Verified headless:
  rendered 29-node Chamath room, programmatic select, full L1→L3→L5 panel content.
  _Investigated/Rejected:_ first force model applied the spring along the full displacement
  (`dx*f`) — velocities exploded and every node flew off-canvas within a second (blank
  screenshot); fixed to unit-vector force with a ±4 clamp.
- `install-skills-global.sh`: also **wires Codex** — appends an idempotent "sos skills
  directory" section to `~/.codex/AGENTS.md` (Codex has no skills dir; its global AGENTS.md
  is the discovery mechanism), so all three agents (Claude Code, Hermes, Codex) pick up
  skills from one sos clone. `CODEX_AGENTS_MD` overrides the path; skipped if `~/.codex`
  doesn't exist.
- `plugins/sos/skills/dreammaketrue/` — **DreamMakeTrue as a cross-agent tool.** A skill +
  zero-dependency CLI (`scripts/dmt.py`, stdlib urllib) that lets ANY agent (Claude Code,
  Hermes, Codex, OpenClaw) drive the Participation Engine: `analyze` (any source → knowledge
  map + grounded avatars → durable Room), `chat` (grounded avatar turns, folded back into the
  room transcript), `express` (room → user-attributed LinkedIn post / essay / podcast script),
  plus `ingest` / `rooms` / `library` / `status`. Self-heals when the engine is down (launchd →
  uvicorn from a local clone → clear install instructions); `DMT_API_URL` targets a remote
  engine. _Why:_ the engine was webapp-only — packaging the API (not the app) as a skill makes
  every agent a client of the same engine, so the data moat (rooms, shared library) compounds
  no matter which agent drives. Verified end-to-end live: status → rooms → library → a real
  grounded Chamath chat turn (41s on local Ollama). Eval note: a hook that silently intercepts
  was rejected — skills auto-trigger on intent, which is the right "without prompting" shape.

### Changed

- `README.md` — reordered the nine feature sections newest-first (Local LLM Fallback → …
  → Gateway Watchdog), matching `NEWS.md` and the git introduction dates, and corrected stale
  facts surfaced by an accuracy audit: test count 377 → **430** (clean Python 3.12 collection),
  "11 source modules (~3,200 lines)" → **13 modules (~5,600 lines)**, added `self_eval.py` and
  `local_llm_fallback.py` to the architecture tree, and retitled §2 to "Reusable Skills &
  Commands" (no workflow is distributed anymore). _Why:_ keep the README reflecting the
  shipped situation, newest work first.

### Removed

- `plugins/sos/workflows/goal-10x.js` — the old multi-agent goal-10x workflow. Once the `sos`
  plugin is installed it surfaced as a second `/sos:goal-10x` entry that collided with the
  consolidated `/goal-10x` command ("one loop, two gears", commit #15), reintroducing the exact
  "two competing loops" that consolidation removed. Its parallel multi-agent capability lives on
  as the **parallel gear** (`/sos:ship-loop` → `lavish`/`treehouse`/`no-mistakes`), so nothing is
  lost. _Why:_ keep a single front door — one goal-10x, no divergent duplicate.

### Added

- `plugins/sos/scripts/install-goal-10x.sh` — one-command, idempotent cross-machine
  installer for `/goal-10x`. Registers the `wjlgatech/sos` marketplace, installs the `sos`
  plugin at user scope, and symlinks `~/.claude/commands/goal-10x.md` to the live plugin
  command so both the bare `/goal-10x` and namespaced `/sos:goal-10x` work on any machine and
  stay in sync via `claude plugin marketplace update`. _Why:_ `~/.claude` has no Anthropic-cloud
  sync, so the git-backed marketplace is the supported way to carry the command across computers;
  the symlink restores the bare name a plugin install can't provide on its own.
