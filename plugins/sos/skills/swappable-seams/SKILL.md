---
name: swappable-seams
description: 'Enforce OOP swappability AND close the build-measure-feedback loop — the
  discipline HarnessX demonstrates (agent = model.agentic(harness); behavior as composable,
  swappable Processors that observe→adapt→evolve). A dependency you can replace without
  editing its callers is a *seam*; seams are what make a system testable, adaptable, and
  self-improving. Use when: writing or reviewing code that touches an external dependency
  (LLM/model, storage, retrieval, transport, telemetry, payment, queue); designing how a new
  module plugs into an existing system; auditing a codebase for hardcoding / "every module
  must be swappable"; deciding whether to adopt or build on a framework; closing a goal-10x
  run (did the change go through a seam, and does it measure itself?). NOT for: a true
  one-off script or spike with no second implementation in sight; a stable-for-years
  dependency at no volatility boundary (a premature seam is dead cost); when a recorded
  decision (ADR/YAGNI) has consciously deferred the seam — honor it, do not relitigate.'
metadata:
  type: technique
  portable: true
  ground_truth: expert_judged
---

# Skill: Swappable seams + the closed loop (the harness discipline)

A dependency you can replace **without editing its callers** is a *seam*. Seams are the
unit of swappability — and swappability is the precondition for the closed loop that lets a
system measure itself and improve. HarnessX makes this its whole thesis:
`agent = model.agentic(harness)` separates *what model* from *how it behaves*, expresses
behavior as **Processors** that compose with `|`, then **observes → adapts → evolves** over
those swappable units. You can only adapt and evolve what you can swap. The two halves are
one idea: **seams enable loops.**

## Core mechanism (why it works)

Every system has *volatile* dependencies (things that change: providers, storage backends,
ranking algorithms, judges) and *stable* ones. A seam is an **injected interface** at a
volatility boundary — a Protocol / ABC / callback / factory — so a caller depends on the
*shape* of a thing, not its identity. Three things prove a seam is real, not decorative:

1. **An interface** the callers depend on (`Protocol`, ABC, `Callable` type, trait).
2. **A selector** that picks the implementation from config/env, not a hardcoded `import`
   (a factory: `make_x(settings) -> XProtocol`).
3. **A second body** behind it — a test fake at minimum, ideally a real alternative. *A
   seam with exactly one implementation and no fake is just indirection.*

