---
name: no-mistakes
description: "Audit AI-generated code for the mistakes AI makes — the Validate phase of a high-velocity agentic loop. Use AFTER tests pass and BEFORE merging any agent-produced PR, especially when reviewing many PRs from a parallel fan-out (treehouse) faster than a human can read them. Triggers on 'review this PR', 'validate this change', 'is this AI code safe to merge', 'audit this diff', or as the merge gate in the ship loop. Checks for the failure modes specific to AI code — hallucinated APIs, spec violations / silent scope creep, tests that assert nothing or mirror the bug, missing error paths, security naivety, dependency drift — and returns a merge / fix / reject verdict with evidence per check. NOT a replacement for unit tests; it runs as the final audit layer on top of them."
argument-hint: "[PR number, branch, or diff to audit — plus the lavish spec it should satisfy]"
allowed-tools: Read, Grep, Glob, Bash(git *), Bash(grep *), Bash(rg *), Bash(pytest *), Bash(ruff *), Bash(mypy *)
metadata:
  type: workflow
  phase: validate
  portable: true
  cross-agent: true
---

# Skill: No Mistakes — audit AI code before it merges

No Mistakes is the **Validate** phase. It is an **AI code-review audit layer** tuned for the
way *AI-generated* code fails — which is differently from how human code fails. It replaces the
human as the *bottleneck* reviewer of high-volume agent output, not the *judgment* of whether
code is correct. The output is a verdict per PR: **merge**, **fix**, or **reject**, with
evidence.

> Provenance: distilled from Kun Chen's `no-mistakes` (AI-driven review of AI code), the gate
> that let him stop manually reviewing every PR. Two load-bearing rules:
> **it is NOT a substitute for unit tests**, and it runs **after** tests pass, as the final
> audit before merge.

## Why AI code needs a different review

Human review evolved to catch human mistakes — typos, off-by-one, forgotten edge case. AI
makes *those too*, but it also fails in ways that look *more* convincing than human error:
fluent, plausible, confidently wrong. The dangerous ones:

- **Hallucinated surface** — calls a function/flag/field/import that doesn't exist, or no
  longer does. Reads perfectly; fails (or worse, silently no-ops) at runtime.
- **Plausible-but-wrong logic** — the shape is right, a condition is inverted or an edge
  mishandled. Passes a happy-path test that was *also* generated to match the wrong behavior.
- **Silent scope creep** — built more than the spec asked (gold-plating) or touched files it
  shouldn't. Each extra line is unrequested risk.
- **Theater tests** — tests that assert nothing, assert a tautology, mock the thing under test,
  or were written to match the bug. Green CI that proves nothing.
- **Security naivety** — string-built SQL, unsanitized input, secrets in code, permissive
  defaults. AI reaches for the simplest thing that runs.
- **Dependency drift** — adds a package, pins a wrong/yanked version, or imports something not
  in the manifest.

`no-mistakes` is a checklist *targeted at exactly these*, because generic "looks good" review
slides right past fluent-but-wrong code.

## Hard preconditions (do not skip)

1. **Tests already pass.** This is an audit *on top of* a green suite, not instead of one. If
   tests are red, that's the author's job, not this gate's. (NOT a replacement for unit tests.)
2. **The spec is in hand.** You audit the diff *against* its `lavish` `div.req`: the `data-ac`
   list, `data-files`, `data-no`. Without the spec you can only guess intent — which is the
   thing this gate refuses to do.

## The checks

Run every check against `(diff, spec-unit)`. Each yields PASS / WARN / FAIL with evidence.
(These are the audit's substance — Kun's "series of specific checks" before merge.)

1. **Symbol reality.** Every function, method, import, flag, env var, and config key the diff
   *introduces a call to* — does it actually exist? Grep the codebase/manifest/stdlib for each
   new reference. A call to something undefined → **FAIL** (hallucination).

2. **Spec conformance.** Does the diff satisfy *each* `data-ac` for this unit — and is each
   `data-check` command actually green when run? Missing AC → **FAIL**.

3. **Scope fence.** Are changed files ⊆ the unit's `data-files`? Did it build anything in the
   spec's `data-no`? Files outside the set, or out-of-scope features → **FAIL** (scope creep).

