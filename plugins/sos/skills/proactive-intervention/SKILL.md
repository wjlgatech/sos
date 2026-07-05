---
name: proactive-intervention
description: >-
  Notice recurring friction — a repeated instruction, redone rework, a by-hand step, a
  decision that will recur — and turn it into a PERMANENT solution (a global rule, a skill,
  a hook, or a memory) without waiting to be asked. Use when Paul says "make this a rule /
  a habit / permanent", "so I don't repeat myself", "proactively propose", or when you catch
  yourself doing something already done before. The always-on version lives in
  ~/.claude/instructions-paul-wu.md ("PROACTIVE OBSERVATION & INTERVENTION"); this skill is
  the detailed how + a place to tune it.
---

# Proactive observation & intervention — turn repetition into a rule

**The one idea:** if Paul has to say it twice, a rule should have said it for him. Silent
repetition is the defect. Your job is to *catch the pattern and codify it* — before he asks
again. This is always on; you don't need to be invoked to do it. Invoke this skill to review
or refine the behavior.

## The loop (OBSERVE → CLASSIFY → PLACE → APPLY → SURFACE)

### 1. OBSERVE — what counts as a trigger
- **Repeated instruction** — said >1× (this session, a prior one, or a saved memory). The
  strongest signal. Example this was built from: "update README + linked docs in the anyagent
  pattern / add an infographic / propose it, don't wait" — said across several turns.
- **Rework / friction** — a fix you redid, a manual step that could be a script/hook/template,
  a thing that broke the same way twice.
- **Recurring decision** — a convention, threshold, default, or naming choice you'll face again.
- **Cross-task lesson** — something that would change your behavior on an *unrelated* task.

### 2. CLASSIFY — backbone vs attachment (the deciding rule, from anyagent)
- Changes behavior on an **unrelated** task (a CLI, a pipeline, a UI alike) → **backbone**:
  codify in the always-on global instructions.
- Names a **specific technology or domain** → **attachment**: a skill or a project memory,
  revealed on demand — don't bloat the always-on layer.

### 3. PLACE — pick the SMALLEST permanent home by leverage
| The lesson is… | Home | Reaches |
|---|---|---|
| An always-on behavior | `~/.claude/instructions-paul-wu.md` or `~/.claude/CLAUDE.md` | every project, every machine (synced via `wjlgatech/dotfiles`) |
| A situational how-to | `~/.claude/skills/<name>/SKILL.md` | invoked on demand |
| A mechanical guarantee | a git hook / `scripts/*.sh` (he already runs doc-sync hooks) | enforced, can't be forgotten |
| A one-project fact | that project's `memory/` or `CLAUDE.md`/`AGENTS.md` | that repo only |

Prefer the **narrowest** home that still fires when needed. A global rule that only matters for
one repo is bloat; a per-repo memory for a universal habit is a leak.

### 4. APPLY — draft it and put it in place (standing authorization: "no waiting")
Write the rule/skill/hook/memory now. `~/.claude` is a git repo — safe and reversible. Keep the
addition tight and in Paul's voice (concrete-first, two-rail, no ceremony). Mechanical enforcement
beats a written rule when it's available (a hook that blocks > a sentence that reminds).

### 5. SURFACE — show, don't ask-permission-to-notice
Report in ≤6 lines: the pattern you caught, the home you chose, the diff, and how to revert. You
don't ask before *noticing* — you do show what you changed so he stays in control. Commit the
`~/.claude` change so it syncs.

## Guardrails
- **Don't over-fire.** One-offs aren't patterns. Wait for the *second* occurrence (or an explicit
  "make this a habit") before codifying — except when he names it outright.
- **Smallest home wins.** Don't promote a domain-specific trick into the always-on layer.
- **Keep the always-on layer lean.** If two rules overlap, merge them; dedupe on sight (the
  anyagent reflect-loop discipline: promotion threshold, capped renders, no singleton bloat).
- **Reversible + visible.** Every codification is a git-tracked diff you showed him.

## Self-check (run at session close, ~1 line)
*"What did Paul say this session that a rule should have said for him?"* If the answer isn't
"nothing," you have one more intervention to make before you sign off.
