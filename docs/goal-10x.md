# `/goal-10x` — the 10x objective driver

> Absorb a messy goal, research the codebase **and** you, drive every objective to a
> verified green, coach while doing it, and leave the system sharper than you found it —
> in **any** repo, with **one** command.

`/goal-10x` is not a code generator and not a chat assistant. It's a **closed-loop
controller for shipping**: you give it the target, it figures out the route, drives to a
checkable finish line, and upgrades its own tooling on the way out.

---

## TL;DR

| Question | Answer |
|---|---|
| What is it? | One front-door command that runs a 5-stage loop: research → absorb → coach → drive-to-green → self-improve |
| What's the core idea? | Treat shipping as a feedback loop. The **only** definition of done is a check that passes. The system compounds each run. |
| When do I reach for it? | Any objective in any repo — fuzzy or sharp, one file or fifty, software or not |
| When do I *not*? | A single trivial edit you'd just type yourself; or when you want a one-off answer, not a driven loop |
| How does it scale up? | Two **gears** (sequential / parallel fan-out) and an optional **engine** (`/ce-plan`→`/ce-work`) — it picks them from the shape of the work |
| What do I get at the end? | `objective status · what it taught you · the one improvement it made` |

---

## First principles — why it exists

Three beliefs, and everything else follows from them.

1. **Act on a map, not a guess.** Most agent failures are *situational*, not logical — they
   relitigate a settled decision, edit a load-bearing file blind, or solve the literal ask
   while missing the real one. So stage 0 builds a map first: the codebase's past/present/
   future, the recent roadblocks, and *your* intent. No keystroke before the map.

2. **Verification is the only truth.** "Looks done" is a lie an agent tells confidently. The
   loop's finish line is always an *executable check the project already trusts* —
   discovered, never invented. It runs → reads the failure → fixes the named file → re-runs.
   An honest ❌ beats a fake ✅, every time. (Think of it as a PID controller: the test
   suite is the sensor, the diff is the actuator, "green" is the setpoint.)

3. **A run should compound.** A tool that solves today's task and learns nothing is linear.
   `/goal-10x` ends every run by making *one* concrete improvement — a new check, a tuned
   threshold, a saved fix, even an edit to itself. Linear effort, compounding capability.
   This is the "10x": not 10× faster typing, but a system that bends its own curve upward.

> **The analogy, and where it breaks.** It's a thermostat for code: sense (tests) → compare
> to setpoint (green) → actuate (edit) → repeat. Where the analogy *breaks*: a thermostat
> can't change what "comfortable" means, but stage 4 can change the setpoint itself — adding
> objectives and checks the project didn't have. The controller rewrites its own reference.

---

## The mechanism — one loop, five stages

You invoke it with a raw dump. It runs these in order, narrating as it goes.

```
0. RESEARCH ── 1. ABSORB ── 2. COACH ── 3. DRIVE TO GREEN ── 4. SELF-IMPROVE
   (build a       (parse the    (teach +      (pick gear+engine,    (one concrete
    3-axis map)    mess into     ask only at    discover the check,   upgrade; the
                   objectives)   real forks)    loop until green)     compounding)
```

