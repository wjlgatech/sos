---
name: future-self
description: Apply Dr. Benjamin Hardy's "Be Your Future Self Now" framework — design, measure, and close the gap to an intended future self. Use when building becoming/growth features, goal systems, self-modeling, or any product that moves a person toward who they want to become.
source: "Be Your Future Self Now — Dr. Benjamin Hardy (Hay House, 2022), 230pp / ~52k words"
metadata:
  type: reference
  portable: true
---

# Skill: Be Your Future Self Now (operationalized)

Distilled framework + how to apply it in software. Portable across projects.

## The core idea

> **Your future self drives your present.** You are not a fixed personality moving away
> from your past; you are pulled forward by the version of you that you can vividly see.
> The future self is the **organizing principle** of who you become — and it is *designed*,
> not discovered. Most people have a **random future self** because they never author it
> and are unaware of the environment producing it.

Two foundational distinctions that power everything below:
- **Gain vs. Gap** (from Hardy's companion book): measure progress **backward** from where
  you started (the Gain → confidence, fuel) AND forward to the ideal (the Gap → direction).
  Measuring *only* against the ideal is demoralizing. You need both axes.
- **Emergent vs. Intended future self:** your environment is *already* producing a future
  self (the byproduct). The intended one is the one you author. The whole game is closing
  emergent → intended.

## Part 1 — 7 Threats (the diagnostic: what pulls you off course)

Use these as **detectors**, not just warnings. Each is an observable failure mode.

1. **No hope in the future → the present loses meaning.** (Detect: no articulated future self.)
2. **A reactive narrative about your past stunts your future.** (Detect: backward-looking self-talk.)
3. **Unawareness of your environment creates a random future self.** Environment is the byproduct. (Detect: intended ≠ emergent.)
4. **Disconnection from your future self → myopic, short-term decisions.** (Detect: present-bias in choices.)
5. **Urgent battles and small goals keep you stuck.** (Detect: goal-shrinkage, busywork.)
6. **Not being in the arena is failing by default.** (Detect: avoidance, no attempts.)
7. **Success is often the catalyst for failure.** (Detect: comfort/plateau after a win.)

## Part 2 — 7 Truths (the design principles)

1. **Your future drives your present** — design backward from the future self.
2. **Your future self is different than you expect** — bigger/stranger; don't anchor on today.
3. **Your future self is the Pied Piper** — make it vivid and it *pulls* you (motivation = clarity).
4. **You become what you actively measure** — the future self defines the metrics. ⟵ key for product.
5. **Failing as your future self > succeeding as your current self** — reward direction, not safety.
6. **Success = being true to your future self, nothing else** — its standards override external ones.
7. **Your view of God/meaning impacts your future self** — anchor in a transcendent purpose.

## Part 3 — 7 Steps (the conversation / workflow spine)

A becoming session should walk these in order:

1. **Clarify your contextual purpose** — the "why" for this season.
2. **Eliminate lesser goals** — subtract; most goals are noise (Who Not How / 80-20).
3. **Elevate from needing → wanting → knowing** — move identity from scarcity to certainty.
4. **Ask for exactly what you want** — specificity; name the concrete outcome.
5. **Automate and systemize your future self** — environment + systems do the work, not willpower.
6. **Schedule your future self** — put the future self on the calendar before the urgent fills it.
7. **Aggressively complete imperfect work** — shipping beats polishing; reps in the arena.

## How to apply it (software patterns)

- **Author the future self as a proposal, then let the user edit.** Don't impose; generate
  (current self + admired traits) → human approves/edits. (Truth #2 + agency.)
- **Make the future self define the metrics.** Ask "what would you be measuring if you were
  already this person?" Those become the dashboard. (Truth #4.)
- **Show BOTH axes.** Gain (distance from past-you → inner reward) + Gap (distance to
  future-you → direction). Never only the Gap. (Gain vs Gap.)
- **Run the growth loop as a threat scan.** Each cadence, detect *which of the 7 threats* is
  active from real behavior, not just "ahead/behind." Diagnosis > a speedometer.
- **Mirror the environment.** Infer the *emergent* future self from real interaction history;
  surface the gap to the *intended* one. (Threat #3.)
- **Reward arena-entry and aimed-failure**, not just outcomes. (Truth #5, Threat #6.)
- **Structure becoming sessions on the 7 Steps**; output an artifact per step (purpose
  statement, cut-list, schedule, first imperfect ship).
- **Vividness is the lever.** The more concrete/sensory the future self, the stronger the
  pull — invest in making it real (voice, day-in-the-life, a letter from future self). (Truth #3.)

## Anti-patterns
- A flattering future self (becomes a hype-man; must be demanding + grounded in real limits).
- A future self that's a generic "better you" (must be specific, measured, environment-aware).
- Measuring only the Gap (demoralizing) or only the Gain (complacent).
- A one-shot vision with no cadence/re-measure (the future self is a *practice*, not a poster).

## Where this is used in DreamMakeTrue
Powers the **future-self avatar** (current corpus + admired heroes' models → editable proposal),
the **growth loop** (weekly/monthly/quarterly threat scan + Gain/Gap roadmap), and the
**becoming room** (you + future-you + heroes walking the 7 Steps → expression artifacts).
Ingested into the graph under `group_id="future-self-hardy"` for retrieval. See
`docs/COPILOT_UI_SPEC.md`, `docs/SURFACES.md`.
