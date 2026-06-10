# Changelog

All notable changes are logged here — for humans **and** agents.
Format follows [Keep a Changelog](https://keepachangelog.com/). Newest first.

## [Unreleased]

### Added

- `skillfy` skill: compress ANY source/expertise into a bounded, verifiable skill —
  atomic Skill schema with honest `not_good_at` edges, masked by-hand worksheet,
  mechanical checker, discernment check, teach-back. Two modes: served (drives a
  running super-u API, incl. `POST /skillfy/extract` and the dreammaketrue
  `POST /creator/skillfy` bridge; free via NVIDIA NIM) or standalone (any agent —
  Claude, Hermes, Codex — applies the method and emits super-u-compatible
  `skill.yaml`). Mirrors super-u's Skillify→Skillfy rename.

### Added

- `living-repo` skill: **"✨ Ask the field"** — the generated graph webapp is now
  conversational, powered by NVIDIA's free NIM API. Client-side retrieval (token-overlap
  scoring over nodes, top-10 + 1-hop edges) builds a grounded context; the answer must
  cite node names, rendered as chips that jump-select the node on the map. BYO free key
  (build.nvidia.com), stored only in the visitor's localStorage; calls go through
  `free-llm/nim-bridge/` (deployed: https://nim-bridge.vercel.app — keyless, stores
  nothing) because integrate.api.nvidia.com only allows CORS from build.nvidia.com
  (verified via preflight probe). Model picker: GLM 5.1 / DeepSeek v4 flash / Kimi K2.6.
  Error paths verified live in-browser: bad key → "NVIDIA rejected the key", 429 → wait
  message. First deployment: the awesome-auto-ai-research map.

### Changed

- **`nvidia-free-llm` skill renamed to `free-llm`** and upgraded with THE FALLBACK-CHAIN
  RULE (Paul's standing policy): any agent wired to a free LLM gets the survival chain
  **NIM → local Ollama → OpenRouter → Anthropic/OpenAI**, with probe commands per tier
  (dead links in a chain are theater), the exact verified Hermes `fallback_providers`
  YAML (local Ollama via `provider: custom` + explicit base_url — confirmed honored by
  `try_activate_fallback`), and the hard-won Hermes gotchas (dict-form entries only;
  gateway loads the chain at startup → restart; `provider: auto`/None aux+cron follow the
  main provider — pin them). Why: a live 429 from NIM's 40 req/min ceiling killed a
  desktop chat mid-turn; the chain makes throttling survivable. `nim-bridge/` (Vercel
  CORS proxy for browser apps, from the living-repo work) now ships inside the skill.

### Fixed

- `nvidia-free-llm` `nim.py test`: no longer crashes on reasoning-style replies —
  gpt-oss/nemotron-class models put output in `reasoning_content` (with `content` None or
  absent when the token budget is eaten by thinking). Now falls back
  content→reasoning_content and bumps max_tokens 40→200. Found live: gpt-oss-120b answered
  in 0.6s but `test` raised TypeError/KeyError on its shape.

### Added

- `plugins/sos/skills/living-repo/` — **awesome-list → living knowledge system.**
  `awesome_kg.py`: deterministic, stdlib-only compiler from README GFM tables to a typed
  knowledge graph (paper/repo/person/lab/talk/benchmark nodes; authored_by/has_code/
  member_of/part_of/builds_on edges; bold-mention person resolution "S. Hu" ≈ "Shengran
  Hu"; log-scaled confidence from citations/stars) + a self-contained interactive
  force-graph HTML (canvas, zero external scripts — works from file:// and GitHub Pages).
  Optional `nim-enrich` proposes lineage edges via the free NVIDIA NIM API; a hand-written
  `enrichments.json` overlay carries curator knowledge across regenerations.
  `check_freshness.py`: concurrent link prober (HEAD→GET fallback, bot-walled domains are
  WARN not DEAD) + a weekly GitHub Action template that opens an issue on dead links.
  Why: deterministic parse = zero tokens, CI-safe, no hallucinated nodes — LLM extraction
  via the engine's 7B backup was tried and rejected (hallucinated a "Karpathy" node).
  First deployment: wjlgatech/awesome-auto-ai-research (139 nodes · 246 edges; the
  freshness check found 5 dead links in its first run, incl. a placeholder
  `acl-long.xxx` URL). Plugin bumped to 1.1.0; plugin README table also backfilled with
  the previously-undocumented knowledge-graph / dreammaketrue / nvidia-free-llm rows.

### Changed

- `nvidia-free-llm` skill: Hermes wiring upgraded from "Custom provider + base_url" to the
  verified NATIVE path — Hermes ships a `nvidia` provider (`agent/models_dev.py`: env
  `NVIDIA_API_KEY`, base URL pre-baked, 94 NIM models in its models.dev registry), so setup
  is just key-in-env + `model.provider: nvidia`. Why: fact-checked against the Hermes
  codebase; the Custom route was unnecessary indirection.

### Added

- `plugins/sos/skills/nvidia-free-llm/` — **NVIDIA's free NIM API as a skill.** 120 hosted
  frontier models behind one OpenAI-compatible endpoint, free key from build.nvidia.com
  (~40 req/min, ~1yr). SKILL.md documents verified model ids — the viral post's GLM/Kimi ids
  were WRONG (`zhipuai/glm-5.1` → `z-ai/glm-5.1`, `moonshot-ai/kimi-2.5` →
  `moonshotai/kimi-k2.6`; catalog listable without a key, fact-checked live) — plus wiring
  for Hermes / Cursor / OpenCode / DreamMakeTrue (which gained a one-click "NVIDIA NIM
  (free)" Settings preset). `scripts/nim.py` (zero-dep): `list [filter]` (live catalog),
  `test <model>` (one tiny completion), `pick` (recommended id per role). Guidance: verify
  ids before wiring (they churn), respect 40 req/min, keep a fallback.
- `dreammaketrue` artifact voice: diagnostic failure messages. Investigated a "could not
  transcribe" report: OS-level mic capture verified healthy (sounddevice RMS/peak test) and
  whisper transcribed a live room recording — so empty transcripts mean the BROWSER stream
  was silent or wordless. The failure message now reports KB + seconds and uses the opus
  silence ratio (<3KB/s ≈ silent stream) to say either "Chrome recorded SILENCE — check the
  address-bar mic device (BlackHole vs MacBook Pro Microphone)" or "audio captured, no words
  recognized." 2048-byte header-only guard keeps its own message.
- `dreammaketrue` artifact: **voice input** (tap 🎙 to record, tap ⏹ to stop → engine
  faster-whisper STT → auto-asks) and **screen-aware questions** — every ask now carries
  `viewContext()` (map vs infographic + selected node + depth), so "explain this idea" means
  the visible one. Mic limits surfaced honestly in-UI: browsers allow the mic only on
  HTTPS/localhost, so the plain-http LAN link offers text-only on the phone (the message
  points at the tunnel option); iOS Safari records mp4/aac — whisper decodes it fine.
- `dreammaketrue` skill: after publish, the FILE copy of an artifact is re-baked with the
  engine's **LAN url** (not localhost) — a downloaded artifact opened on a phone now reaches
  the engine over Wi-Fi (pairs with the engine's null-origin CORS fix). The served copy is
  untouched (always same-origin). `file_engine` reported in the result.
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