**0 · Research & understand.** Three axes before acting: the **codebase** (`git log`, README,
agent guide, recent diffs — what shipped, what's load-bearing), **recent roadblocks**
(CHANGELOG, `fix:`/`perf:` commits, `memory/` — so it won't re-litigate settled calls), and
**your intent** (what your recent work-shape implies you're really after). Opens with 3–4
lines of what it understood.

**1 · Absorb.** Parses your wall of text/links/half-goals into: *sources, explicit
objectives, implied objectives, what "done" looks like, genuine ambiguities*. Reflects it
back in ≤6 lines so you can correct in one reply. Nothing is silently dropped.

**2 · Coach.** Asks clarifying questions **only** at genuine forks (≤2). Explains each stage
in ADEPT order — Analogy → Diagram → Example → Plain → Tech — and *names the analogy's
breaking point* so you learn the system, not a cartoon of it. Compresses when you move fast,
goes deep when you ask why.

**3 · Drive to green.** The engine room — two **orthogonal** choices, both read from the work:

- **Gear** = *how many units at once.*
  - **Sequential** (default): small, coupled, or still-fuzzy — about one PR's worth. Drive
    it here, in this branch.
  - **Parallel** (`/sos:ship-loop`): work that decomposes into independent units. Author a
    `lavish` HTML spec; its independent-set size is the dial. Fan out via `treehouse`
    (one agent / worktree / PR), gate every PR through `no-mistakes`.
- **Engine** = *how much rigor.*
  - **Inline** (default): drive the loop yourself. Right when a durable plan doc would be
    ceremony.
  - **`/ce-plan` → `/ce-work`**: when the work wants a durable, **traceable** artifact —
    team handoff, multi-agent execution, long-lived work, anything you'll cross-reference in
    PRs/issues. `/ce-plan` turns your stage 0–2 research into guardrails (stable **U-IDs**,
    per-unit test scenarios, scope, risks — no pre-written code); `/ce-work` executes them
    (idempotent, worktree-isolated, gated to a reviewed PR); `/ce-compound` banks the lesson.

  Then it **discovers the verification source — never hardcodes one**: a project objective
  registry/runner if present; else the repo's own command (`make check`, `pnpm test`,
  `pytest`, `cargo test`, `go test ./...`, …); else it co-defines 3–7 checkable objectives
  with you. It loops until green, or stops after the **same failure 3×** and escalates with
  what it tried.

**4 · Self-improve.** Flags anything *flaky*, proposes **one** improvement and applies it with
consent — a new objective+check, a tuned threshold, a fix saved to `memory/`, or an edit to
the command itself. If the engine ran, `/ce-compound` folds in the learning. Closes with:
**objective status · what it taught · the one improvement.** That last line is the compounding.

---

## What it is — and what it is *not*

| `/goal-10x` **is** | `/goal-10x` is **not** |
|---|---|
| A control loop that drives to a *checkable* finish line | A one-shot "write me this code" generator |
| Project-agnostic — it discovers each repo's own harness | A tool that assumes one stack or one test runner |
| A coach that teaches the system while it works | A black box that hands you a diff and leaves |
| Self-improving — sharper after each run | A static script frozen at install time |
| The single front door that *picks* gear + engine for you | A thing you must hand-configure per task |
| Honest about ❌ — never fakes green | A confidence machine that declares victory early |

---

## When to use it — and when not

**Reach for it when:**
- You have an objective in a repo and want it *driven to a verified finish*, not just drafted.
- The input is messy — links, half-formed goals, a brain-dump — and needs structuring.
- You're not sure whether the work is one PR or ten (it'll pick the gear for you).
- You want to *learn the codebase/system* while the work happens.

**Skip it (or use something lighter) when:**
- It's a single trivial edit you'd type faster than you'd describe. Just do it.
- You want a *one-off answer or explanation*, not a driven loop — use `/living-knowledge` or
  a plain question.
- Product behavior isn't decided yet — that's upstream ideation/brainstorm territory; bring
  `/goal-10x` once there's something to drive to green.

---

## How to use it correctly — with examples

The skill rewards a **rich, honest dump** and an **objective you can check**.

```text
# Good: messy input + a checkable target + context links
/goal-10x add per-channel rate limiting to the gateway. notes below + 2 links.
done = inbound over limit returns 429 with Retry-After, and `pnpm test` stays green.
<paste your notes / issue link / PRD>
```

```text
# Good: let it pick the gear — describe shape, don't prescribe strategy
/goal-10x migrate all 14 API routes from callback style to async/await; each route is
independent. keep the contract tests green.
# → it spots the independent set and shifts into the parallel gear on its own.
```

```text
# Good: ask it to teach as it goes
/goal-10x fix the flaky auth test; explain the root cause in ADEPT as you fix it.
```

```text
# Good: opt into rigor when the work will be handed off / cross-referenced
/goal-10x plan and ship the billing-webhook feature with the ce-plan→ce-work engine —
i need a durable plan with U-IDs the team can review in the PR.
```

**Rules of thumb for correct use**
- State **what "done" looks like as a check** ("`make check` green", "endpoint returns 429").
  A checkable finish line is what the loop steers toward.
- **Paste the mess.** Links, half-thoughts, the issue body — stage 1 is built to absorb it.
- **Answer the ≤2 fork questions** honestly; they're the only ones it asks.
- **Let it pick gear and engine.** Describe the *shape* of the work, not the strategy.

---

## How to use it *wrongly* — antipatterns

| Antipattern | Why it backfires | Do this instead |
|---|---|---|
| "Make it better / clean this up" | No checkable finish line → the loop can't tell when it's done | Name a check: "…until `make check` is green and p95 < 200ms" |
| Pre-prescribing the strategy ("spawn 8 agents and…") | You override the gear/engine selection that reads the work | Describe the work's shape; let stage 3 choose |
| Withholding context to "keep it short" | Stage 0/1 then guesses; you get a confident wrong map | Dump links, notes, the issue — it's designed for mess |
| Using it for a 1-line typo fix | All ceremony, no payoff | Just edit it (or `/ce-work` bare-prompt) |
| Trusting a green you didn't define | It drives to *the discovered check* — if that check is weak, green is hollow | Make sure the project's check actually covers the behavior; add one in stage 4 |
| Reaching for the `ce-*` engine on tiny/non-software work | Plans become ceremony; U-IDs/PRs don't apply | Stay inline — that's the default for a reason |
| Demanding a fake ✅ to "just finish" | It won't, and shouldn't | Read the honest ❌; the 3×-same-failure stop is a signal, not a bug |

---

## Storytelling — pattern vs antipattern

**Scene A — the antipattern.** You type `/goal-10x make the dashboard faster`. No check, no
context. It guesses "faster" means bundle size, trims an import, declares a vague win. You
meant *server response time*. Two wasted turns. The loop had no setpoint, so it steered
toward the wrong one.

**Scene B — the pattern.** You type:
`/goal-10x dashboard p95 is 900ms; target < 300ms. here's the flamegraph link + the slow
query. done = the perf test asserts < 300ms and `pytest` is green.` Now stage 0 reads the
flamegraph, stage 1 fixes the finish line as a *check*, stage 3 discovers `pytest`, adds the
asserting perf test, and loops: profile → fix the named query → re-run → green. Stage 4
notices the perf test didn't exist before and **keeps it** — so the next regression trips a
wire automatically. Same effort as Scene A; a permanently faster dashboard *and* a new guard.
That delta — a durable check that didn't exist before — is the compounding made concrete.

---

## Installation — across projects and across computers

`/goal-10x` ships in the `sos` Claude Code plugin. There's no Anthropic-cloud sync of
`~/.claude`, so "everywhere" means two distinct things:

### A. Across every project (this machine) — install the plugin

```text
/plugin marketplace add wjlgatech/sos
/plugin install sos@wjlgatech-plugins
# → /sos:goal-10x  /sos:ship-loop  /sos:lavish  /sos:treehouse  /sos:no-mistakes …
```

Plugins live under `~/.claude/` (user scope), so once installed they're available in
**every project** on this machine — no per-repo step.

**Want the bare `/goal-10x` name** (not just `/sos:goal-10x`)? One idempotent script adds the
marketplace, installs the plugin, and symlinks `~/.claude/commands/goal-10x.md` → the live
plugin command so both names work and stay in sync:

```bash
curl -fsSL https://raw.githubusercontent.com/wjlgatech/sos/main/plugins/sos/scripts/install-goal-10x.sh | sh
```

### B. Across computers (every machine you work on)

Pick whichever fits how you sync machines:

**Option 1 — re-run the one-liner per machine (simplest).** On each new computer:

```bash
curl -fsSL https://raw.githubusercontent.com/wjlgatech/sos/main/plugins/sos/scripts/install-goal-10x.sh | sh
# update later:  claude plugin marketplace update wjlgatech-plugins
```

**Option 2 — track a portable manifest in your `~/.claude` dotfiles (zero re-typing).** Claude
Code records marketplaces + enabled plugins in `~/.claude/settings.json` (`extraKnownMarketplaces`
+ `enabledPlugins`), but that file usually isn't synced (it can hold machine-specific/security
keys). Keep a **secret-free manifest** in your dotfiles and merge it on each machine:

