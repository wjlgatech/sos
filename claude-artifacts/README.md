# Claude Code Artifacts

Reusable **Claude Code** artifacts (skills, workflows, slash commands, installers) developed
across SOS-adjacent projects, kept here so they don't get stranded in a single product repo.
These are markdown/JS — they drop straight into a Claude Code project (`.claude/`) or
`~/.claude/`, no Python required. (The Python self-monitoring _patterns_ live in `src/`.)

## Layout

```
claude-artifacts/
├── commands/      slash commands  → .claude/commands/
├── workflows/     multi-agent workflows → .claude/workflows/
├── skills/        skills (dir or .md) → .claude/skills/ or ~/.claude/skills/
└── scripts/       portable installers/utilities
```

## Contents

| Artifact                      | Type      | What it does                                                                                                                                                                                 |
| ----------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `commands/goal.md`            | command   | `/goal <stage>` — verify one objective stage; `/goal all` drives all objectives to green autonomously (verify → fix → loop).                                                                 |
| `commands/goal-10x.md`        | command   | `/goal-10x` — the 10x driver: absorbs messy input, **researches the codebase + user intention**, coaches via adaptive Q&A + ADEPT, drives to green, and self-improves each run.              |
| `workflows/goal-10x.js`       | workflow  | Multi-agent: Understand (∥ researchers) → Verify → Fix-in-worktrees → adversarial Judge → Synthesize a situational-awareness report.                                                         |
| `skills/living-knowledge/`    | skill     | Explain a concept just in time, at just the right depth — 4 layers (Sensation→Mechanism→Principle→Expression), real-time mode, name-the-seam, transfer-to-another-domain as the proof.       |
| `skills/copilotkit/`          | skill     | Integrate CopilotKit (in-app AI copilot UI) into a Next.js app — provider + runtime route + actions, version/bundling gotchas pre-solved.                                                    |
| `skills/future-self.md`       | skill     | Hardy's "Be Your Future Self Now" framework, operationalized — emergent vs intended self + the gap.                                                                                          |
| `scripts/install-doc-sync.sh` | installer | Drops a CHANGELOG + `scripts/changelog.sh` + a pre-commit guard into any git repo (stack-aware: husky / plain hook / pre-commit snippet) so feature changes always carry a log + doc update. |

## Install

Copy an artifact into the target project's `.claude/` (or `~/.claude/` for global skills):

```bash
cp -R claude-artifacts/skills/copilotkit ~/.claude/skills/
cp claude-artifacts/commands/goal-10x.md  <your-project>/.claude/commands/
cp claude-artifacts/workflows/goal-10x.js <your-project>/.claude/workflows/
sh claude-artifacts/scripts/install-doc-sync.sh   # run from inside a git repo
```

## Provenance

Built in the DreamMakeTrue Participation Engine and contributed here per the standing rule:
every reusable artifact gets published to SOS — agent-monitoring/cost/quality _patterns_ as
`src/` modules, Claude Code _artifacts_ here.
