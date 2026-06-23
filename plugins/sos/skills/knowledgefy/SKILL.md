---
name: knowledgefy
description: "Turn ANY single source into a self-contained INTERACTIVE knowledge-graph web page in one shot — a GitHub repo, a website/article, a YouTube or podcast URL, a local PDF/audio/video/notebook, a folder, or pasted text. Produces a portable tabbed HTML artifact (Map: incremental force-graph with click-to-deepen L1→L3→L5 living-knowledge layers · Infographic: a NotebookLM-style one-pager · Ask: graph-grounded Q&A) and prints its shareable URL. Use ONLY when the user explicitly wants to 'knowledgefy', 'kgfy', 'KG-fy', 'make/build a knowledge graph (map) of <X>', or 'visualize this source as a graph' — the fast, no-setup one-shot. It wraps DreamMakeTrue's `dmt.py kgfy` (the engine self-heals if down). NOT for: talking to / asking a person's grounded avatar, simulating a conversation, or turning a discussion into a post/essay/podcast (use `dreammaketrue`); multi-source topic OR persona research ranked by engagement (use `knowledge-graph`); turning an awesome-list repo into a living list (use `living-repo`); or a quick one-paragraph explainer (use `living-knowledge`)."
argument-hint: '<github-repo | url | youtube/podcast | file.pdf | folder | "pasted text"> [--title T]'
allowed-tools: Bash, Read, Write
metadata:
  type: integration
  portable: true
  cross-agent: true
  source: "https://github.com/wjlgatech/dreammaketrue"
---

# Skill: knowledgefy — any source → an interactive knowledge graph, one command

`/knowledgefy <source>` is the fast lane: hand it one source and get back a single,
self-contained, interactive **living-knowledge** web page (plus a NotebookLM-style infographic)
and a shareable URL. No room, no avatars, no setup. It is a thin wrapper over DreamMakeTrue's
`dmt.py kgfy` one-shot — this skill does **not** reimplement the engine or carry its own copy of
the script.

## Operating procedure

**1. Resolve `dmt.py`** (it lives in the sibling `dreammaketrue` skill — try these in order,
use the first that exists; `DMT` env overrides):

```bash
DMT="${DMT:-}"
for c in \
  "$DMT" \
  "$HOME/.claude/skills/dreammaketrue/scripts/dmt.py" \
  "$HOME/.hermes/skills/dreammaketrue/scripts/dmt.py" \
  "$(dirname "$0")/../dreammaketrue/scripts/dmt.py" \
  "$HOME/Documents/Projects/sos/plugins/sos/skills/dreammaketrue/scripts/dmt.py" ; do
  [ -n "$c" ] && [ -f "$c" ] && DMT="$c" && break
done
[ -f "$DMT" ] || { echo "knowledgefy: dmt.py not found. Install the dreammaketrue skill (bash plugins/sos/scripts/install-skills-global.sh) or set DMT=/path/to/dmt.py"; exit 1; }
```

**2. Run the one-shot** (the engine auto-starts if it's down — `kgfy` calls `ensure_api()`):

```bash
python3 "$DMT" kgfy "<source>"            # add --title "…" to label it; --out file.html to choose the path
```

Sources accepted (whatever `kgfy` already handles): a **GitHub repo URL**, any **website/article
URL**, a **YouTube/podcast URL**, a **local file** (`.pdf/.png/.mp3/.mp4/.ipynb` extracted via the
engine; `.md/.txt/.html/code` read directly), a **folder** (README + docs + a few binaries), or
**pasted text** (write it to a `.txt` first, then pass the path). Long sources can take a minute
or two — stream the progress lines, don't kill it.

**3. Surface the result.** `kgfy` prints a JSON object — read these and hand them to the user:

- `served_url` — open this; the engine serves the page as a real URL (Map + Infographic + Ask).
- `phone_url` — the same page on the LAN (open it on a phone on the same Wi-Fi).
- the written HTML file path (auto-opens on macOS) — the portable copy; Map + Infographic work
  offline, **Ask** needs the engine reachable.

If `served_url` is `null`, the engine couldn't publish (likely down/unreachable) — the local HTML
file still works for Map + Infographic; say so and point the user at the file.

## When to reach past this skill

`knowledgefy` is intentionally just the one-shot. The moment the user wants to **converse with**
the knowledge (ask a real person's grounded avatar, simulate a debate) or **express** it (a
LinkedIn post / essay / podcast in their voice), hand off to the `dreammaketrue` skill — it owns
the room → talk → express flow and the same engine. For ranked multi-source topic/persona
research use `knowledge-graph`; for an awesome-list repo use `living-repo`.

## Cross-agent note

`dmt.py` is zero-dependency stdlib Python, so Codex/OpenClaw can run the step-2 command directly;
Claude Code & Hermes also reach it by typing `/knowledgefy`. The engine itself lives in the
`dreammaketrue` repo — this skill, like `dreammaketrue`, is only a client.
