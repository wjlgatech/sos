#!/usr/bin/env python3
"""kg.py — assemble a topic/persona knowledge graph from extracted nodes+edges.

Zero external deps (stdlib only), so it runs on any machine. The AGENT gathers + extracts
(per SKILL.md) into a graph.json; this script does the deterministic part:

  • validate the schema
  • DEDUP nodes by entity overlap (Jaccard overlap coefficient — ported from last30days
    cluster.py: merges "PagedAttention" / "Paged Attention" / "vLLM paging" into one node)
  • compute ENGAGEMENT-WEIGHTED CONFIDENCE per edge:
        confidence = clamp(source_quality × freshness × (0.5 + 0.5·engagement_norm) × corroboration)
  • render a self-contained dark-mode HTML view (no external scripts)

Usage:
  kg.py schema topic|persona            # print the target JSON template
  kg.py build graph.json [--mode topic|persona] [--out out.html]
"""

from __future__ import annotations

import html
import json
import math
import re
import sys
from datetime import datetime, timezone

# Per-platform quality baseline (last30days signals.py). Unknown → 0.6.
_SOURCE_QUALITY = {
    "docs": 1.0,
    "paper": 1.0,
    "arxiv": 1.0,
    "github": 0.9,
    "hackernews": 0.8,
    "hn": 0.8,
    "youtube": 0.85,
    "official": 0.95,
    "blog": 0.7,
    "reddit": 0.6,
    "x": 0.68,
    "twitter": 0.68,
    "tiktok": 0.5,
    "polymarket": 0.5,
    "news": 0.75,
}
_TOPIC_EDGES = {"supports", "contradicts", "causes", "part_of", "transfers_to", "relates_to"}
_PERSONA_EDGES = {
    "holds",
    "builds_on",
    "criticizes",
    "collaborates_with",
    "influenced_by",
    "relates_to",
}
_STOP = {
    "the",
    "a",
    "an",
    "of",
    "and",
    "or",
    "to",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "it",
    "this",
    "that",
    "new",
    "how",
    "why",
    "what",
    "vs",
    "using",
    "your",
    "you",
}


# ── entity-overlap dedup (Jaccard overlap coefficient) ──────────────────────────
def _tokens(s: str) -> set[str]:
    # Split camelCase/PascalCase first so "PagedAttention" ≈ "Paged Attention".
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s or "")
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in _STOP and len(t) > 2}


def _overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))  # tolerant of short-vs-long names


def _same_entity(
    a_name: set[str], a_full: set[str], b_name: set[str], b_full: set[str], thresh: float
) -> bool:
    """Same node if NAMES overlap strongly (≥0.7, both ≥2 meaningful tokens — so 'vLLM' and
    'vLLM paging' don't merge), OR name+summary overlap clears the stricter `thresh`."""
    if len(a_name) >= 2 and len(b_name) >= 2 and _overlap(a_name, b_name) >= 0.7:
        return True
    return _overlap(a_full, b_full) >= thresh


def _dedup_nodes(nodes: list[dict], thresh: float = 0.85) -> tuple[list[dict], dict[str, str]]:
    """Merge near-duplicate nodes of the same type. Returns (kept, id_remap)."""
    kept: list[tuple[dict, set[str], set[str]]] = []  # (node, name_sig, full_sig)
    remap: dict[str, str] = {}
    for n in nodes:
        nsig = _tokens(n.get("name", ""))
        fsig = _tokens(f"{n.get('name', '')} {n.get('summary', '')}")
        hit = None
        for k, k_name, k_full in kept:
            if k.get("type") == n.get("type") and _same_entity(nsig, fsig, k_name, k_full, thresh):
                hit = k
                break
        if hit:
            remap[n["id"]] = hit["id"]
            hit.setdefault("sources", []).extend(n.get("sources", []))  # merge provenance
        else:
            remap[n["id"]] = n["id"]
            kept.append((n, nsig, fsig))
    return [k[0] for k in kept], remap


