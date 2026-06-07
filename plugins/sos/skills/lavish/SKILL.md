---
name: lavish
description: "Turn a rough idea into an AI-ready spec authored as structured HTML — the Plan phase of a high-velocity agentic loop. Use BEFORE writing code, when a task is fuzzy, multi-part, or about to be handed to one or more coding agents (Claude, Codex, Hermes, OpenClaw). Triggers on 'plan this', 'write a spec', 'turn this idea into a task', 'scope this feature', or any messy dump that needs to become buildable work. Produces a typed HTML spec — objective, requirements with ids, machine-checkable acceptance criteria, a file map, interfaces, out-of-scope, and parallelization hints — that downstream agents parse far more reliably than prose or Markdown. NOT for one-line changes you'd just do directly."
argument-hint: "[the rough idea, or path to notes/links to turn into a spec]"
allowed-tools: Read, Grep, Glob, Edit, Write, WebSearch, WebFetch, Bash(bash *)
metadata:
  type: workflow
  phase: plan
  portable: true
  cross-agent: true
---

# Skill: Lavish — rough idea → AI-ready HTML spec

Lavish is the **Plan** phase. It converts a half-formed idea into a **structured HTML
specification** that coding agents can execute with minimal ambiguity. The output is not
documentation for humans to admire — it is a *machine contract* the **Code** phase
(`treehouse`) fans out and the **Validate** phase (`no-mistakes`) audits against.

> Provenance: distilled from Kun Chen's `lavish` (an HTML editor for visual planning).
> The thesis below — **HTML beats Markdown for specs** — is the load-bearing idea.

## Why HTML, not Markdown, for a spec

A Markdown spec is a *flat blob of prose*. An agent re-derives structure from it every time,
and re-derives it slightly differently each time — which requirement is this acceptance
criterion under? Is "the parser" the same component two sections down? That ambiguity is
where AI implementations drift from intent.

HTML is a **typed tree**, so the structure is *in the artifact*, not re-inferred:

| Need | Markdown | HTML |
| --- | --- | --- |
| Stable identity for a requirement | a heading you must string-match | `id="REQ-3"` — addressable |
| "this AC belongs to that requirement" | inferred from indentation | nesting + `data-req="REQ-3"` — explicit |
| State (done / blocked / in-progress) | a `[ ]` checkbox, untyped | `data-status="blocked"` — queryable |
| Link requirement ↔ file ↔ test | prose | `data-files`, `data-tests` attributes |
| "these units are independent" | a sentence an agent may miss | `data-parallel-group` — a directive |
| Machine-checkable acceptance | prose to interpret | discrete `<li data-ac data-check="…">` |

The payoff: an agent (or a fleet of them) reads the same structure you wrote, every time. The
spec becomes *queryable* — `treehouse` can select all units with no unmet `data-depends`,
`no-mistakes` can diff the PR against the exact `data-ac` list. Prose can't be queried.

## Procedure

1. **Locate intent (do this first).** Read the dump end to end. Research the codebase the way
   the work demands — `git log --oneline -20`, the repo's `CLAUDE.md`/`AGENTS.md`, the files
   the change will touch. State back in ≤5 lines: the objective, what "done" looks like, and
   the genuine ambiguities. Resolve forks with the user *now* — a spec built on a guess fans
   out the guess to every agent.

2. **Scaffold the HTML spec.** Run `scripts/new-spec.sh <slug>` to emit a typed template into
   `specs/<slug>.html` (or write it by hand from the schema below). One spec = one objective.

3. **Fill the typed regions** (schema below). The discipline that matters:
   - Every requirement gets a stable `id` (`REQ-1`, `REQ-2`, …).
   - Every acceptance criterion is **machine-checkable** — phrased as something a test or a
     command could decide, with `data-check` naming *how* (a test path, a command, a grep).
     "Login works" is not an AC. "`pytest tests/test_auth.py::test_login` passes" is.
   - Map each requirement to the **files** it touches (`data-files`) and the **tests** that
     prove it (`data-tests`). This is what makes the spec queryable downstream.
   - Declare **out-of-scope** explicitly. AI agents over-build; the fence prevents scope creep
     (and gives `no-mistakes` a list to flag violations against).

