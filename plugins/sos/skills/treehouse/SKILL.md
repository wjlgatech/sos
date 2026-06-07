---
name: treehouse
description: "Fan a spec out to many coding agents running in parallel, isolated git worktrees — the Code phase of a high-velocity agentic loop. Use AFTER a spec exists (from lavish) and the work splits into independent units, when you want dozens of changes moving at once instead of coding sequentially. Triggers on 'build this spec', 'parallelize this', 'run agents on these tasks', 'fan this out', 'spin up workers', or any plan with multiple independent work units. Decomposes the spec by dependency, assigns one unit per agent, runs the independent set concurrently in isolated worktrees, and collects one PR per unit. Agent-agnostic — the unit-of-work contract runs on Claude, Codex, Hermes, or OpenClaw. NOT for a single change (just do it) or for tightly-coupled work that can't be isolated."
argument-hint: "[path to the lavish HTML spec, or the set of independent tasks to fan out]"
allowed-tools: Read, Grep, Glob, Edit, Write, Bash(git *), Bash(bash *), Agent
metadata:
  type: workflow
  phase: code
  portable: true
  cross-agent: true
---

# Skill: Treehouse — orchestrate parallel coding agents

Treehouse is the **Code** phase. It takes a spec (ideally a `lavish` HTML spec) and turns it
into **many changes moving at once**: each independent work unit is assigned to its own agent,
running in its own **git worktree**, producing its own PR. Sequential coding is the bottleneck
between a plan and shipped work; Treehouse removes it.

> Provenance: distilled from Kun Chen's `treehouse` (agent orchestration), used to run
> 20–30 agents in parallel toward ~40 PRs/day. The two load-bearing ideas:
> **decompose by dependency** and **isolate by worktree**.

## The core model

```
            ┌──────────────── lavish spec (queryable: REQ ids, data-depends, groups) ───────────────┐
            │                                                                                         │
   ┌────────▼────────┐   independent set (no unmet deps)    ┌──────────────┐   1 PR / unit
   │  decompose +    │ ───────────────────────────────────▶ │  fan out N   │ ─────────────────▶  collect
   │  topo-sort      │                                       │  agents      │                     + order
   └─────────────────┘   each agent: own worktree + branch  └──────────────┘                     merges
```

A **work unit** = one `div.req` from the spec: an objective, acceptance criteria, the files it
owns, the tests that prove it. It is the atom of parallelism — one unit, one agent, one
worktree, one branch, one PR.

## Procedure

1. **Load and decompose the spec.** Read the `lavish` HTML spec. Extract each `div.req` with its
   `id`, `data-depends`, `data-parallel-group`, `data-files`, `data-tests`, and `data-ac` list.
   If there's no spec, write one first (`/sos:lavish`) — fanning out without a spec fans out
   ambiguity. Run `scripts/plan-fanout.sh <spec.html>` to print the unit table and the
   dependency-ordered wave plan.

2. **Build the wave plan (topological).** Group units into **waves** by dependency:
   - **Wave 1** = every unit with no unmet `data-depends` → all run concurrently.
   - **Wave 2** = units whose deps all landed in wave 1. And so on.
   - Within a wave, only run units that don't share files (`data-files` disjoint). Overlapping
     files = a merge collision waiting to happen — sequence them into different waves instead.

3. **Check for file collisions before launching.** `plan-fanout.sh` flags any two same-wave
   units that touch the same path. Resolve by re-waving (not by hoping). Isolation is the whole
   point; two agents editing one file defeats it.

4. **Isolate each unit in its own worktree.** For each unit in the wave:
   ```bash
   git worktree add -b agent/<spec-slug>/<REQ-id> ../wt-<REQ-id> <base-branch>
   ```
   Each agent gets a clean checkout. They cannot step on each other because they're literally
   editing different working directories.

5. **Dispatch one agent per unit (the unit-of-work contract).** Launch the wave concurrently —
   in Claude Code, multiple `Agent` calls in a single message run in parallel. Hand each agent
   exactly the contract below. Keep concurrency sane (Kun runs 20–30; start lower and raise it
   as your review/CI throughput allows).