# ── engagement-weighted confidence ──────────────────────────────────────────────
def _quality(src: dict) -> float:
    blob = f"{src.get('url', '')} {src.get('platform', '')}".lower()
    for key, q in _SOURCE_QUALITY.items():
        if key in blob:
            return q
    return 0.6


def _freshness(src: dict) -> float:
    d = str(src.get("date", "") or "")
    m = re.search(r"(\d{4})-(\d{1,2})", d) or re.search(r"(\d{4})", d)
    if not m:
        return 0.7  # undated → neutral
    try:
        year = int(m.group(1))
        month = int(m.group(2)) if m.lastindex and m.lastindex >= 2 else 6
        age_months = (datetime.now(timezone.utc).year - year) * 12 + (6 - month)
    except (ValueError, IndexError):
        return 0.7
    return max(0.35, min(1.0, 1.0 - age_months * 0.015))  # ~ -1.8%/mo, floor 0.35


def _engagement_norm(sources: list[dict]) -> float:
    eng = max((float(s.get("engagement", 0) or 0) for s in sources), default=0.0)
    return min(1.0, math.log1p(eng) / math.log1p(10_000))  # log-scaled, saturates ~10k


def _confidence(sources: list[dict]) -> float:
    if not sources:
        return 0.25
    quality = max(_quality(s) for s in sources)
    fresh = max(_freshness(s) for s in sources)
    eng = _engagement_norm(sources)
    corroboration = min(
        1.0, 0.7 + 0.15 * (len({s.get("url", i) for i, s in enumerate(sources)}) - 1)
    )
    return round(max(0.05, min(1.0, quality * fresh * (0.5 + 0.5 * eng) * corroboration)), 3)


# ── build ───────────────────────────────────────────────────────────────────────
def build(graph: dict, mode: str | None) -> dict:
    kind = mode or graph.get("kind") or "topic"
    nodes_in = graph.get("nodes", [])
    edges_in = graph.get("edges", [])
    if not nodes_in:
        raise ValueError("graph has no nodes")

    nodes, remap = _dedup_nodes(nodes_in)
    by_id = {n["id"]: n for n in nodes}
    valid_edges = _TOPIC_EDGES if kind == "topic" else _PERSONA_EDGES

    edges: list[dict] = []
    seen: set[tuple] = set()
    warnings: list[str] = []
    for e in edges_in:
        src, dst = remap.get(e.get("src"), e.get("src")), remap.get(e.get("dst"), e.get("dst"))
        etype = e.get("type", "relates_to")
        if src not in by_id or dst not in by_id or src == dst:
            continue
        if etype not in valid_edges:
            warnings.append(f"unknown edge type '{etype}' ({src}→{dst}) — kept as relates_to")
            etype = "relates_to"
        key = (src, dst, etype)
        if key in seen:
            continue
        seen.add(key)
        edges.append(
            {
                **e,
                "src": src,
                "dst": dst,
                "type": etype,
                "confidence": _confidence(e.get("sources", [])),
            }
        )

    for n in nodes:
        n["confidence"] = _confidence(n.get("sources", []))
        if not n.get("sources"):
            warnings.append(f"node '{n.get('name', n['id'])}' has NO source (unsupported)")
        if n.get("confidence", 0) < 0.35 or len({s.get("url") for s in n.get("sources", [])}) < 2:
            n["flag"] = "thin-evidence"

    if kind == "persona":
        mm = [n for n in nodes if n.get("type") == "mental_model"]
        weak = [m for m in mm if len(m.get("evidence", [])) < 2 or not m.get("limitation")]
        if len(mm) < 3:
            warnings.append(f"persona has only {len(mm)} mental_models (nuwa floor is 3)")
        if weak:
            warnings.append(f"{len(weak)} mental_model(s) missing 2+ evidence or a limitation")
        if not [n for n in nodes if n.get("type") == "honest_limit"]:
            warnings.append(
                "no honest_limit nodes — a faithful persona names where the record is thin"
            )

    return {
        "kind": kind,
        "subject": graph.get("subject", ""),
        "nodes": nodes,
        "edges": edges,
        "warnings": warnings,
        "stats": _stats(nodes, edges),
    }


