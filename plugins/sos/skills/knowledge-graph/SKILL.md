---
name: knowledge-graph
description: "Build a TOPIC knowledge graph or a PERSONA (person) knowledge graph from multi-source evidence, ranked by what people actually engage with — then emit structured graph JSON + a self-contained HTML view. Triggers on 'build a knowledge graph of X', 'map the topic X', 'model person X as a graph', 'what does X think / how do they reason', 'graph the landscape of X', or when you need a grounded, relationship-rich model of a topic or a person rather than a prose summary. Topic mode → concepts/claims/evidence/principles with typed edges (supports/contradicts/causes/transfers-to). Persona mode → worldview/mental-models/heuristics/honest-limits with relationship edges (builds-on/criticizes/collaborates). Every edge carries engagement-weighted confidence and a temporal stamp. NOT for a quick factual lookup or a one-paragraph explainer (use living-knowledge for that)."
argument-hint: "[topic OR person] [--mode topic|persona]"
allowed-tools: WebSearch, WebFetch, Read, Write, Bash, Grep, Glob
---

# Knowledge Graph Builder

Turn many sources into one **graph you can reason over** — not a prose brief that evaporates.

Two modes:

- **Topic** → a living-knowledge map: `concept → claim → evidence → principle`, with typed edges.
- **Persona** → a faithful model of a person: `worldview · mental-models · decision-heuristics · honest-limits`, with relationship edges.

This skill is the synthesis of two ideas. From **last30days** (mvanhorn): gather across many sources and rank by _what people actually engage with_ (upvotes, likes, stars, prediction-market odds) — not editorial authority — and merge duplicates across sources by **entity overlap**, recency-aware. From the **DreamMakeTrue engine**: deep, schema'd extraction (living-knowledge 5-layer topic maps; nuwa-style persona maps). The 10x both lack on their own: **explicit subject–predicate–object edges, each with engagement-weighted confidence and a temporal stamp.**

> Knowledge becomes a graph when every claim is _anchored_ (who said it, where, how strongly engaged), _typed_ (supports / contradicts / causes / builds-on), and _dated_. A list of facts is a filing cabinet; a graph is something you can interrogate.

---

## When to use

- "Build / map / graph the topic of **X**" → **topic mode**.
- "Model **Person** as a graph" · "how does **X** reason / what do they believe" → **persona mode**.
- You want a structured, relationship-rich, _sourced_ artifact you can query, diff over time, or hand to another system — not a summary.