6. **Collect and order the merges.** Each agent returns a self-report (contract below). Gather
   them. Merge in **dependency order** (a unit merges only after everything in its `data-depends`
   has merged). Before merging *anything*, run the **Validate** phase — `no-mistakes`
   (`/sos:no-mistakes`) audits each PR against its `data-ac`. Treehouse produces PRs; it does
   **not** self-approve them.

7. **Clean up worktrees.** `git worktree remove ../wt-<REQ-id>` once a unit is merged or
   abandoned. Re-wave any failed units (an agent that got stuck) with tighter scope.

## The unit-of-work contract (agent-agnostic)

Every dispatched agent — Claude, Codex, Hermes, OpenClaw — receives the **same** contract.
This is what makes the fan-out portable: the unit is the API, the agent is the implementation.

**Input given to the agent**
- `worktree`: the isolated checkout it owns (its CWD).
- `branch`: `agent/<spec-slug>/<REQ-id>` (already created).
- `objective`: the `div.req` heading.
- `acceptance`: the `data-ac` list with each `data-check` command.
- `files`: `data-files` — the paths it may touch. **It must not edit outside this set.**
- `out_of_scope`: the spec's `data-no` list.
- `interfaces`: the spec's `data-contract` block it must conform to.

**Output the agent must return (self-report)**
```json
{
  "req_id": "REQ-3",
  "branch": "agent/auth-revamp/REQ-3",
  "status": "ready | blocked | failed",
  "acceptance": [{ "check": "pytest tests/test_auth.py::test_login", "passed": true }],
  "files_changed": ["src/auth.py", "tests/test_auth.py"],
  "out_of_scope_touched": [],
  "notes": "anything the reviewer needs; blockers if status != ready"
}
```

**Rules every agent must honor**
- Touch only `files`; if the work genuinely needs a file outside the set, return
  `status: "blocked"` with the reason — do **not** silently widen scope (that's what breaks
  the collision guarantees and what `no-mistakes` will flag).
- Make every `data-ac` check pass, and run them — `acceptance[].passed` must be real, not
  assumed.
- Stay inside the spec. Don't build anything in `out_of_scope`.
- One unit = one focused PR. Don't bundle unrelated changes.

## Cross-agent orchestration

The contract above is a JSON-in / JSON-out spec, so the orchestrator is harness-agnostic:

- **Claude Code:** dispatch with parallel `Agent` calls (one message, multiple tool uses);
  each subagent runs the contract in its worktree.
- **Codex / Hermes / OpenClaw / mixed fleets:** spawn one process per unit pointed at its
  worktree, feeding the input block and parsing the self-report. You can even mix harnesses
  within one wave — cheap models for mechanical units, stronger ones for the hard `div.req`.
- This repo's `src/multi_agent_performance.py` patterns (per-agent scoring, capability maps)
  are the natural place to record which agent/harness handled which unit and how it scored —
  feed that back into routing.

## Anti-patterns (self-check before fanning out)

1. **Fanning out without a spec.** No `data-files`/`data-depends` means no collision detection
   and no acceptance to check. Run `lavish` first.
2. **Same-wave file overlap.** Two agents editing one path → guaranteed merge pain. The whole
   value of worktrees is isolation; re-wave instead.
3. **Faking independence.** Coupled units forced into one wave to look parallel. They'll
   produce PRs that only merge together — which isn't parallelism, it's a delayed monolith.
4. **Self-merging.** Treehouse's output is *PRs*, not merges. Skipping `no-mistakes` to hit a
   PR count ships AI mistakes at scale — the exact failure mode the loop exists to prevent.
5. **Unbounded concurrency.** 30 agents you can't review or CI in time is a queue, not
   throughput. Match fan-out width to downstream (review + CI) capacity.
6. **Scope-creeping agents.** A unit that touches files outside `data-files` broke the
   contract — treat it as `blocked`, re-scope, don't merge the surprise.

## Where this fits

`lavish` (Plan) → **`treehouse` (Code, parallel agents)** → `no-mistakes` (Validate). Run the
full arc with **`/sos:ship-loop`**. Treehouse's only job: turn a queryable spec into many
isolated, collision-free PRs, fast — then hand every PR to the validator before anything merges.