def _stats(nodes: list[dict], edges: list[dict]) -> dict:
    def counts(items, k):
        out: dict[str, int] = {}
        for it in items:
            out[it.get(k, "?")] = out.get(it.get(k, "?"), 0) + 1
        return out

    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "node_types": counts(nodes, "type"),
        "edge_types": counts(edges, "type"),
    }


# ── self-contained HTML render (no external scripts) ────────────────────────────
def render_html(g: dict) -> str:
    e = html.escape
    rows = []
    for n in sorted(g["nodes"], key=lambda x: -x.get("confidence", 0)):
        flag = ' <span class="flag">thin</span>' if n.get("flag") else ""
        extra = ""
        if n.get("principle"):
            extra += f"<div class='sub'>principle: {e(n['principle'])}</div>"
        if n.get("limitation"):
            extra += f"<div class='sub'>limit: {e(n['limitation'])}</div>"
        for ev in n.get("evidence", [])[:3]:
            extra += f"<div class='ev'>“{e(str(ev))}”</div>"
        rows.append(
            f"<div class='node t-{e(n.get('type', '?'))}'><span class='conf'>{n.get('confidence', 0):.2f}</span>"
            f"<b>{e(n.get('name') or n.get('type', ''))}</b> <span class='ty'>{e(n.get('type', ''))}</span>{flag}"
            f"<div class='sum'>{e(n.get('summary', ''))}</div>{extra}</div>"
        )
    nm = {n["id"]: (n.get("name") or n.get("type", n["id"])) for n in g["nodes"]}
    elines = "".join(
        f"<div class='edge'><span class='conf'>{ed.get('confidence', 0):.2f}</span>"
        f"{e(nm.get(ed['src'], ed['src']))} <i>{e(ed['type'])}</i> {e(nm.get(ed['dst'], ed['dst']))}</div>"
        for ed in sorted(g["edges"], key=lambda x: -x.get("confidence", 0))
    )
    warn = "".join(f"<li>{e(w)}</li>" for w in g.get("warnings", []))
    st = g["stats"]
    return f"""<!doctype html><meta charset=utf-8><title>{e(g["subject"])} — {g["kind"]} graph</title>
<style>
:root{{color-scheme:dark}} body{{background:#0d0d0f;color:#e8e8e8;font:14px/1.5 -apple-system,Inter,system-ui;margin:0;padding:24px;max-width:860px}}
h1{{font-size:20px;margin:0 0 2px}} .meta{{color:#888;font-size:12px;margin-bottom:18px}}
h2{{font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:#9a8;margin:22px 0 8px}}
.node{{border:1px solid #26262b;border-left:3px solid #444;border-radius:8px;padding:8px 10px;margin:6px 0;background:#141417}}
.t-concept{{border-left-color:#6ab0f3}} .t-claim{{border-left-color:#d4a574}} .t-evidence{{border-left-color:#7bd88f}}
.t-worldview{{border-left-color:#c08af3}} .t-mental_model{{border-left-color:#6ab0f3}} .t-heuristic{{border-left-color:#d4a574}} .t-honest_limit{{border-left-color:#e57}}
.ty{{color:#888;font-size:11px;text-transform:uppercase}} .sum{{color:#bbb;margin-top:3px}} .sub{{color:#998;font-size:12px;margin-top:3px}}
.ev{{color:#7bd88f;font-size:12px;margin-top:3px;font-style:italic}}
.conf{{display:inline-block;min-width:34px;color:#0d0d0f;background:#9a8;border-radius:4px;padding:0 4px;font-weight:700;font-size:11px;margin-right:6px}}
.edge{{font-size:13px;padding:3px 0;border-bottom:1px solid #1c1c20}} .edge i{{color:#d4a574;font-style:normal}}
.flag{{background:#e57;color:#0d0d0f;border-radius:4px;padding:0 4px;font-size:10px}}
.warn{{background:#2a1a1a;border:1px solid #533;border-radius:8px;padding:8px 12px;color:#e99;font-size:12px}}
</style>
<h1>{e(g["subject"])}</h1>
<div class=meta>{e(g["kind"])} knowledge graph · {st["nodes"]} nodes · {st["edges"]} edges ·
node types {e(json.dumps(st["node_types"]))} · built by sos/knowledge-graph</div>
{f"<div class=warn><b>flags</b><ul>{warn}</ul></div>" if warn else ""}
<h2>Nodes (by confidence)</h2>{"".join(rows)}
<h2>Edges (by confidence)</h2>{elines}
<script type="application/json" id="graph">{e(json.dumps(g))}</script>
"""