```jsonc
// ~/.claude/claude-plugins.json   (tracked in your dotfiles repo)
{
  "extraKnownMarketplaces": {
    "wjlgatech-plugins": { "source": { "source": "github", "repo": "wjlgatech/sos" } }
  },
  "enabledPlugins": { "sos@wjlgatech-plugins": true }
}
```

```bash
# fresh machine: pull dotfiles, then merge the manifest into settings.json + restart Claude Code
~/.claude/scripts/install-plugins.sh    # idempotent: merges the two keys, preserves the rest
```

To make the **bare `/goal-10x`** alias travel too (the symlink lives in the usually-ignored
`commands/`), have your `install-plugins.sh` recreate it idempotently after the merge:

```bash
mkdir -p "$HOME/.claude/commands"
ln -sfn "$HOME/.claude/plugins/marketplaces/wjlgatech-plugins/plugins/sos/commands/goal-10x.md" \
        "$HOME/.claude/commands/goal-10x.md"
```

**Fresh-machine recipe (Option 2), end to end:**

```bash
git clone <your-dotfiles> ~/.claude     # or pull if it already exists
~/.claude/scripts/install-plugins.sh    # marketplaces + enabled plugins + bare alias
# restart Claude Code → /goal-10x, /sos:*, (and /ce-* if you track them too) are live
```

> Verify anytime: `ls -lL ~/.claude/commands/goal-10x.md` (bare alias resolves) and that
> `sos@wjlgatech-plugins` is `true` in `~/.claude/settings.json`.

---

## See also

- [`commands/goal-10x.md`](../plugins/sos/commands/goal-10x.md) — the command itself (source of truth)
- [`commands/ship-loop.md`](../plugins/sos/commands/ship-loop.md) — the parallel gear (`lavish`→`treehouse`→`no-mistakes`)
- `/ce-plan` → `/ce-work` → `/ce-compound` — the optional plan+execute engine (compound-engineering plugin)
- [`CHANGELOG.md`](../CHANGELOG.md) — what changed and why
