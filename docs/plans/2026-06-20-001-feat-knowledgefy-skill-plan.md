---
title: "feat: /knowledgefy — a focused, first-class slash-command skill for the kgfy one-shot"
type: feat
date: 2026-06-20
depth: lightweight
status: planned
origin: none (solo /ce-plan)
---

# feat: `/knowledgefy` skill

**Target repo:** `sos` (`~/Documents/Projects/sos`). All paths below are repo-relative to **sos**,
not to the dreammaketrue repo this was planned from.

## Summary

Add a new, focused **`knowledgefy`** skill to the sos plugin that gives users a discoverable,
explicit **`/knowledgefy <source>`** command: turn ANY source (GitHub repo, web page,
YouTube/podcast, PDF, local file, folder, or pasted text) into a self-contained **interactive
living-knowledge HTML artifact** (Map + Ask tabs + a NotebookLM-style infographic) and surface
its shareable URL. It is a **thin wrapper** over the existing `dmt.py kgfy` one-shot — no
pipeline, engine, or `dmt.py` reimplementation, and no second copy of the script.

## Problem Frame

`kgfy` already works, but today it's only reachable through the **broad, model-auto-triggered
`dreammaketrue` skill** (whose description spans knowledge maps, avatar conversation, express,
voice, etc.). There is no single-purpose, typeable entry point for the highest-value one-shot —
"turn this into an interactive knowledge graph." A user who just wants that has to know the
`dreammaketrue` skill exists and phrase it so the model picks the kgfy path. A dedicated
`/knowledgefy` command makes the one-shot first-class and discoverable, without duplicating the
engine work.

## Goals & Success Criteria

- **G1** — `/knowledgefy <source>` produces the interactive HTML artifact and prints its served
  URL (plus the LAN/phone URL) for any source `dmt.py kgfy` already accepts.
- **G2 — DRY.** Reuses the existing `dmt.py kgfy`; no copy of the pipeline. Resolves `dmt.py`
  from the installed `dreammaketrue` sibling skill.
- **G3 — Clean separation.** Explicit `/knowledgefy` is the primary entry; the skill's
  description is narrow enough that the model does not double-fire it alongside `dreammaketrue`'s
  kgfy trigger.
- **G4 — Resilient.** A down engine self-heals (auto-start), inherited from `dmt.py`.
- **G5 — Discoverable.** The skill is registered (auto-discovered from `skills/`) and the
  plugin/CHANGELOG/README reflect it.

## Key Technical Decisions

- **KTD1 — Thin wrapper, not reimplementation.** The SKILL.md operating procedure shells out to
  `python3 <dmt.py> kgfy <source> [--title …]` and surfaces the returned `served_url` /
  `phone_url`. No new engine routes, no new `dmt.py` subcommand — `cmd_kgfy` already publishes via
  `/v1/engine/artifacts` and returns both URLs.
- **KTD2 — `dmt.py` resolution mirrors the dreammaketrue skill.** `dreammaketrue/SKILL.md`
  already documents `DMT=~/.claude/skills/dreammaketrue/scripts/dmt.py` (or the skill's own
  `scripts/` dir). `knowledgefy` resolves the same script across install layouts (installed
  skills dir, plugin-cache marketplace path, sibling `../dreammaketrue/scripts/dmt.py`) and fails
  with a clear, actionable message if absent. No symlink, no vendored copy.
- **KTD3 — Narrow trigger + explicit NOT-for.** The description leads with `/knowledgefy` and the
  kgfy one-shot, and explicitly defers the broad flows: conversation/avatars/express → use
  `dreammaketrue`; multi-source topic/persona research → `knowledge-graph`; awesome-list repos →
  `living-repo`; one-paragraph explainers → `living-knowledge`. This is what keeps it from
  colliding with the existing kgfy auto-trigger (G3).
- **KTD4 — Sources are inherited, not re-scoped.** v1 accepts exactly what `dmt.py kgfy` handles
  today (repo / url / video / podcast / file via engine extractors / folder / text). No new
  source types in this skill.

## Implementation Units

### U1. Author the `knowledgefy` SKILL.md (the skill itself)

- **Goal:** A focused skill that runs the kgfy one-shot and surfaces the artifact URL.
- **Requirements:** G1, G2, G3, G4.
- **Dependencies:** none.
- **Files:** `plugins/sos/skills/knowledgefy/SKILL.md` (create).
- **Approach:** Frontmatter mirroring sibling skills — `name: knowledgefy`; a tight `description`
  leading with the `/knowledgefy` one-shot + triggers ("kgfy/KG-fy/make a knowledge graph of
  <repo/video/PDF/folder>") and the KTD3 NOT-for clause; `argument-hint: "<repo | url | video |
pdf | folder | "pasted text">"`; `allowed-tools: Bash, Read, Write`; `metadata` (type
  integration, portable, cross-agent, source: dreammaketrue). Body = a short operating procedure:
  (1) resolve `dmt.py` per KTD2, (2) run `kgfy <source>` (note it auto-starts a down engine and
  emits the Map/Ask artifact + infographic), (3) print the served + phone URLs and offer to open
  them. Keep it compact — mirror `living-knowledge`'s shape, not the long `dreammaketrue` one.
- **Patterns to follow:** `plugins/sos/skills/living-knowledge/SKILL.md` (compact structure);
  `plugins/sos/skills/dreammaketrue/SKILL.md` (frontmatter fields, the `DMT=` resolution snippet,
  the kgfy row in its command table).
