---
name: viral-loop
description: Closed-loop viral marketing — loop engineering applied to media content. Runs MAKE → AUTO-REVIEW (rubric-scored, iterate to bar) → HUMAN GATE → PUBLISH+ENGAGE (1-click intents, drafted comment replies) → MEASURE → LEARN, with the measurement/scoring half backed by sos's marketing-eval engine (computed scores, never vibes) when available. Use when the user wants to promote/announce/viralize content ("write a post about X", "reply to these comments", "log this post's numbers", "what have we learned about our posts", "run the viral loop"). Drafts everything, sends NOTHING — auto-posting/auto-DM/auto-reply bots violate platform ToS; a human always owns Send.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash(python *), Bash(node *), Bash(make *)
---

# Skill: /viral-loop — closed-loop viral marketing

Loop engineering applied to marketing: every stage that can be honestly automated is
(drafting, reviewing, measuring, learning); the one that can't stays human (publishing,
replying). The loop closes on **measurement → learning**, so every post starts smarter
than the last. It is the marketing instance of sos's own DISCOVER → SCORE → RECOMMEND →
REPORT pattern — self-aware (it scores its own output), self-healing (below-bar drafts
iterate or die honestly), self-improving (lessons are banked and constrain the next MAKE).

## Hard rules (non-negotiable)

1. **Draft, never send.** Never auto-post, auto-DM, auto-comment, or auto-reply on any
   platform — not via API, not via browser automation (LinkedIn/X ToS prohibit it).
   Output is always paste-ready copy or a 1-click share-intent URL the human clicks.
2. **No invented facts.** Every claim traces to the product, the repo, or a real
   citation. Illustrative stories are framed as illustrative. Unsourceable stat → cut.
3. **Metrics are computed, never claimed.** Scores come from the marketing-eval engine
   or arithmetic on numbers the human pasted from platform analytics. Never estimate.
4. **Learnings must be earned.** A rule needs ≥3 posts of evidence (cited by id);
   below that it's a hypothesis with a named next test.

## The engine seam (use it when present)

If the repo has sos's marketing-eval engine (`src/marketing_eval.py` — check for it),
MEASURE and part of AUTO-REVIEW are **its** job, not prose:

```bash
python src/__main__.py marketing-discover      # DISCOVER: scan marketing/ for content
python src/__main__.py marketing-score         # SCORE: weighted composite 0-100 (code, not vibes)
python src/__main__.py marketing-publish --content-id <id> --url <live-url>
python src/__main__.py marketing-metrics --content-id <id> --impressions N --engagements N
python src/__main__.py marketing-eval --markdown   # REPORT: the full scorecard
python src/__main__.py marketing-recommend     # RECOMMEND: feeds LEARN
```

No engine (a plain content repo)? Fall back to a `marketing/ledger.md` table (one row
per artifact: id · date · platform · hook · impressions · reactions · comments · shares ·
clicks · conversions · notes-with-computed-rates) + `marketing/LEARNINGS.md`.

## The loop — run the stage the user is at

### 1 · MAKE (auto)
Read the learnings file FIRST — active rules constrain the draft. Draft the artifact +
per-platform copy (X ≤280 chars, URLs billed at 23; LinkedIn long-form or feed post;
YouTube description; IG caption): ONE hook in line 1, ONE ask, real links, grounded in
the actual repo/product — read it, don't remember it.

### 2 · AUTO-REVIEW (auto — iterate until ≥4.0/5, max 3 revisions)
Score 1–5 each, average: **Hook** (would a scroller stop at line 1?) · **Specificity**
(concrete nouns/numbers; zero "synergy") · **Honesty** (claims sourced, limits stated) ·
**CTA** (exactly one, low-friction) · **Fit** (platform-native, length limits met).
Where the engine exists, also run `marketing-score` on the draft file (its
content_quality sub-score is rule-based: word count, CTA, link — computed). Report the
scorecard honestly; below bar after 3 revisions → name the structural weakness, don't
inflate.

### 3 · HUMAN GATE (always human)
Final draft + scorecard + assets → the human edits, approves, or kills. Never proceed
without an explicit go.

### 4 · PUBLISH + ENGAGE (assisted)
Paste-ready copy + share-intent URLs (`twitter.com/intent/tweet?text=…`,
`linkedin.com/sharing/share-offsite/?url=…`). On publish, record it
(`marketing-publish` or a ledger row). When the human pastes incoming comments, draft a
reply per comment in their voice — answer, thank specifics, never argue, route qualified
people to the outreach playbook if one exists. Batch the replies. **The human sends.**

### 5 · MEASURE (auto, on pasted numbers)
At a consistent checkpoint (48h): `marketing-metrics --content-id <id> --impressions …`
(or append the ledger row) and regenerate the report (`marketing-eval --markdown`).
Rates and grades are the engine's/arithmetic's — never estimated.

### 6 · LEARN (auto)
`marketing-recommend` (or compare the new row against the ledger) → extract ≤2 lessons:
`RULE (n≥3): <what> — evidence: <ids>` or `HYPOTHESIS (n=1–2): <what> — test next by:
<concrete variation>`. Promote/demote on evidence; prune contradicted rules. End with
the one-line compounding takeaway: what the next post starts with that this one didn't.

## Cadence

On "run the viral loop" with no stage named: check for published content missing
metrics (→ §5), then a pending hypothesis (→ test it in §1), else ask what artifact to
promote. One full cycle per artifact; never queue unattended sends.

## Reference deployment

The agentic-portfolio repo runs this loop end-to-end: `docs/marketing/` (VIRAL-LOOP.md,
ledger, learnings, multi-brand media art-boards) — a working example of the no-engine
fallback plus token-driven share assets.
