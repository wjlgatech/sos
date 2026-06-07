The high-velocity agentic shipping loop: **Plan → Code → Validate**, the three-phase lifecycle
Kun Chen uses to ship at volume. Takes a rough idea and drives it to audited PRs by composing
three skills — `lavish` (Plan), `treehouse` (Code), `no-mistakes` (Validate). Project-agnostic
and agent-agnostic: the work units run on Claude, Codex, Hermes, or OpenClaw.

> **This is the parallel gear of `/sos:goal-10x`** (one loop, two gears). Normally you start
> with `/sos:goal-10x`, which escalates here automatically when the work's independent set is
> large. Invoke `/sos:ship-loop` directly only when you're *knowingly* doing bulk, decomposable
> work and don't need the intake/coaching front-end. Both share the same verification-harness
> discovery and the same self-improve tail.

Raw input (a half-formed idea, notes, links, or an existing `specs/*.html`): $ARGUMENTS

---

## The lifecycle

```
  PLAN                    CODE                         VALIDATE
  ────                    ────                         ────────
  lavish                  treehouse                    no-mistakes
  rough idea →            spec → dependency waves →     each PR audited for
  AI-ready HTML spec      N agents in isolated          AI-specific failure
  (queryable, fanned)     worktrees → 1 PR / unit       modes → merge/fix/reject
```

Sequential coding is the bottleneck between an idea and shipped work. This loop removes it:
plan *once* into a queryable spec, fan the spec out *wide*, and gate *every* PR through an audit
tuned for how AI code fails — so the fan-out can run wide safely.

## 0. Orient

State back in ≤5 lines what you understood: the objective, what "done" looks like, the genuine
ambiguities. Skim the repo (`git log --oneline -20`, `CLAUDE.md`/`AGENTS.md`, the files in
play). Resolve real forks with the user **now** — an ambiguity in the plan becomes an ambiguity
in every agent's task.

## 1. PLAN — invoke `lavish`

Turn the input into a structured HTML spec (`specs/<slug>.html`):
- objective + observable done-condition,
- requirements with stable ids, each a single reviewable PR,
- **machine-checkable** acceptance criteria (each with a `data-check` command/test),
- file map (`data-files`) + tests (`data-tests`) per requirement,
- out-of-scope fence, interfaces/contracts,
- **parallelization** tags (`data-parallel-group`, `data-depends`) — maximize the independent set.

Validate it: `bash plugins/sos/skills/lavish/scripts/new-spec.sh --check specs/<slug>.html`.
Do not proceed until the spec is well-formed and complete. (See the `lavish` skill.)

## 2. CODE — invoke `treehouse`

Fan the spec out:
- decompose into work units; build the **wave plan** (topological by `data-depends`) and check
  for same-wave file collisions: `bash plugins/sos/skills/treehouse/scripts/plan-fanout.sh specs/<slug>.html`,
- for each unit in a wave: create an isolated worktree + branch
  (`git worktree add -b agent/<slug>/<REQ-id> ../wt-<REQ-id> <base>`),
- dispatch one agent per unit **concurrently** (in Claude Code: multiple `Agent` calls in one
  message), each given the unit-of-work contract (objective, acceptance, `data-files` it may
  touch, out-of-scope, interfaces) and returning the self-report JSON,
- collect self-reports. Produce **PRs, not merges**. (See the `treehouse` skill.)

Keep concurrency matched to your downstream (review + CI) capacity — start modest, widen as the
validate gate keeps up.

## 3. VALIDATE — invoke `no-mistakes`

Before anything merges, audit **every** PR against its spec unit:
- precondition: that unit's tests are green (this gate is *on top of* tests, not instead of),
- run the checks — symbol reality, spec conformance, scope fence, test integrity, logic/edge
  paths, security, dependency hygiene, debt,
- emit a verdict per PR: **merge** (queue it), **fix** (return `must_fix` to the author agent /
  a fresh treehouse unit, then re-audit), **reject** (re-spec). (See the `no-mistakes` skill.)

## 4. MERGE & CLOSE THE LOOP

Merge `merge`-verdict PRs in **dependency order** (a unit lands only after its `data-depends`
have). Remove finished worktrees (`git worktree remove ../wt-<REQ-id>`). Re-wave any `fix`/`failed`
units with tighter scope. If the repo enforces docs/CHANGELOG, update them.

End every run with: **spec status (units planned/merged/fixed/rejected) · what the fan-out
taught (which checks caught the most, which agent/harness scored best) · one improvement** —
a sharper acceptance check, a tighter scope fence, a new `no-mistakes` check for a failure that
slipped through, or an edit to one of the three skills. That last line is the compounding: the
loop gets stricter and faster every run.

## Notes

- **Agent-agnostic by design.** Each phase is a plain-Markdown contract over plain artifacts
  (HTML spec in, JSON self-report/verdict out). Mix harnesses freely — cheap models for
  mechanical units, stronger ones for hard `div.req`s; record results via this repo's
  `multi_agent_performance` / `self_eval` patterns and feed them back into routing.
- **Don't skip the gate to hit a PR count.** The whole reason the fan-out is safe at volume is
  that `no-mistakes` audits each PR for AI-specific failure modes. Volume without the gate just
  ships AI mistakes faster.
- For a single, obvious change, skip the loop and just make it. This is for fuzzy, multi-part,
  parallelizable work.