- **Test scenarios (verified via U2's smoke, since a SKILL.md is instructions not code):**
  - Happy: invoking the documented command on a small text source yields an HTML artifact + a
    printed `served_url`.
  - Disambiguation: the description's NOT-for clause names dreammaketrue / knowledge-graph /
    living-repo / living-knowledge so the model routes a broad "talk to / express" request away
    from knowledgefy.
- **Verification:** The skill file exists, is valid frontmatter, and its procedure runs the kgfy
  command end-to-end (U2).

### U2. `dmt.py` resolution + end-to-end smoke

- **Goal:** Prove the wrapper actually produces an artifact, and that `dmt.py` is found across
  install layouts (or fails loudly).
- **Requirements:** G1, G2, G4.
- **Dependencies:** U1.
- **Files:** `plugins/sos/skills/knowledgefy/scripts/knowledgefy_smoke.sh` (create — a thin smoke
  that resolves `dmt.py` and runs `kgfy` on a tiny fixture); optionally a `scripts/` resolver
  helper only if the SKILL.md inline resolution proves too long.
- **Approach:** The smoke resolves `dmt.py` (same candidate-path order the SKILL.md documents),
  runs `kgfy` on a small pasted-text/markdown fixture, and asserts a non-empty HTML artifact and a
  `served_url`/`local_url` in the output. Reuses the already-working `cmd_kgfy`; this unit adds
  no engine logic.
- **Patterns to follow:** `plugins/sos/skills/dreammaketrue/scripts/dmt.py` (`cmd_kgfy` output
  shape: `served_url` / `phone_url`); the engine self-heal already in `dmt.py` (`_ensure_engine`).
- **Test scenarios:**
  - Happy: `kgfy` on a ~1-paragraph text fixture → exit 0, an `.html` file written, `served_url`
    present in stdout/JSON.
  - Error: engine unreachable → `dmt.py` auto-starts it (inherited) and still completes; if it
    genuinely can't, the smoke surfaces the engine error rather than a silent empty artifact.
  - Edge: `dmt.py` not present at any candidate path → the resolver prints a clear "install the
    dreammaketrue skill / set DMT=…" message and exits non-zero (no Python traceback).
- **Verification:** Running the smoke locally produces an artifact + URL; removing `dmt.py` from
  the path yields the actionable not-found message, not a stack trace.

### U3. Register + docs sync

- **Goal:** Make the skill discoverable and keep the plugin docs honest.
- **Requirements:** G5.
- **Dependencies:** U1.
- **Files:** `plugins/sos/.claude-plugin/plugin.json` (add `knowledgefy` to the prose
  `description`, bump `version`), `CHANGELOG.md` (new entry), `README.md` (skill list/table),
  and the root marketplace manifest **if** one lists skills explicitly (verify at execution).
- **Approach:** Skills are auto-discovered from `plugins/sos/skills/`, so no array edit is
  required for the skill to load — but the human-facing surfaces (plugin description, README skill
  list, CHANGELOG) should name it so it's findable and the release is logged. Confirm whether a
  root `.claude-plugin/marketplace.json` enumerates skills; if so, add it there too.
- **Patterns to follow:** the existing skill entries in `plugins/sos/.claude-plugin/plugin.json`
  `description` and the `README.md` skill list; `CHANGELOG.md` format.
- **Test scenarios:** `Test expectation: none — docs/manifest only.` Verify `plugin.json` remains
  valid JSON and the new skill auto-loads (appears in the available-skills list / `/knowledgefy`
  resolves).
- **Verification:** `plugin.json` parses; `/knowledgefy` is offered as a command; CHANGELOG +
  README mention the skill.

## Scope Boundaries

**In scope:** a new `knowledgefy` SKILL.md wrapping `dmt.py kgfy`, a resolution + smoke test, and
docs/registration sync — all in the **sos** repo.

### Outside this skill's identity (non-goals)

- Any change to `dmt.py`'s pipeline, the DreamMakeTrue engine, or the kgfy renderer.
- The broad conversation / avatar / express / voice flows — those remain the `dreammaketrue`
  skill's job (knowledgefy's NOT-for points there).
- New source types beyond what `dmt.py kgfy` already accepts.

### Deferred to follow-up work

- A dedicated `dmt.py kgfy` flag or output mode if `/knowledgefy` ever needs a different artifact
  shape than the shared one-shot.
- Broad model-auto-triggering (held back intentionally per G3 to avoid double-firing with
  `dreammaketrue`).

## Open Questions (resolve at execution)

- **Q1:** Exact on-disk path of `dmt.py` on a fresh install (installed skills dir vs plugin
  cache). Resolve by mirroring the `dreammaketrue` skill's own candidate-path resolution.
- **Q2:** Does a root `.claude-plugin/marketplace.json` enumerate skills (needing an explicit
  add), or is the per-plugin `plugin.json` + auto-discovery sufficient? Check in U3.

## Sources & Research

- `plugins/sos/skills/dreammaketrue/scripts/dmt.py` — `cmd_kgfy` (kgfy one-shot: any source →
  tabbed living-knowledge HTML + infographic, publishes via engine `/v1/engine/artifacts`,
  returns `served_url`/`phone_url`; engine self-heal in `_ensure_engine`).
- `plugins/sos/skills/dreammaketrue/SKILL.md` — frontmatter fields, the `DMT=` resolution
  snippet, and the kgfy command-table row (the capability being surfaced).
- `plugins/sos/skills/living-knowledge/SKILL.md` — compact single-purpose skill to mirror in
  shape/length.
- `plugins/sos/.claude-plugin/plugin.json` — skills are auto-discovered; the description lists
  them in prose (sync target for U3).
- No external research (pure local mirror pattern); no `docs/solutions/` learnings in sos for this.
