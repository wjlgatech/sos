# Changelog

All notable changes are logged here — for humans **and** agents.
Format follows [Keep a Changelog](https://keepachangelog.com/). Newest first.

## [Unreleased]

### Added

- `dreammaketrue` artifact: **the chat is now a persistent Ask dock beside the content**, not
  a third tab — you converse with the knowledge WHILE looking at the Map or the Infographic
  (Paul: "I can not ask questions [from the infographic]"). `#workspace` = content + 380px
  `aside#ask-dock` (header badge shows the serving tier); phones stack the dock below at
  46vh. Cited-node chips still jump-select on the Map. Republished the served artifact —
  a published page does NOT update itself when the template changes; regenerate + republish.
- `dreammaketrue` skill: kgfy/view artifacts **auto-publish to the engine** after render
  (best-effort POST /v1/engine/artifacts) and report `served_url` + `phone_url` (LAN). The
  page JS prefers `location.origin` when served over http(s) — same-origin Ask tab, no CORS,
  tunnel-churn-proof — and falls back to the baked engine URL only for file:// opens. This is
  how a phone gets the conversational experience: open the LAN link, not the attachment.
- `dreammaketrue` skill artifact v3 — **one tabbed page that you can talk to** (Paul's 4-part
  ask, /goal-10x run). Map · Infographic · Ask in a single self-contained HTML (was 2 files):
  (1) **incremental display** — the map starts at the concepts (30/79 on the test graph),
  each tap reveals that node's web (+N badges show hidden neighbors) and the inspector
  deepens progressively L1→L3→L5 — the living-knowledge contract, restored after the
  full-dump version; (2) **Ask tab** — graph-grounded chat → new engine `POST /v1/engine/
  kg/chat` (BFS paths between question-matched nodes, bridge detection, explicit no-path
  findings), cited nodes render as chips that jump to the Map tab and select the node;
  (3) **agentic** — creation intents return a full grounded artifact in-chat (verified: a
  LinkedIn post citing graph nodes, 30s on local Ollama); (4) mobile viewport + stacked
  layout for phones. Eval calls: Kumo stays on the relational moat (semantic graphs want
  traversal + LLM, not RFM); CopilotKit is right for the webapp, wrong for a portable
  single-file artifact (vanilla chat panel instead). `window.dmtAsk()` test hook.
- `dreammaketrue` skill: **infographic one-pager** (à la Google NotebookLM) emitted alongside
  every `kgfy`/`view` map — `…-infographic.html`: designed single page with a stat band
  (ideas/claims/quotes/connections), Big Ideas cards with ⚡principle callouts + transfer
  chips, two-column numbered Key Claims, dark verbatim-quote cards, and a transfer-domain
  cloud. Deterministic (built straight from the graph JSON — zero extra LLM cost), mobile
  viewport + print CSS (save-as-PDF to share). Gotcha fixed en route: same-quote nesting
  inside f-strings is Python 3.12+ only and auto-formatters normalize quotes INTO that form —
  build HTML fragments with explicit locals to stay 3.9-compatible.
- `dreammaketrue` skill: **`kgfy` — one word, any source → living-knowledge map.** Paul's
  spoken UX ("I give you a repo and say kg-fy it"): `dmt.py kgfy <anything>` handles a GitHub
  repo / website / YouTube / podcast URL (engine's tiered ingestion), a local file — PDF,
  audio, video, notebook routed through the engine's `/upload` extractors (pypdf·vision·
  whisper) via a stdlib multipart client, text read directly — or a folder (README + docs +
  up to 5 binaries). Straight to the chunked topic-map extractor and the interactive HTML;
  no room/avatars required. Generic "user-provided text" topic label replaced by the real
  source name. Verified live on free local Ollama: GitHub repo URL → 29 nodes (3min);
  9.7MB PDF → 38 nodes (4.6min).
- `dreammaketrue` skill `view` v2 — **nodes are actually clickable now, and a click shows the
  FULL details.** User-reported: nodes weren't clickable/expandable. Three real defects:
  (1) the dpr factor was mixed into both the draw transform and the pointer math, so on a
  Retina screen everything rendered half-size and hit-tests landed off the nodes; (2) the hit
  zone was the small dot only — people click the label text, which started a pan instead;
  (3) details were gated behind two "go deeper" clicks. Now: coordinates are CSS-px with dpr
  isolated to the backing store; the hit zone covers dot + label; click-vs-drag discriminated
  by a 5px movement threshold (pointer-captured); hover shows a pointer cursor + highlight;
  and a single click opens the complete living-knowledge detail (L1 summary · L3 principle +
  transfers · limitation · L5 typed-edge web · verbatim evidence). `window.dmtScreen('name')`
  added for dispatching genuine pointer events in tests — which is how this was verified
  (real `PointerEvent`s on the dot AND on the label, not just the programmatic hook that
  masked the bug in v1).
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
