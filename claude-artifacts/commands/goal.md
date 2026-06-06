Verify DreamMakeTrue objectives and report machine-checkable pass/fail.

Stage to verify: $ARGUMENTS

> **API base:** the live API is on `:8001` (see memory: `:8000` is taken by another app).
> Never hardcode it — the runner reads `NEXT_PUBLIC_API_URL` / `DMT_API_URL`, default `:8001`.
> Project dir: `/Users/openclaw/Documents/Projects/dreammaketrue`.

## What you must do

1. **Parse the stage** from $ARGUMENTS. Valid values:
   - `all` or `auto` → **autonomous mode** — verify ALL objectives, fix failures, loop until green (see below)
   - `topic-map` or `stage-1`
   - `person-map` or `stage-2`
   - `simulator` or `stage-3`
   - `expression` or `stage-4`
   - `first-slice` or `stage-5` (runs all stages end-to-end)

---

## `/goal all` — autonomous mode (the no-babysitting contract)

The single source of truth for objectives is **`docs/OBJECTIVES.md`**; the runner is
**`scripts/autodrive.py`** (it acts as the end user: real URL → `/analyze` → `/simulate`
→ `/express`, and checks every machine objective). In this mode you DO NOT hand control
back after one report — you drive to green:

1. **Ensure the stack is up.** `curl -s $DMT_API_URL/health` (default `http://localhost:8001`).
   If down, tell the user the one command to start it and stop; otherwise continue.
2. **Run the harness:**
   ```bash
   apps/api/.venv/bin/python scripts/autodrive.py --json /tmp/objectives.json
   ```
3. **Read the ❌ rows.** Each objective id maps to a stage + service file (OBJECTIVES.md).
   For every failure: open the named `apps/api/src/services/*.py`, find the cause, fix it.