_TOPIC_TMPL = {
    "kind": "topic",
    "subject": "<topic>",
    "nodes": [
        {
            "id": "n1",
            "type": "concept",
            "name": "<concept>",
            "summary": "<jargon-free>",
            "principle": "<transferable truth>",
            "transfer_domains": ["<domain>"],
            "sources": [{"url": "", "author": "", "date": "YYYY-MM", "engagement": 0, "quote": ""}],
        },
        {"id": "n2", "type": "claim", "name": "<claim>", "summary": "", "sources": [{"url": ""}]},
        {
            "id": "n3",
            "type": "evidence",
            "name": "<quote>",
            "summary": '"<verbatim>"',
            "sources": [{"url": ""}],
        },
    ],
    "edges": [
        {"src": "n1", "dst": "n2", "type": "causes", "sources": [{"url": ""}]},
        {"src": "n3", "dst": "n2", "type": "supports", "sources": [{"url": ""}]},
    ],
}
_PERSONA_TMPL = {
    "kind": "persona",
    "subject": "<person>",
    "nodes": [
        {
            "id": "p1",
            "type": "worldview",
            "summary": "<their core stance>",
            "sources": [{"url": ""}],
        },
        {
            "id": "m1",
            "type": "mental_model",
            "name": "<model>",
            "summary": "",
            "evidence": ["<verbatim 1>", "<verbatim 2>"],
            "limitation": "<where it breaks>",
            "sources": [{"url": "", "engagement": 0}],
        },
        {
            "id": "h1",
            "type": "heuristic",
            "name": "<rule>",
            "example": "<concrete>",
            "sources": [{"url": ""}],
        },
        {
            "id": "l1",
            "type": "honest_limit",
            "summary": "<thin part of the record>",
            "sources": [{"url": ""}],
        },
    ],
    "edges": [
        {"src": "p1", "dst": "m1", "type": "holds", "sources": [{"url": ""}]},
        {"src": "m1", "dst": "h1", "type": "builds_on", "sources": [{"url": ""}]},
    ],
}


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == "schema":
        print(json.dumps(_TOPIC_TMPL if argv[1] == "topic" else _PERSONA_TMPL, indent=2))
        return 0
    if len(argv) >= 2 and argv[0] == "build":
        path = argv[1]
        mode = None
        out = path.rsplit(".", 1)[0] + ".html"
        i = 2
        while i < len(argv):
            if argv[i] == "--mode" and i + 1 < len(argv):
                mode = argv[i + 1]
                i += 2
            elif argv[i] == "--out" and i + 1 < len(argv):
                out = argv[i + 1]
                i += 2
            else:
                i += 1
        with open(path) as f:
            g = build(json.load(f), mode)
        norm_path = path.rsplit(".", 1)[0] + ".graph.json"
        with open(norm_path, "w") as f:
            json.dump(g, f, indent=2)
        with open(out, "w") as f:
            f.write(render_html(g))
        st = g["stats"]
        print(f"✓ {g['kind']} graph: {st['nodes']} nodes, {st['edges']} edges")
        print(f"  node types: {st['node_types']}")
        print(f"  edge types: {st['edge_types']}")
        if g["warnings"]:
            print("  ⚠ flags:")
            for w in g["warnings"]:
                print(f"    - {w}")
        print(f"  → {norm_path}\n  → {out}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