The closed loop then rides on the seams: **Compose** (behavior as swappable units) →
**Adapt** (observe each run's outcome against a check) → **Evolve** (feed that signal into
the next configuration). In a work loop (e.g. goal-10x's drive-to-green) this means: every
change ships *with the check that scores it*, and the score chooses the next move. Code that
runs but cannot be measured is an open loop — it cannot get better on its own.

## When to use

- Touching any external dependency: model/LLM, DB/storage, retrieval/embeddings, HTTP
  transport, telemetry sink, queue, payment, auth provider.
- Designing how a new capability plugs in (new layer, plugin, processor, target).
- Auditing for hardcoding, or answering "should every module be swappable here?"
- Deciding whether to adopt / build on a framework (is it a *consumer* you feed, or a
  *foundation* you couple to? prefer the exporter/adapter over the dependency).
- Closing a build loop: before declaring green, check the seam + the measurement.

## When NOT to use

- A genuine one-off (script, spike, throwaway) with no realistic second implementation.
- A dependency at no volatility boundary and stable for years — a seam there is pure cost
  (indirection, a dead abstraction, a leaky interface frozen too early).
- When an ADR / documented YAGNI has *consciously* deferred the seam. A recorded "we hardcode
  files until a loop demands a store" is a correct decision, not debt — honor it.
- As a reason to add a layer "to be safe." Safety is the test fake, not the abstraction.

## Honest edges — where this skill fails

- **It over-abstracts in the wrong hands.** "Every module swappable" as dogma manufactures
  premature interfaces, indirection, and config sprawl. The skill's whole value is knowing
  *which* boundaries earn a seam — get that wrong and it's net-negative.
- **It can't tell you the volatility boundary for you** — that's a judgment about what will
  actually change, which needs domain knowledge the skill doesn't carry.
- **The closed loop needs a cheap, honest check.** Where ground truth is expensive or absent
  (taste, novel research), "measure every change" degrades into vanity metrics. Name the
  ground-truth source first (mechanical / expert-judged / real-world) or the loop is fake.
- **Framework-adoption calls are economic, not architectural.** This skill says "feed the
  harness, don't couple to it" — but a real per-token-cost or multi-tenant trigger can flip
  that. Defer to a recorded decision with revisit triggers over this skill's default.

If the task touches one of these, SAY SO instead of forcing the skill.

## How to tell it apart

Similar to: dependency injection, hexagonal/ports-and-adapters, SOLID's DIP, plugin
architectures, the strategy pattern.
This skill is the *judgment layer* on top of all of them: those tell you *how* to build a
seam; this tells you **whether a given boundary deserves one**, and ties the seam to a
**measurement loop** (compose→adapt→evolve) so swappability buys self-improvement, not just
tidiness. DIP says "depend on abstractions"; this says "depend on abstractions *at real
volatility boundaries, proven by a second body, in service of a feedback loop* — and nowhere
else."

## Explain it (ADEPT lenses)

- **Analogy:** A pro climber racks **swappable** protection — same harness loop, any cam fits
  the crack in front of them — *and* dogs the route, logging each fall to choose the next
  beta. Swappable gear (seams) makes the send-measure-adjust loop possible. Breaking point:
  rock is passive; software dependencies have behavior and contracts, so a bad interface
  (a cam that won't seat) silently fails under load — the interface itself is load-bearing.
- **Plain:** Put the things that change behind a plug. Don't add plugs where nothing changes.
  Make every change report a number, and let the number pick what you do next.
- **Example:** super-u's LLM seam — `CompleteFn` Protocol + `make_llm_client(settings)` factory
  + env-selected Anthropic/OpenAI bodies + test fakes. One file changes to add a provider;
  tests inject deterministic fakes; eval scorecards feed the next extraction. That's a seam
  closing a loop. Its storage layer is *deliberately hardcoded to files* (recorded YAGNI) —
  correct, because no second body and no volatility yet.
- **Technical:** At each external boundary, define the interface (`Protocol`/ABC/`Callable`),
  resolve the impl through a composition root / factory keyed on config, and require a fake
  for tests. Compose behavior as units (pipeline/processor/strategy). Instrument each unit's
  outcome against a declared ground truth; route that signal back into selection (config
  search, threshold tuning, next-iteration choice). Seam first, loop second, dogma never.

## Apply procedure (for an agent)

1. **Judge FIT first** against the rules above: `use | partial | dont-use` — name the
   specific boundary and cite the use_when / dont_use_when / edge that decided it. If a
   recorded ADR/YAGNI already settled this boundary, that's `dont-use` — honor it.
2. **Find the volatility boundaries** in the change: list each external dependency it touches
   and ask "will this plausibly get a second implementation, or need a test fake?" Only those
   are seam candidates. Be explicit about the ones you're *choosing not to seam* and why.
3. **For each real seam:** interface + config-keyed factory + a fake. No fake ⇒ no seam yet.
4. **Close the loop:** the change must ship with the check that scores it, and you must name
   the ground-truth source. If you can't measure it, say so — that's an open loop, flag it.
5. **Framework boundary:** if a framework is in play, prefer *feeding it through an
   adapter/exporter* over coupling to it; couple only against a recorded economic trigger.
6. Verify with the discernment check below — a choice under ambiguity, never recall.

## Discernment check

You're reviewing a PR that wraps the project's single, stable config-file loader behind a new
`ConfigSource` interface with one implementation and no test fake, "so we can swap it later" —
and separately leaves a third-party payment SDK called directly inline in four handlers. Which
of the two needs a seam, which doesn't, and what's the tell?

**Pass condition:** Names the **payment SDK** as the seam that's missing (real volatility
boundary: providers change, it needs a test fake to avoid live calls, multiple call sites) and
the **config loader** as a premature seam to *remove* (one stable impl, no second body, no
boundary — indirection masquerading as flexibility). The tell is "second body + volatility +
a loop that needs it," not "could we abstract this." Bonus: notes the inline payment calls also
block the closed loop (can't test or measure outcomes without a fake).
(ground truth: expert_judged, closed by the reviewer's architectural judgment)
