---
name: living-repo
description: "Transform a static awesome-list / link-collection repo into a LIVING knowledge system: compile its README tables into a typed knowledge graph (papers/repos/people/labs/talks/benchmarks with authored_by/has_code/member_of/part_of/builds_on edges), render a self-contained interactive force-graph HTML (works from file:// and GitHub Pages), and install a weekly link-freshness GitHub Action so the list stays honest. Triggers on 'make this repo living', 'turn this awesome list into a knowledge graph', 'kgfy this repo' (when the repo is a curated list), 'add freshness checks', 'living knowledge repo'. The parse is DETERMINISTIC (stdlib-only, zero LLM tokens, CI-safe); an optional nim-enrich pass adds paper-lineage edges via NVIDIA's free NIM API, and a hand-written enrichment overlay carries curator knowledge the tables can't. NOT for arbitrary prose sources (use dreammaketrue/kgfy) and NOT for multi-source topic research (use knowledge-graph)."
argument-hint: "[path-to-awesome-repo]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Living Repo — awesome-list → living knowledge system

A curated list is a filing cabinet. This skill turns it into something a reader can
**interrogate**: a typed graph (who wrote what, what implements what, what builds on
what), an interactive map, and automation that keeps the links honest.

The deliberate design choice: **the parse is deterministic.** Awesome lists already
encode their knowledge in GFM tables — column headers name the fields, bold spans mark
key people, links carry identity. No LLM is needed to read that, so the compile step
costs zero tokens, runs identically in CI, and never hallucinates a node. LLM calls are
reserved for the one thing tables can't express — cross-paper lineage — and even then
go to NVIDIA's free NIM API (see the `nvidia-free-llm` skill), never the expensive path.

## The three moves

### 1 · Compile the graph

```bash
python3 scripts/awesome_kg.py build README.md \
  --out knowledge/graph.json \
  --html docs/index.html \
  --enrich knowledge/enrichments.json   # optional curator overlay
```

What the parser understands (the de-facto awesome-list grammar):

| README element | Graph result |
|---|---|
| table header `Paper / Repo / Person / Lab / Benchmark / Title+Speaker` | node type |
| `Authors / Venue / Year / Citations / Stars / Code / Focus` columns | node fields |
| **bold names** in author cells | `authored_by` edges, resolved against people tables ("S. Hu" ≈ "Shengran Hu") |
| GitHub links shared by a paper row and a repo row | `has_code` edges |
| lab names appearing in a person's row | `member_of` edges |
| section headings | `category` nodes + `part_of` edges |
| citations / stars | deterministic confidence (log-scaled) |

`docs/index.html` is **self-contained** (canvas force layout, search, type filters,
click-to-inspect detail panel, drag/pan/zoom — no external scripts). It works from
`file://`, and putting it at `docs/index.html` makes the repo one Settings-toggle away
from a GitHub Pages site.

### 2 · Carry curator knowledge in an overlay

The tables can't say "DGM builds on AI-GAs builds on the Gödel Machine". Write that
once in `knowledge/enrichments.json` (`{"nodes": [...], "edges": [{"src","dst","type"}]}`)
— it survives every regeneration. If `NVIDIA_API_KEY` is set (free: build.nvidia.com),
propose more lineage edges for review at zero Claude-token cost:

```bash
python3 scripts/awesome_kg.py nim-enrich knowledge/graph.json
```

### 3 · Keep it honest — freshness automation

```bash
python3 scripts/check_freshness.py README.md --report freshness-report.md
```

Probes every link concurrently (HEAD→GET fallback); bot-walled domains (x.com,
linkedin, scholar) are WARN not DEAD. Exit 1 only on genuinely dead links. Install the
weekly GitHub Action (cron + manual dispatch) that runs it and opens/updates an issue
on failures — see the workflow template below. **If the README claims automated
checks, this is what makes the claim true.**

```yaml
# .github/workflows/freshness.yml
name: freshness
on:
  schedule: [{cron: "0 6 * * 1"}]   # Mondays 06:00 UTC
  workflow_dispatch:
jobs:
  links:
    runs-on: ubuntu-latest
    permissions: {issues: write, contents: read}
    steps:
      - uses: actions/checkout@v4
      - name: Check links
        id: check
        run: python3 scripts/check_freshness.py README.md --report freshness-report.md
      - name: Open issue on dead links
        if: failure()
        env: {GH_TOKEN: "${{ github.token }}"}
        run: |
          title="🔗 Dead links found by weekly freshness check"
          existing=$(gh issue list --state open --search "$title" --json number --jq '.[0].number')
          if [ -n "$existing" ]; then gh issue comment "$existing" --body-file freshness-report.md
          else gh issue create --title "$title" --body-file freshness-report.md --label maintenance; fi
```

## Workflow for the agent

1. **Compile**: run `awesome_kg.py build` on the README. Read the printed stats — if a
   table contributed 0 nodes, its header didn't match; extend `_ROLES`/`_NAME_TYPES`
   rather than hand-writing nodes.
2. **Enrich**: author `knowledge/enrichments.json` from what YOU know of the domain
   (lineage, influence) — cite the timeline/sections of the README itself where
   possible. Run `nim-enrich` only when a key is present; always review its edges.
3. **Install freshness**: copy `check_freshness.py` into the repo's `scripts/`, add the
   workflow. Run it once locally to baseline (expect some bot-walled WARNs).
4. **Surface it**: add a "Living Knowledge" README section linking `docs/index.html`
   (raw + Pages URL), `knowledge/graph.json`, and the regen command. Update CHANGELOG.
5. **Verify**: `python3 -c "import json; json.load(open('knowledge/graph.json'))"`,
   open the HTML, click a node, confirm edges. The graph must round-trip: every edge's
   src/dst exists.

## Quality bar

- Every node traceable to a README row (or the overlay) — the compiler never invents.
- Person resolution must merge "S. Hu" / "Shengran Hu" / "**Hu**" into ONE node.
- The HTML must work offline from `file://` — no CDN scripts, ever.
- Freshness must never cry wolf: bot-walled ≠ dead.