Do **not** use for a quick "what is X" explainer (that's `living-knowledge`) or a one-off fact.

---

## The pipeline (run these phases)

### Phase 1 — GATHER (multi-source, engagement-ranked, recency-aware)

Use `WebSearch` + `WebFetch` to pull **5–15 sources**. Deliberately diversify — do not over-index on one outlet. Per source, record what you'll need for confidence: **url, author, date, and an engagement signal** (upvotes / likes / stars / citations / views / odds).

Source priorities by intent (from last30days — pick what fits):

- **Foundational/technical topic** → docs, papers, GitHub (stars/releases), Hacker News, long-form posts.
- **Opinion/contested topic** → Reddit threads (upvotes + top comments), X/social (likes/reposts), debate venues.
- **Fast-moving topic** → recent X / Reddit / news, weighted toward the last 30–90 days.
- **Persona mode** → the person's OWN output first: recent **GitHub** activity (what they ship — PRs, repos, releases), **X/social** posts (what they say), talks/interviews/papers (canon), THEN how others react (Reddit/HN/quotes). Model them from their _recent real footprint_, not just their bio.

For each source, capture 1–3 verbatim quotes — those become `evidence` nodes / mental-model evidence.

### Phase 2 — EXTRACT (into the target schema)

Print the schema first: `python3 scripts/kg.py schema topic` (or `persona`). Then, from the gathered evidence, write a single `graph.json` of **nodes** and **edges** (see schemas below). Rules:

1. **Ground every node** in ≥1 source. No node without provenance. (If you can't source it, drop it — same refuse-don't-hallucinate rule as the engine's person-map.)
2. **Type every edge** — `supports`, `contradicts`, `causes`, `part_of`, `transfers_to` (topic); `builds_on`, `criticizes`, `collaborates_with`, `influenced_by`, `holds` (persona).
3. On each node/edge put `sources: [{url, author, date, engagement, quote?}]`. The script computes confidence from these.
4. Persona mode: every mental-model gets ≥2 evidence + a `limitation`; include `honest_limits` (where the record is thin). This is the nuwa/darwin discipline — it's what makes the model _faithful_ instead of flattering.

### Phase 3 — ASSEMBLE (the script does the deterministic work)

```bash
python3 scripts/kg.py build graph.json --mode topic --out topic.html
```

The script: validates the schema, **dedups nodes by entity overlap** (Jaccard overlap coefficient, ported from last30days `cluster.py` — merges "PagedAttention" + "Paged Attention" + "vLLM's paging"), computes **engagement-weighted confidence** per edge:

```
confidence = clamp( source_quality × freshness × (0.5 + 0.5·engagement_norm) × corroboration )
```

(source_quality baseline per platform; freshness from recency; corroboration = # distinct sources backing the edge — the cross-source agreement signal), then writes a normalized `*.graph.json` + a **self-contained dark-mode HTML** view (no external scripts).

### Phase 4 — REPORT

Show the user: node/edge counts by type, the highest-confidence edges, the **single-source / thin-evidence** flags (honesty about what's weakly grounded), and the path to the HTML. For persona mode, surface the darwin-style check: are there ≥3 mental models w/ evidence+limitation, ≥3 honest limits?

---

## Topic graph schema (living-knowledge)

```json
{
  "kind": "topic",
  "subject": "vLLM inference",
  "nodes": [
    {
      "id": "n1",
      "type": "concept",
      "name": "PagedAttention",
      "summary": "KV-cache paging that removes contiguous-memory waste (jargon-free).",
      "principle": "Treat scarce memory like virtual memory: page it.",
      "transfer_domains": ["OS memory paging", "database buffer pools"],
      "sources": [
        {
          "url": "...",
          "author": "...",
          "date": "2025-10",
          "engagement": 1800,
          "quote": "..."
        }
      ]
    },
    {
      "id": "n2",
      "type": "claim",
      "name": "vLLM raises throughput ~24x",
      "summary": "Continuous batching + paging vs. naive serving.",
      "sources": [{ "url": "...", "engagement": 540 }]
    },
    {
      "id": "n3",
      "type": "evidence",
      "name": "benchmark quote",
      "summary": "\"...up to 24x higher throughput...\" (verbatim).",
      "sources": [{ "url": "..." }]
    }
  ],
  "edges": [
    {
      "src": "n1",
      "dst": "n2",
      "type": "causes",
      "sources": [{ "url": "...", "engagement": 540 }]
    },
    {
      "src": "n3",
      "dst": "n2",
      "type": "supports",
      "sources": [{ "url": "..." }]
    }
  ]
}
```

Node types: `concept` (jargon-free summary + `principle` + `transfer_domains`), `claim`, `evidence` (verbatim quote in `summary`). Edge types: `supports`, `contradicts`, `causes`, `part_of`, `transfers_to`, `relates_to`.

## Persona graph schema (nuwa)

```json
{
  "kind": "persona",
  "subject": "Cedric Clyburn",
  "nodes": [
    {
      "id": "p1",
      "type": "worldview",
      "summary": "Open-source LLM serving should be efficient AND accessible; ship pragmatically.",
      "sources": [
        {
          "url": "...",
          "author": "Cedric Clyburn",
          "date": "2025-11",
          "engagement": 120
        }
      ]
    },
    {
      "id": "m1",
      "type": "mental_model",
      "name": "Quantize before you scale hardware",
      "summary": "Compress the model first; it's the cheapest lever.",
      "evidence": [
        "\"...quantization gets you most of the win...\"",
        "demoed LLM Compressor"
      ],
      "limitation": "Less applicable when accuracy floors are strict.",
      "sources": [{ "url": "...", "engagement": 90 }]
    },
    {
      "id": "h1",
      "type": "heuristic",
      "name": "Measure before you optimize",
      "example": "Benchmark throughput/latency on YOUR traffic before tuning.",
      "sources": [{ "url": "..." }]
    },
    {
      "id": "l1",
      "type": "honest_limit",
      "summary": "Thin public record on multi-node distributed serving.",
      "sources": [{ "url": "..." }]
    }
  ],
  "edges": [
    {
      "src": "m1",
      "dst": "h1",
      "type": "builds_on",
      "sources": [{ "url": "..." }]
    },
    { "src": "p1", "dst": "m1", "type": "holds", "sources": [{ "url": "..." }] }
  ]
}
```

Node types: `worldview`, `mental_model` (needs `evidence[]` ≥2 + `limitation`), `heuristic` (with `example`), `honest_limit`, `signature_phrase`. Edge types: `holds`, `builds_on`, `criticizes`, `collaborates_with`, `influenced_by`, `relates_to`.

---

## Faithfulness rules (non-negotiable)

1. **No unsourced node.** Provenance or it doesn't exist.
2. **Persona = the real person, not a flattering sketch.** Use only grounded positions; tag any extrapolation `[beyond the record]`; always include `honest_limits`.
3. **Engagement is a signal, not truth.** High likes ≠ correct — it weights _attention/corroboration_, surfaced as confidence, never as fact.
4. **Verbatim evidence.** Quotes are copied, not paraphrased, so the graph stays auditable.

## Output

`*.graph.json` (normalized, deduped, confidence-scored) + a self-contained HTML view. Both are portable — feed the JSON to any downstream system (e.g. a Neo4j/Graphiti loader, or DreamMakeTrue's topic-map / person-map).
