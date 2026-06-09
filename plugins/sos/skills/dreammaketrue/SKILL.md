---
name: dreammaketrue
description: "Drive the DreamMakeTrue Participation Engine: turn ANY source (YouTube/podcast/article/X/PDF/course/pasted text) into a knowledge map + grounded person-avatars, TALK to those avatars (they answer strictly from sourced evidence, refusing to hallucinate), and EXPRESS the conversation as a publishable, user-attributed artifact (LinkedIn post, essay, podcast script, video brief). Use when the user wants to deeply understand a source ('build a knowledge map of this video/PDF'), converse with a real person's grounded avatar ('what would Karpathy/Chamath say about X', 'let me ask the author'), ingest a whole course, or turn a discussion into a publishable artifact ('make this a LinkedIn post in my voice'). Triggers on 'knowledge map', 'talk to <person> about', 'ask <expert>', 'simulate a conversation with', 'turn this into a post/essay/podcast', 'ingest this course/video/PDF'. NOT for a quick factual lookup (just answer), a graph without avatars/conversation (use knowledge-graph), or a one-paragraph explainer (use living-knowledge)."
argument-hint: '[what you want — e.g. ''map this video'', ''chat <room> "question"'', ''express <room> as linkedin'']'
allowed-tools: Bash, Read, Write, WebFetch
metadata:
  type: integration
  portable: true
  cross-agent: true
  source: "https://github.com/wjlgatech/dreammaketrue"
---

# Skill: DreamMakeTrue — the Participation Engine, as a tool any agent can drive

DreamMakeTrue moves a person from _listener_ → _participant_ → _creator_: ingest a source,
build a **living knowledge map** + **grounded avatars** of the real speakers, let the user
**participate** (ask, push back), then **express** the exchange as an artifact carrying the
user's verbatim contribution. This skill is the thin client: everything runs through the
engine's REST API via one zero-dependency script.

```bash
DMT=~/.claude/skills/dreammaketrue/scripts/dmt.py   # or this skill's scripts/ dir
python3 $DMT status        # health + provider/credits (auto-starts a local engine if down)
```

`DMT_API_URL` (default `http://localhost:8001`) points at the engine; set it for a remote
machine. If the engine isn't running locally, `dmt.py` self-heals: launchd service →
uvicorn from a local clone → clear install instructions. **No other setup.**

## The flow (map → talk → express)

1. **Analyze: source(s) → room.** One call ingests everything (YouTube captions→yt-dlp→
   Whisper floor; web→trafilatura→Jina→stealth), builds the topic knowledge map AND a
   person-map per mind, and saves a durable **Room**:

   ```bash
   python3 $DMT analyze --minds "Andrej Karpathy" "https://youtube.com/watch?v=…"
   # → { room_id, topic, minds, next: 'chat …' }   (long: minutes; poll output streams)
   ```

   Minds can be ANY real people with public footprint — detected speakers or chosen names.

2. **Chat: participate in the room.** Avatars answer **only from their sourced person-map**
   (worldview, mental models, honest limits) — ungrounded names refuse rather than
   hallucinate. The turn is folded back into the room transcript automatically:

   ```bash
   python3 $DMT chat <room_id> "How should I think about risk in my first startup?" --user Paul
   ```

3. **Express: the conversation → publishable artifact.** The user's verbatim words MUST
   appear in the artifact (attribution is sacred — pass them via `--contribution`):
   ```bash
   python3 $DMT express <room_id> --contribution "the user's exact words" \
       --format linkedin_post --user Paul
   # formats: linkedin_post · essay · podcast_script · video_brief · participation_brief
   ```

## Supporting commands

| Command                            | Use                                                              |
| ---------------------------------- | ---------------------------------------------------------------- |
| `ingest <url-or-text>`             | just normalize a source → document (provenance, warnings)        |
| `rooms` / `room <id>`              | list / load saved rooms (resume any prior conversation)          |
| `library [avatars\|topics\|stats]` | the shared cross-room knowledge base (reuse already-built minds) |
| `status` / `start`                 | engine health + credits / force-start the local engine           |

## Agent guidance

- **Reuse before rebuilding:** check `library avatars` first — an already-built mind
  (e.g. `chamath-palihapitiya`, `andrej-karpathy`) means `analyze` is instant for that
  person (corpus-hash dedup). Don't re-analyze a source that already has a room (`rooms`).
- **Be honest about grounding:** if `chat` returns `[ungrounded]`, the avatar was never
  built — run `analyze` with sources for that person; don't fake a reply.
- **Attribution is sacred:** `express` requires the user's _verbatim_ contribution. Never
  substitute your own paraphrase.
- **Long calls:** `analyze` can take minutes (ingest + N research agents). Stream the
  progress lines; don't kill it.
- **Whole courses:** for a learn.deeplearning.ai (or similar) course the engine has a
  dedicated route — `POST /v1/engine/ingest-course` with `{"url": …}` (see the repo's
  CLAUDE.md API table); use `ingest` for single lessons.

## Cross-agent install (once per machine)

```bash
git clone https://github.com/wjlgatech/sos.git && cd sos
bash plugins/sos/scripts/install-skills-global.sh        # symlinks → ~/.claude/skills + ~/.hermes/skills
```

Claude Code & Hermes auto-trigger on the description; Codex/OpenClaw call
`scripts/dmt.py` directly (zero-dep stdlib Python). The engine itself lives in the
`dreammaketrue` repo — this skill is only the client.
