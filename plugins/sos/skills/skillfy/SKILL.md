---
name: skillfy
description: Skillfy ANY source or expertise into a bounded, verifiable, transferable skill — atomic Skill schema with honest edges (not_good_at), ADEPT explanations, a masked by-hand worksheet, a mechanical checker, a discernment check (choice under ambiguity, never recall), and a teach-back. Two modes — served (drive a running super-u API) or standalone (apply the method with your own model, emit super-u-compatible skill.yaml). Use when asked to 'skillfy this', 'turn this paper/video/expertise into a skill', 'compress this expertise', 'make a worksheet from this', 'extract the discernment', or when a user wants to LEARN a mechanism by hand rather than read a summary. NOT for prose summaries (that's a summary, not a skill) and NOT for quick explanations (use living-knowledge).
source: "Super U Layer 2 (Skillfy) — https://github.com/wjlgatech/super-u, master spec §5"
metadata:
  type: technique
  portable: true
---

# Skill: Skillfy — compress expertise into a verifiable, transferable skill

A summary tells you *about* a mechanism. A **skillfied** skill makes you *operate* it:
see it move (Fast pass), compute it by hand with masked steps (Slow pass), get checked
mechanically, then prove judgment with a choice under ambiguity. The unit of transfer is
the atomic **Skill schema** — and the heart of it is **discernment**: a skill with no
`not_good_at` edges is rejected. Knowing where a tool fails IS the expertise.

## Non-negotiables (from the Super U spec — enforce these in any mode)

1. **Specificity beats comprehensiveness.** One narrow mechanism per skill ("scaled
   dot-product attention"), never a survey ("transformers").
2. **Ground truth required.** Every skill declares how correctness is verified:
   `mechanical` (a reference implementation checks it), `expert_judged`, or
   `real_world_outcome` — and who/what closes the loop.
3. **Skeleton before skin.** Schema, checker, masked steps first; styling and tone last.
4. **Discernment, never recall.** The verification question must be a *choice under
   ambiguity* with a pass condition ("names the O(n²) wall AND picks a
   locality-respecting alternative"), not a definition quiz.

## Mode 1 — served (a super-u API is running)

Default base: `http://127.0.0.1:8000`. Probe `GET /health` first; if down, use Mode 2.

| Endpoint | What it does |
|---|---|
| `GET /skillfy/skill` | The reference skill (self-attention-001) as schema JSON |
| `GET /skillfy/ladder` | Depth ladder: Intuition → Working → Applied → Mastery |
| `GET /skillfy/worksheet` | By-hand worksheet, masked steps withheld |
| `POST /skillfy/check` | Mechanical check of worksheet answers vs the reference impl |
| `GET/POST /skillfy/discernment-check` | The ambiguity question / grade an answer |
| `POST /skillfy/extract` `{source_text}` | **LLM-judged**: source → full Skill schema (rejects edgeless skills) |
| `POST /creator/skillfy` `{room}` | Skillfy a dreammaketrue Room (flywheel bridge) |

`/extract` and `/creator/skillfy` need an LLM key — or **zero-cost** via NVIDIA NIM:
`SUPER_U_LLM_PROVIDER=openai`, `SUPER_U_LLM_BASE_URL=https://integrate.api.nvidia.com`,
`SUPER_U_LLM_API_KEY=nvapi-…`, `SUPER_U_LLM_MODEL=z-ai/glm-5.1` (see the `free-llm`
skill; ~40 req/min, verify ids against the live `/v1/models`).

## Mode 2 — standalone (no server; Claude / Hermes / Codex native)

Produce three artifacts from the source (paper, video transcript, doc, your own analysis):

**1. `skill.yaml`** — conform to the Skill schema (all fields required unless noted):

```yaml
id: <kebab-id-001>            # one narrow mechanism
name: <human name>
one_line: <what it lets you DO>
identity: { what_it_is, core_mechanism }   # mechanism, not topic
competence:
  good_at: [..]
  not_good_at: [..]           # REQUIRED non-empty — edgeless skills are rejected
activation: { use_when: [..], dont_use_when: [..] }
differentiation: { similar_skills: [..], how_to_tell_apart }
granularity: { ... }          # scope: what's in, what's explicitly out
expression:
  modalities: [text, ...]
  practice_artifact: <the by-hand exercise>
  adept: { analogy, diagram, example, plain, technical }   # all five ADEPT lenses
provenance: { source_type, source_ref, extracted_on }
verification:
  discernment_check: <choice under ambiguity>
  pass_condition: <mechanically checkable halves>
  ground_truth: { type: mechanical|expert_judged|real_world_outcome, who_or_what_closes_it }
```

**2. Worksheet** — 3–6 steps on a TINY concrete instance (small numbers, one row).
Reveal arithmetic scaffolding; **mask** the 1–2 steps that carry the insight (mark
`🔒 decision` / `🔒 arithmetic`). The learner fills only the masked steps.

**3. Checks** — (a) a mechanical checker for the masked steps (exact values from a
reference computation, with tolerance); (b) the discernment check + pass condition;
(c) a teach-back prompt ("compress it to a tweet") with the core mechanism to diff against.

**Self-verify before delivering:** does `not_good_at` have ≥1 honest edge? Is the
discernment check answerable *wrongly* by someone who only memorized? Can the masked
steps be checked without an LLM? If any answer is no, fix it — don't ship it.

## Reference implementation

Working example end-to-end: super-u's one-pager (`/` when served) — self-attention
heatmap (Fast), masked worksheet + checker (Slow), genome discernment question,
teach-back. Source: `src/super_u/layers/skillfy/` and
`artifacts/self-attention-001/skill.yaml` in https://github.com/wjlgatech/super-u.
