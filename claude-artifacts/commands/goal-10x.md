The 10x objective driver (global, project-agnostic): absorb messy input, research the
codebase + the user, drive every objective to green, coach while doing it, and get better
each run. Works in ANY repo — it discovers the project's own objectives + verification
harness rather than assuming one. (A project may ship its own `.claude/commands/goal-10x.md`
that overrides this with project-specific wiring — e.g. dreammaketrue's autodrive harness.)

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

## 3. DRIVE to green (discover this project's objectives + harness)

Find the verification source, in priority order — DO NOT hardcode one:

1. **A project objective registry + runner** — e.g. `docs/OBJECTIVES.md` + a harness script,
   or a project-local `/goal` command. Use it as the source of truth.
2. **Else the project's own check/test command** — detect from the repo:
   `make check` (Makefile) · `pnpm check` / `pnpm test` / `npm test` (package.json) ·
   `pytest` / `ruff` (pyproject.toml) · `cargo test` · `go test ./...`, etc.
3. **Else co-define 3–7 verifiable objectives with the user**, then check them.

Loop: run → read each failure → fix the named file → re-run → repeat until green, OR stop
after the **same failure 3×** and escalate with what you tried. Never fake a green; an honest
❌ beats a bad fix. Surface human-judgment gates (the things a check can't score) to the user
with the real artifact — don't self-answer them.

## 4. SELF-IMPROVE (the system is sharper after this run)

After the run: flag anything **flaky** (passes some runs, fails others — a threshold/prompt
problem). Propose ONE concrete improvement and apply with consent — a new objective + check,
a tuned threshold, a recurring fix saved to `memory/`, or an edit to this command itself.
If you changed feature code and the repo enforces it, update CHANGELOG + docs.

End every run with: **objective status · what you taught · the one improvement you made or
propose.** That last line is the compounding.