4. **Test integrity.** For each new/changed test: does it actually *assert* a meaningful
   condition? Would it *fail* if the code under test were broken (mentally mutate a line — does
   a test catch it)? Does it mock the very thing it claims to verify? Tautologies, assert-free
   tests, self-mocking → **FAIL** (theater).

5. **Logic & edge paths.** Walk the changed logic against the AC. Inverted conditions, off-by-one,
   unhandled None/empty/error returns, swallowed exceptions, missing the non-happy path → **WARN**
   or **FAIL** depending on whether an AC covers it.

6. **Security.** Injection (string-built SQL/shell), unsanitized external input, hardcoded
   secrets/keys, overly permissive defaults, unsafe deserialization → **FAIL** on anything
   exploitable, **WARN** on hardening gaps.

7. **Dependency hygiene.** New imports/packages present in the manifest? Versions sane (not
   yanked, not a guessed number)? Lockfile consistent? Drift → **WARN/FAIL**.

8. **Debt & coherence.** Dead code, copy-paste drift, duplicated logic that already exists in
   the repo, naming/idiom inconsistent with the surrounding file → **WARN** (the kind of debt
   AI accretes at volume).

## Verdict

Aggregate the checks into one decision:

- **MERGE** — all checks PASS (warnings allowed if minor and noted). Safe for the queue.
- **FIX** — one or more FAILs that are *bounded and clear*. Return the specific failures so the
  author agent (or a fresh treehouse unit) can correct them; re-audit after.
- **REJECT** — fundamental: wrong approach, hallucinated core, security hole in the critical
  path, or theater tests on the main behavior. Don't patch — re-spec or re-do.

Output is structured so it can drive automation (auto-request-changes, auto-merge on MERGE):

```json
{
  "pr": "REQ-3",
  "verdict": "merge | fix | reject",
  "checks": [
    { "name": "symbol-reality", "result": "fail",
      "evidence": "src/auth.py:42 calls jwt.decode_safe() — no such symbol in pyjwt" }
  ],
  "must_fix": ["src/auth.py:42 — jwt.decode_safe does not exist; use jwt.decode(..., verify=True)"],
  "notes": "tests green, but test_login mocks verify_token, so it proves nothing about REQ-3"
}
```

## Cross-agent contract

The audit takes `(diff, spec-unit)` → verdict JSON, so any harness can run it or consume it:

- **Claude Code:** `/sos:no-mistakes` on a PR/branch; emits the verdict and (in `ship-loop`)
  gates the merge.
- **Codex / Hermes / OpenClaw / CI:** run the checks as a step that parses the spec and the
  diff and emits the verdict JSON — wire `verdict == "merge"` to auto-merge, `fix` to
  request-changes (with `must_fix` as the comment), `reject` to close + re-spec. Pairs with this
  repo's `src/self_eval.py` gate-runner pattern (real tools, parsed output, weighted verdict).

## Anti-patterns (self-check before issuing a verdict)

1. **Reviewing without the spec.** Then you're guessing intent — exactly the human-judgment
   call this gate must not fake. Get the `div.req` first.
2. **Trusting green CI.** Green proves the tests pass, not that the tests *test* anything (check
   #4 exists because of this). AI writes tests that match its own bug.
3. **Becoming the test suite.** Re-deriving correctness by hand for things a unit test should
   own. This is an *audit on top of* tests — if a behavior needs ongoing protection, the verdict
   is "add a test," not "I checked it once."
4. **Rubber-stamping at volume.** The point of the gate is to be *fast and strict*, not fast and
   lenient. A MERGE that skipped checks to keep the queue moving ships the mistake.
5. **Patching a REJECT.** Fundamentally wrong code gets re-spec'd, not nudged. Bandaging an AI's
   wrong approach compounds debt.
6. **Vague FIX.** "Looks off" isn't actionable. Every FAIL needs file:line + the concrete fix in
   `must_fix`, so an agent can correct it without a human in the loop.

## Where this fits

`lavish` (Plan) → `treehouse` (Code) → **`no-mistakes` (Validate)**. Run the full arc with
**`/sos:ship-loop`**. No Mistakes is the merge gate: it lets the fan-out run wide *because* every
PR is audited for AI-specific failure modes before it lands — never as a replacement for the
unit tests underneath it.
