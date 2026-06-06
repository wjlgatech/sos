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
`/sos:goal-10x`, `/sos:living-knowledge`, `/sos:copilotkit`, `/sos:future-self`. Update with
`/plugin marketplace update wjlgatech-plugins`.

> No Anthropic-cloud sync of `~/.claude` exists — this plugin (a git-backed marketplace) is
> the supported way to get the same skills across machines.

## What's inside

| Component                     | Type      | What it does                                                                                                                                                                     |
| ----------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `commands/goal-10x.md`        | command   | `/sos:goal-10x` — project-agnostic objective-driven dev loop: research codebase + user intention, coach via adaptive Q&A + ADEPT, drive to green, self-improve.                  |
| `skills/living-knowledge/`    | skill     | Explain a concept just in time, at the right depth — 4 layers (Sensation→Mechanism→Principle→Expression), real-time mode, name-the-seam, transfer-as-proof.                      |
| `skills/copilotkit/`          | skill     | Integrate CopilotKit (in-app AI copilot UI) into a Next.js app — provider + runtime route + actions, version/bundling gotchas pre-solved.                                        |
| `skills/future-self/`         | skill     | Hardy's "Be Your Future Self Now" framework, operationalized — emergent vs intended self + the gap.                                                                              |
| `scripts/install-doc-sync.sh` | installer | (bundled util, run manually) drops a CHANGELOG + pre-commit docs-sync guard into any git repo.                                                                                   |
| `workflows/goal-10x.js`       | workflow  | (reference, **not** auto-installed — Claude Code can't distribute workflows yet) multi-agent understand→verify→fix→judge→synthesize. Copy into a project's `.claude/workflows/`. |

## Provenance

Built in the DreamMakeTrue Participation Engine and contributed here per the standing rule:
every reusable artifact is published to SOS (agent-monitoring/cost/quality _patterns_ → `src/`
modules; Claude Code _artifacts_ → this plugin) and installed globally for all projects.
