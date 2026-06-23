The 10x objective driver (global, project-agnostic): absorb messy input, research the
codebase + the user, drive every objective to green, coach while doing it, and get better
each run. Works in ANY repo — it discovers the project's own objectives + verification
harness rather than assuming one. (A project may ship its own `.claude/commands/goal-10x.md`
that overrides this with project-specific wiring — e.g. dreammaketrue's autodrive harness.)

**One loop, two gears.** This is the single front door. It drives work to green in a
**sequential gear** by default, and shifts into a **parallel gear** — the `/sos:ship-loop`
fan-out (`lavish` → `treehouse` → `no-mistakes`) — when the work decomposes into many
independent units. You pick the objective; step 3 picks the gear. Orthogonally, within
either gear it can drive **inline** or delegate to the **`/ce-plan` → `/ce-work` engine**
when a durable, traceable decision artifact pays off (step 3) — keeping this loop's
coaching (step 2) and self-improve (step 4) wrapper around it.

Raw user input (may be a wall of text, links, half-formed goals): $ARGUMENTS

---

## 0. RESEARCH & UNDERSTAND (situational awareness first)

Build a current picture along three axes before acting:

1. **The codebase — past, present, future.** `git log --oneline -30`; the repo's
   `README`, `docs/`, and agent guide (`CLAUDE.md` or `AGENTS.md`); recent diffs. Know what
   shipped, what's load-bearing, what's planned.
2. **Recent roadblocks & lessons.** `CHANGELOG.md` (esp. any "Investigated / Rejected"),
   recent `fix:`/`perf:` commits, and any project `memory/`. Don't relitigate settled calls.
3. **The user's intention — from behavior + avatar.** What does the user's recent work-shape
   imply they're really after? If they keep a personal "future-self / current-self" avatar
   (e.g. in a `super-u`-style repo), read it to infer intention. Serve the larger goal, not
   just the literal ask.

Open with 3–4 lines stating what you understood across these three.

## 1. ABSORB messy / massive input

Parse a big dump into: **sources** (URLs/text), **explicit objectives**, **implied
objectives**, **intent** (what "done" looks like), **ambiguities** (genuine forks). Reflect
it back in ≤6 lines so the user can correct in one reply. Never silently drop parts.

## 2. COACH adaptively (teach while you work)

- **Adaptive Q&A:** ask clarifying questions ONLY at genuine forks (≤2, via AskUserQuestion).
- **ADEPT explanations** per stage so the user learns the system — invoke the
  **`living-knowledge`** skill (global): Analogy → Diagram → concrete Example → Plain → Tech;
  name the analogy's breaking point. Compress when they move fast; go deep when they ask why.

## 3. DRIVE to green — pick the gear, then drive

**First, pick the execution gear from the *shape* of the work (don't guess — let it read itself):**

- **Sequential gear (default).** Small, coupled, or still-fuzzy work — roughly one PR's
  worth. Drive it yourself in this repo/branch (the loop below).
- **Parallel gear (`/sos:ship-loop`).** Multi-part work that decomposes into independent
  units. Author a `lavish` HTML spec first; its **independent-set size is the dial** — if
  many requirements have no unmet `data-depends` (run `plan-fanout.sh`), shift into the
  parallel gear: fan out via `treehouse` (one agent / worktree / PR) and gate **every** PR
  through `no-mistakes`. If everything turns out coupled, fall back to the sequential gear.
  The full procedure lives in `/sos:ship-loop` — invoke it as the CODE stage here.

**Then pick the engine — drive inline, or delegate to a plan+execute engine when rigor pays off:**

- **Inline (default).** Drive the loop yourself in this repo/branch. Right for small,
  coupled, or fuzzy work where a durable plan document would be ceremony.
- **`/ce-plan` → `/ce-work` engine.** When the work is non-trivial AND benefits from a
  durable, traceable decision artifact — team handoff, multi-agent execution, long-lived
  work, or anything you'll cross-reference in PRs/issues — hand your step 0–2 research to
  **`/ce-plan`** as origin input. It produces guardrails (decisions, scope, atomic units
  with stable **U-IDs**, per-unit test scenarios, risks) without pre-writing the code; then
  **`/ce-work`** executes against them — idempotent (no silent reimplementation),
  worktree-isolated, gated through tests + review to a reviewed PR. This composes with
  either gear: run one coupled unit inline-style, or fan its U-IDs out through the parallel
  gear. The engine owns plan+execute; you keep the coaching (step 2) and self-improve
  (step 4) wrapper. Don't reach for it on small/non-software work — that's what inline is for.

**The verification source is the same across gears and engines — discover it, DO NOT hardcode one:**

1. **A project objective registry + runner** — e.g. `docs/OBJECTIVES.md` + a harness script,
   or a project-local `/goal` command. Use it as the source of truth.
2. **Else the project's own check/test command** — detect from the repo:
   `make check` (Makefile) · `pnpm check` / `pnpm test` / `npm test` (package.json) ·
   `pytest` / `ruff` (pyproject.toml) · `cargo test` · `go test ./...`, etc.
3. **Else co-define 3–7 verifiable objectives with the user**, then check them.

**Sequential gear loop:** run → read each failure → fix the named file → re-run → repeat
until green, OR stop after the **same failure 3×** and escalate with what you tried.

**Parallel gear loop:** merge `merge`-verdict PRs in dependency order, re-wave `fix`/`failed`
units with tighter scope. Here `no-mistakes` runs **on top of** the discovered test harness
(not instead of it) — tests must be green before the audit.

Either way: never fake a green; an honest ❌ beats a bad fix. Surface human-judgment gates
(the things a check can't score) to the user with the real artifact — don't self-answer them.

## 4. SELF-IMPROVE (the system is sharper after this run)

Both gears converge here — this is the shared self-improve tail. After the run: flag anything
**flaky** (passes some runs, fails others — a threshold/prompt problem). Propose ONE concrete
improvement and apply with consent — a new objective + check, a tuned threshold, a recurring
fix saved to `memory/`, or an edit to this command itself. In the parallel gear, also fold in
what the fan-out taught (which `no-mistakes` checks caught the most, which agent/harness
scored best) and record it via `multi_agent_performance` / `self_eval`. If you ran the
`/ce-plan` → `/ce-work` engine, also run **`/ce-compound`** to capture reusable learnings
(bugs hit, patterns set, conventions adopted) into `docs/solutions/`, then fold the headline
lesson into `memory/` so the next `goal-10x` run benefits too. If you changed feature
code and the repo enforces it, update CHANGELOG + docs.

End every run with: **objective status · what you taught · the one improvement you made or
propose.** That last line is the compounding.