4. **Re-run autodrive. Loop steps 2–4** until every machine objective is ✅, or you hit the
   same failure **3 times** — then STOP and escalate with what you tried (don't thrash).
5. **Only then surface the 🔴 judgment gates** (J5.1, J5.2) to the user, with the actual
   artifact printed by autodrive, and ask the two questions. Do not self-answer them.
6. **Report** the final objective table + what you changed. If you fixed feature code, the
   doc-sync hook applies (CHANGELOG + docs).

Escalate early (per CLAUDE.md): bad fixes are worse than an honest ❌. Never fake a green.

2. **Run the verification** for that stage using the method below.

3. **Report every condition** as ✅ PASS or ❌ FAIL with the actual value observed.

4. **Stop at human gates** (🔴) and ask Paul the exact questions specified. Do not proceed until you have a yes.

---

## Stage verification methods

### stage-1 · Topic-Map Extractor

```bash
cd /Users/openclaw/Documents/Projects/dreammaketrue
curl -s -X POST http://localhost:8001/v1/engine/topic-map \
  -H "Content-Type: application/json" \
  -d '{"source_text": "[use a real 500-word excerpt from a podcast or article]"}'
```

**Conditions:**

1. ✅/❌ `nodes` contains ≥ 3 items with `type="concept"`
2. ✅/❌ `nodes` contains ≥ 3 items with `type="claim"`
3. ✅/❌ `nodes` contains ≥ 2 items with `type="evidence"` (verbatim quotes in `summary`)
4. ✅/❌ At least one concept has non-empty `principle` AND `transfer_domains` with ≥ 2 entries
5. ✅/❌ All concept `summary` fields are jargon-free (no domain-specific terms in a 12-year-old test)

**File:** `apps/api/src/services/topic_map.py`

---

### stage-2 · Person-Map Extractor

Run for each speaker in parallel (two API calls):

```bash
curl -s -X POST http://localhost:8001/v1/engine/person-map \
  -H "Content-Type: application/json" \
  -d '{"person_name": "[Name]", "corpus": ["[text corpus]"]}'
```

**Conditions (per speaker):**

1. ✅/❌ `person_map.worldview_summary` is non-empty
2. ✅/❌ `person_map.mental_models` has ≥ 3 entries, each with `name`, `evidence` (≥ 2 items), `limitation`
3. ✅/❌ `person_map.decision_heuristics` has ≥ 5 entries with `example` field
4. ✅/❌ `person_map.honest_limits` has ≥ 3 entries
5. ✅/❌ `skill_md` length > 500 chars (SKILL.md generated)
6. ✅/❌ `quality_scores.total` ≥ 70 (darwin-skill gate)

**File:** `apps/api/src/services/person_map.py`

---

### stage-3 · Participation Simulator

```bash
curl -s -X POST http://localhost:8001/v1/engine/simulate \
  -H "Content-Type: application/json" \
  -d '{"topic_map_id": "[id]", "person_map_ids": ["[Speaker A]", "[Speaker B]"], "user_opening": "[user question]"}'
```

**Conditions:**

1. ✅/❌ Response `raw` length > 100 chars
2. ✅/❌ Both speaker names appear in the response
3. ✅/❌ At least one keyword from the user's question appears in the response (causal, not cosmetic)

**File:** `apps/api/src/services/simulator.py`

🔴 **HUMAN GATE — stop here and ask Paul:**

> "Does the participation feel meaningful? Was your question genuinely shaping the conversation, or was it just cosmetically acknowledged? Yes to proceed, No to identify which part of the simulator broke it."

---

### stage-4 · Expression

Test the `/express` endpoint with `linkedin_post` format:

```bash
curl -s -X POST http://localhost:8001/v1/engine/express \
  -H "Content-Type: application/json" \
  -d '{"session_id": "goal-test", "format": "linkedin_post", "user_name": "[name]", "user_contribution": "[verbatim question]", "topic": "[topic]", "concept_principles": ["[p1]", "[p2]"], "personas": [{"person_name": "[A]", "worldview_summary": "[ws]"}, {"person_name": "[B]", "worldview_summary": "[ws]"}]}'
```

**Conditions:**

1. ✅/❌ `content` length > 200 chars
2. ✅/❌ `author_credit` matches the user name
3. ✅/❌ User's verbatim contribution appears (quoted or clearly present) in `content`
4. ✅/❌ `living_knowledge_layer` is set (2–5)
5. ✅/❌ `provenance_note` is non-empty

Also test `participation_brief`:

```bash
curl -s -X POST http://localhost:8001/v1/engine/participation-brief \
  -H "Content-Type: application/json" \
  -d '{"session_id": "goal-test", "format": "participation_brief", ...}'
```

6. ✅/❌ Brief contains "Questions Only You Would Ask" section with ≥ 2 questions

**File:** `apps/api/src/services/expression.py`

---

### stage-5 · First Slice (end-to-end)

```bash
cd /Users/openclaw/Documents/Projects/dreammaketrue
apps/api/.venv/bin/python scripts/autodrive.py --json /tmp/objectives.json
```

(The modern harness — real ingestion + `/analyze` + `/simulate` + `/express`. The older
`scripts/first_slice_test.py` is kept for reference but points at the legacy `/compose`.)

**Conditions:**

1. ✅/❌ Stage 1 goal conditions all pass
2. ✅/❌ Stage 2 goal conditions all pass (both speakers)
3. ✅/❌ Stage 3 goal conditions all pass
4. ✅/❌ Stage 4 goal conditions all pass

🔴 **HUMAN GATE — stop here and ask Paul two questions:**

> Q1: "Did the participation feel meaningful? Was your question present in the conversation in a way that shaped it — not just acknowledged?"
> Q2: "Is the artifact worth publishing? Would you post this LinkedIn post as-is, or near-as-is?"

If YES to both → First Slice is proven. Announce: "Stage 5 complete. Ready to move to Stage One (90 days)."
If NO → identify which condition broke the human signal and iterate.

---

## Output format

```
/goal [stage]
═══════════════════════════════════════
Stage: [name]
File: [path]
API: [endpoint]
───────────────────────────────────────
  ✅ Condition 1: [label] — [observed value]
  ✅ Condition 2: [label] — [observed value]
  ❌ Condition 3: [label] — expected [x], got [y]
───────────────────────────────────────
PASS: [N]/[total] conditions
[If fail: specific recommendation to fix]
═══════════════════════════════════════
```
