The 10X objective driver: absorb messy input, coach the user while it works, drive every
objective to green, and get better every run. The autonomous core is `/goal all`
(`.claude/commands/goal.md`); this wraps it with input-handling, teaching, and self-improvement.

Raw user input (may be a wall of text, links, half-formed goals): $ARGUMENTS

Read first: `docs/OBJECTIVES.md` (the registry), `scripts/autodrive.py` (the harness),
`scripts/objectives-history.jsonl` (past runs — your memory).

---

## 0. RESEARCH & UNDERSTAND (situational awareness before you act)

Before absorbing the request, build a current picture along three axes. For depth, run the
**multi-agent workflow** `.claude/workflows/goal-10x.js` (parallel researchers + verify +
adversarial judge + synthesis); for a quick turn, do it inline. Either way, ground every
later decision in this:

1. **The whole codebase — past, present, future.**
   - _Past:_ `git log --oneline -30`, and the history of `apps/api/src/services/`.
   - _Future:_ `docs/SPEC.md` (build sequence §8), `docs/OBJECTIVES.md`, `CLAUDE.md`.
   - Know what shipped, what's load-bearing, and what's planned, before you touch anything.

2. **Recent roadblocks & lessons learned.**
   - `CHANGELOG.md` → the `### Investigated / Rejected` entries are the hard-won lessons
     (e.g. "Sonnet slower than Opus — measure, don't assume"; "background the Graphiti fold";
     "placeholder speakers slip past structural gates"). Don't relitigate a settled call.
   - Recent `fix:`/`perf:` commits + `memory/` for project-specific gotchas.

3. **The user's intention — inferred from behavior + their avatar.**
   - _Behavior:_ what does Paul's recent work-shape imply he's really after this session?
   - _Avatar:_ read `/Users/openclaw/Documents/Projects/super-u` — the "future-you /
     current-you" product. If a user avatar exists there, use it to infer intention; if not
     (it's early-stage), infer from super-u's design + note the cross-project thread:
     dreammaketrue's `future_self.py` becoming-engine and super-u are the **same future-self
     vision** in two repos. Serve that larger intention, not just the literal ask.

Open the run by stating, in 3-4 lines, what you understood across these three — so Paul sees
you have the context before you drive.

---

## 1. ABSORB messy / massive input (normalize before doing anything)

The user may paste a lot at once — multiple URLs, transcripts, vague objectives, mixed
requests. Do NOT act on the raw dump. First parse it into a plan:

- **Sources** — every URL or pasted transcript/text to run through the engine.
- **Explicit objectives** — anything they literally asked to verify/build.
- **Implied objectives** — goals their text implies but didn't name (map to OBJECTIVES.md ids).
- **Intent** — what "done" looks like for them this session.
- **Ambiguities** — the few genuine forks you can't resolve from the text + the code.

Then **reflect it back in ≤6 lines** ("Here's what I parsed: 2 sources, objectives S1–S4
on each, 1 fork on which speaker is primary — correct me") so they can fix it in one reply.
If the dump is huge, summarize; never silently drop parts of it.

## 2. COACH adaptively (teach as you run — don't just execute)

You are also the user's tutor for their own engine. Two tools:

- **Adaptive Q&A.** Ask clarifying questions ONLY at genuine forks, max 2, via
  AskUserQuestion. Never interrogate; if the text + code answer it, decide and move on.
  Calibrate to the user: moving fast → fewer questions; exploring → offer the choice.
- **ADEPT explanation** for each stage as it runs, so they learn the engine (invoke the
  `living-knowledge` skill's method): **A**nalogy → **D**iagram/sketch → concrete
  **E**xample from THIS run → **P**lain-English → **T**echnical. Keep each to a few lines;
  name the analogy's breaking point. Adapt depth: compress to Analogy+Plain when they're
  moving fast; go Technical when they ask "why" or "how".
  - e.g. Stage 2 person-map: "Analogy: like building a chess engine's model of a specific
    grandmaster — not 'a smart player' but _their_ openings, blind spots, risk appetite.
    Example: this run gave Chamath 'asymmetric bets' w/ 2 verbatim quotes. Breaks down
    when: a speaker has thin public corpus → we tag [INFERRED]."

## 3. DRIVE to green (the autonomous loop — inherits `/goal all`)

Run the loop from `.claude/commands/goal.md` → "autonomous mode":
`autodrive.py` → read ❌ → fix the named service file → re-run → loop until all machine
objectives ✅ (stop after the same failure 3×; never fake a green). Narrate progress with
the ADEPT explanations above. Surface the 🔴 judgment gates (J5.1/J5.2) with the real
artifact and let the user score them — coach what a good answer looks like, don't answer for them.

## 4. SELF-IMPROVE (the system is better after this run than before)

Every run leaves the engine sharper:

1. **Read the history** (`scripts/objectives-history.jsonl`). Flag any objective that is
   **flaky** (passes some runs, fails others) — that's a threshold or prompt problem, not
   a one-off. e.g. "S2.f darwin score has been 69.8 / 71 / 68 — the gate is borderline."
2. **Propose one concrete improvement per run**, then apply it with consent:
   - a NEW objective you discovered the engine should guarantee → add a check to
     `autodrive.py` + a row to `OBJECTIVES.md`.
   - a flaky/ wrong threshold → tune it (in code) with the evidence from history.
   - a recurring fix → write it as a memory (`memory/`) so future sessions skip the dig.
3. **Improve THIS command.** If the coaching missed, an input shape wasn't handled, or a
   question was noise — edit this file (`.claude/commands/goal-10x.md`) so the next run is
   better. Note the change in your final report.
4. If you changed feature code, the doc-sync hook applies (CHANGELOG + docs).

End every run with: **objective table** · **what you taught** · **the one improvement you
made or propose**. That last line is the compounding — the loop teaching itself.