4. **Mark parallelization — the key output for Treehouse.** Partition requirements into
   **work units** that are independent enough to build *simultaneously in isolated worktrees*.
   - Tag each unit with `data-parallel-group="A"` (same group = safe to run concurrently).
   - Tag real ordering with `data-depends="REQ-1"` (must merge after REQ-1).
   - A good spec maximizes the independent set. If everything depends on everything, the
     plan is too coupled to fan out — split the objective or sequence it, and say so.

5. **Self-check, then hand off.** Validate the spec is well-formed and complete
   (`scripts/new-spec.sh --check specs/<slug>.html`). Then hand to `treehouse` (Code) →
   `no-mistakes` (Validate). The three compose into the ship loop (`/sos:ship-loop`).

## The spec schema

```html
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>SPEC: {slug}</title></head>
<body>
<article class="spec" data-slug="{slug}" data-status="draft">

  <section data-spec="objective">
    <h1>{one sentence: what & why}</h1>
    <p data-done-when>{the observable condition that means "done"}</p>
  </section>

  <section data-spec="context">
    <ul>
      <li data-fact>{a constraint, existing module, or decision an agent must respect}</li>
    </ul>
  </section>

  <section data-spec="requirements">
    <div class="req" id="REQ-1"
         data-status="todo"
         data-parallel-group="A"
         data-depends=""
         data-files="src/foo.py"
         data-tests="tests/test_foo.py">
      <h2>{what this unit must do}</h2>
      <ul class="acceptance">
        <li data-ac data-check="pytest tests/test_foo.py::test_x">{checkable criterion}</li>
        <li data-ac data-check="grep -q 'X' src/foo.py">{another checkable criterion}</li>
      </ul>
    </div>
    <!-- REQ-2 in data-parallel-group="A" with data-depends="" → runs alongside REQ-1
         REQ-3 with data-depends="REQ-1" → merges only after REQ-1 lands -->
  </section>

  <section data-spec="interfaces">
    <pre data-contract>{signatures / schemas / API shapes agents must conform to}</pre>
  </section>

  <section data-spec="out-of-scope">
    <ul><li data-no>{explicitly NOT part of this work — agents must not build it}</li></ul>
  </section>

</article>
</body>
</html>
```

## Cross-agent contract

This skill is plain Markdown + plain HTML — **harness-agnostic on purpose**. The HTML spec is
the interchange format any agent can consume:

- **Claude Code:** invoked as `/sos:lavish`; the spec lands in `specs/` for `treehouse`.
- **Codex / Hermes / OpenClaw / any harness:** point the agent at `specs/<slug>.html` (or
  reference this `SKILL.md` from the project's `AGENTS.md`). The `data-*` attributes are a
  stable contract — an agent selects work with a CSS/attribute query, no NLP guessing.

The whole reason to author in HTML is that *every* agent, not just the one that wrote it,
parses the same structure.

## Anti-patterns (self-check before handing off)

1. **Prose acceptance criteria.** "It should be fast / intuitive / robust." If no command or
   test can decide it, it's a wish, not an AC. Either make it checkable or move it to a human
   judgment note — don't pretend an agent can verify it.
2. **One giant requirement.** A unit so big it can't be one PR can't be fanned out. Split until
   each `div.req` is a single, reviewable change.
3. **Fake parallelism.** Tagging coupled units the same `data-parallel-group` so they *look*
   independent. They'll collide in the worktrees. Only group units that truly don't share state.
4. **No out-of-scope fence.** Omitting it invites every agent to gold-plate. The fence is cheap
   and saves the most review time.
5. **Planning what you should just do.** A one-file, one-line change doesn't need a spec. Lavish
   is for work that's fuzzy, multi-part, or about to be parallelized.
6. **Spec built on an unresolved fork.** You guessed at a genuine ambiguity instead of asking.
   The guess now propagates to every agent in the fan-out. Resolve forks in Step 1.

## Where this fits

`lavish` (Plan) → `treehouse` (Code, parallel agents) → `no-mistakes` (Validate). Run the whole
arc with **`/sos:ship-loop`**. Lavish's only job is to make the next two phases *deterministic*:
a queryable spec that fans out cleanly and audits exactly.
