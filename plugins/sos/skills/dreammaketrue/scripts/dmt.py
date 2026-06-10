#!/usr/bin/env python3
"""dmt.py — zero-dependency CLI client for the DreamMakeTrue Participation Engine.

Any agent that can run a shell (Claude Code, Hermes, Codex, OpenClaw) drives the engine
through this one file: ingest any source, build a knowledge map + grounded avatars, talk
to the avatars, and express the conversation as a publishable artifact.

Stdlib only (urllib) — no pip install, runs on any Python 3.9+.

Env:
  DMT_API_URL   engine base URL          (default http://localhost:8001)
  DMT_REPO      local repo for autostart (default ~/Documents/Projects/dreammaketrue)

Commands:
  status                              engine health + provider/credit status
  start                               start the local API (launchd → uvicorn fallback)
  ingest <url-or-text>                any source → normalized document (provenance + warnings)
  analyze --minds "A,B" <src> [src…]  sources → knowledge map + person-map per mind → ROOM
  rooms                               list saved rooms (id · topic · minds)
  room <id>                           dump one full room (topic map, avatars, transcript)
  chat <room_id> "message" [--user N] talk to the room's grounded avatars (one turn)
  express <room_id> --contribution "…" [--format F] [--user N]
                                      room + your verbatim contribution → artifact
                                      F: linkedin_post|essay|podcast_script|video_brief|participation_brief
  library [avatars|topics|stats]      the shared cross-room knowledge base
  kgfy <repo|url|file|dir>            ANY source → ONE tabbed living-knowledge artifact
                                      (no room needed): GitHub repo/article/YouTube/podcast
                                      URL, local file (PDF·a/v via engine), or folder
  view <room_id> [--out map.html]     room → the same ONE tabbed artifact. Tabs:
                                      Map (INCREMENTAL — starts at concepts, each tap
                                      expands that node's web, inspector deepens L1→L3→L5)
                                      · Infographic (NotebookLM-style one-pager)
                                      · Ask (graph-grounded chat → engine /kg/chat: real
                                      paths + bridge nodes; "draft a post…" returns a full
                                      grounded artifact — agentic). Engine URL baked in.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = os.environ.get("DMT_API_URL", "http://localhost:8001").rstrip("/")
REPO = os.path.expanduser(os.environ.get("DMT_REPO", "~/Documents/Projects/dreammaketrue"))


def _req(method: str, path: str, body: dict | None = None, timeout: int = 600) -> dict:
    url = API + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _up() -> bool:
    try:
        return _req("GET", "/health", timeout=4).get("status") == "ok"
    except Exception:
        return False


def ensure_api() -> None:
    """Self-heal: if the engine is down, try launchd (macOS service), then a direct
    uvicorn start from a local clone. Clear instructions if neither exists."""
    if _up():
        return
    # 1. launchd service (the installed-machine path)
    try:
        uid = os.getuid()
        subprocess.run(
            ["launchctl", "kickstart", "-k", f"gui/{uid}/com.dreammaketrue.api"],
            capture_output=True,
            timeout=10,
        )
        for _ in range(20):
            time.sleep(1)
            if _up():
                print(f"engine: started via launchd → {API}", file=sys.stderr)
                return
    except Exception:
        pass
    # 2. direct uvicorn from a local clone
    py = os.path.join(REPO, "apps/api/.venv/bin/python")
    if os.path.exists(py):
        subprocess.Popen(
            [py, "-m", "uvicorn", "src.main:app", "--port", API.rsplit(":", 1)[-1]],
            cwd=os.path.join(REPO, "apps/api"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(30):
            time.sleep(1)
            if _up():
                print(f"engine: started via uvicorn → {API}", file=sys.stderr)
                return
    sys.exit(
        f"DreamMakeTrue engine is not reachable at {API}.\n"
        f"- If it runs on another machine: export DMT_API_URL=http://host:8001\n"
        f"- To install locally: git clone https://github.com/wjlgatech/dreammaketrue "
        f"&& see its CLAUDE.md → LOCAL DEV (needs ANTHROPIC_API_KEY or local Ollama)."
    )


# ── room helpers: turn a saved Room into grounded simulate/express payloads ──────


def _room(room_id: str) -> dict:
    room = _req("GET", f"/v1/engine/rooms/{room_id}")
    if room.get("error"):
        sys.exit(f"room not found: {room_id} (run `dmt.py rooms` to list)")
    return room


def _personas(room: dict) -> list[dict]:
    out = []
    for name, pm in (room.get("person_maps") or {}).items():
        pm = pm or {}
        out.append(
            {
                "person_name": name,
                "worldview_summary": pm.get("worldview_summary", ""),
                "top_mental_models": [
                    m.get("name", "") for m in (pm.get("mental_models") or [])[:5]
                ],
                "signature_phrases": pm.get("signature_phrases") or [],
                "certainty_mode": pm.get("certainty_mode", ""),
                "honest_limits": pm.get("honest_limits") or [],
            }
        )
    return out


def _grounding(room: dict) -> dict:
    tm = room.get("topic_map") or {}
    nodes = tm.get("nodes") or []
    return {
        "topic": tm.get("topic", ""),
        "key_claims": [
            n.get("summary") or n.get("name", "") for n in nodes if n.get("type") == "claim"
        ][:8],
        "concept_principles": [
            n.get("principle") or n.get("summary", "") for n in nodes if n.get("type") == "concept"
        ][:6],
    }


# ── commands ─────────────────────────────────────────────────────────────────────


def cmd_status(_: list[str]) -> dict:
    ensure_api()
    return _req("GET", "/v1/engine/status")


def cmd_start(_: list[str]) -> dict:
    ensure_api()
    return {"ok": True, "api": API}


def cmd_ingest(args: list[str]) -> dict:
    if not args:
        sys.exit("usage: dmt.py ingest <url-or-text>")
    ensure_api()
    return _req("POST", "/v1/engine/ingest", {"source": " ".join(args)})


def cmd_analyze(args: list[str]) -> dict:
    minds, user, sources = [], "Agent", []
    it = iter(args)
    for a in it:
        if a == "--minds":
            minds = [m.strip() for m in next(it, "").split(",") if m.strip()]
        elif a == "--user":
            user = next(it, "Agent")
        else:
            sources.append(a)
    if not sources or not minds:
        sys.exit('usage: dmt.py analyze --minds "Name A,Name B" <source> [source…]')
    ensure_api()
    job = _req(
        "POST",
        "/v1/engine/analyze/start",
        {"sources": sources, "speakers": minds, "user_name": user},
    )
    jid = job.get("job_id")
    print(f"analyze job {jid} — building knowledge map + {len(minds)} avatar(s)…", file=sys.stderr)
    while True:
        time.sleep(5)
        st = _req("GET", f"/v1/engine/analyze/status/{jid}")
        steps = st.get("steps") or {}
        done = sum(1 for v in steps.values() if v in ("done", "error"))
        print(f"  {done}/{len(steps)} steps · {st.get('status')}", file=sys.stderr)
        if st.get("status") in ("done", "error"):
            res = st.get("result") or st
            return {
                "room_id": res.get("room_id"),
                "topic": (res.get("topic_map") or {}).get("topic"),
                "minds": list((res.get("person_maps") or {}).keys()),
                "status": st.get("status"),
                "next": 'dmt.py chat <room_id> "your question"',
            }


def cmd_rooms(_: list[str]) -> dict:
    ensure_api()
    return _req("GET", "/v1/engine/rooms")


def cmd_room(args: list[str]) -> dict:
    if not args:
        sys.exit("usage: dmt.py room <room_id>")
    ensure_api()
    return _room(args[0])


def cmd_chat(args: list[str]) -> dict:
    user = "Agent"
    if "--user" in args:
        i = args.index("--user")
        user = args[i + 1]
        args = args[:i] + args[i + 2 :]
    if len(args) < 2:
        sys.exit('usage: dmt.py chat <room_id> "message" [--user Name]')
    ensure_api()
    room = _room(args[0])
    msg = " ".join(args[1:])
    body = {
        "topic_map_id": room["id"],
        "person_map_ids": room.get("speakers") or [],
        "user_opening": msg,
        "personas": _personas(room),
        **_grounding(room),
    }
    out = _req("POST", "/v1/engine/simulate", body)
    # fold the turn back into the room so the conversation is durable
    try:
        turns = [{"speaker": user, "content": msg}]
        for t in out.get("turns") or []:
            turns.append(t)
        _req(
            "PATCH",
            f"/v1/engine/rooms/{room['id']}",
            {"transcript": (room.get("transcript") or []) + turns},
        )
    except Exception:
        pass  # chat still succeeded; persistence is best-effort
    return out


def cmd_express(args: list[str]) -> dict:
    fmt, user, contrib, room_id = "linkedin_post", "Agent", "", ""
    it = iter(args)
    for a in it:
        if a == "--format":
            fmt = next(it, fmt)
        elif a == "--user":
            user = next(it, user)
        elif a == "--contribution":
            contrib = next(it, "")
        elif not room_id:
            room_id = a
    if not room_id or not contrib:
        sys.exit(
            'usage: dmt.py express <room_id> --contribution "your verbatim words" '
            "[--format linkedin_post|essay|podcast_script|video_brief|participation_brief] [--user Name]"
        )
    ensure_api()
    room = _room(room_id)
    g = _grounding(room)
    body = {
        "session_id": room["id"],
        "format": fmt,
        "user_name": user,
        "user_contribution": contrib,
        "turns": room.get("transcript") or [],
        "topic": g["topic"],
        "key_claims": g["key_claims"],
        "concept_principles": g["concept_principles"],
        "personas": _personas(room),
    }
    out = _req("POST", "/v1/engine/express", body)
    try:  # persist the artifact on the room (best-effort)
        _req("PATCH", f"/v1/engine/rooms/{room_id}", {"artifact": out})
    except Exception:
        pass
    return out


def cmd_library(args: list[str]) -> dict:
    ensure_api()
    what = args[0] if args else "avatars"
    if what == "stats":
        return _req("GET", "/v1/engine/library/stats")
    if what == "topics":
        return _req("GET", "/v1/engine/library/topics")
    return _req("GET", "/v1/engine/library/avatars")


# ── view: graph → ONE self-contained tabbed artifact (Map · Infographic · Ask) ──
# Tab 1 Map: force-directed canvas with INCREMENTAL display — starts at the concepts,
#   each click reveals that node's web (+N badges show what's hidden), and the inspector
#   deepens progressively (L1 → L3 → L5), the living-knowledge way.
# Tab 2 Infographic: the NotebookLM-style designed one-pager (light theme, scoped CSS).
# Tab 3 Ask: graph-grounded chat → engine /kg/chat (paths + bridge nodes computed
#   server-side); creation intents ("draft a post…") return a full artifact — agentic.
# One file, zero dependencies; chat needs the engine reachable (URL baked at generation).

_VIEW_HTML = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>__TITLE__ — living knowledge</title>
<style>
:root{color-scheme:dark}
body{margin:0;background:#0d0d0f;color:#e8e8e8;font:14px/1.5 -apple-system,Inter,system-ui;height:100vh;display:flex;flex-direction:column;overflow:hidden}
nav{display:flex;gap:6px;padding:9px 12px;border-bottom:1px solid #26262b;background:#121215;align-items:center;flex-shrink:0}
nav .t{background:none;border:1px solid #333;border-radius:8px;color:#aaa;padding:6px 16px;font-size:13px;cursor:pointer}
nav .t.on{background:#e8e8e8;color:#0d0d0f;border-color:#e8e8e8;font-weight:600}
nav .title{margin-left:auto;font-size:12px;color:#777;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:40%}
.tab{flex:1;display:none;overflow:hidden;position:relative}.tab.on{display:flex}
/* ── workspace: content (map/info) + a persistent Ask dock beside it ── */
#workspace{flex:1;display:flex;min-height:0}
#main{flex:1;display:flex;position:relative;min-width:0}
#ask-dock{width:380px;flex-shrink:0;display:flex;flex-direction:column;background:#0f0f12;border-left:1px solid #26262b;min-height:0}
.askhdr{display:flex;align-items:center;justify-content:space-between;padding:9px 12px;border-bottom:1px solid #26262b;font-size:13px;color:#bbb;flex-shrink:0}
.askhdr .badge{font-size:10px;color:#7bd88f;border:1px solid #2f4a36;border-radius:999px;padding:1px 8px}
@media(max-width:760px){#workspace{flex-direction:column}#ask-dock{width:auto;height:46vh;border-left:none;border-top:1px solid #26262b}#side{width:42%}}
/* ── map tab ── */
#tab-map{flex-direction:row}
#cv{flex:1;cursor:grab;touch-action:none}
#side{width:340px;border-left:1px solid #26262b;padding:14px;overflow-y:auto;background:#121215}
.meta{color:#888;font-size:11px;margin-bottom:10px}
.meta button{background:#1d1d22;color:#bbb;border:1px solid #333;border-radius:6px;padding:2px 8px;font-size:11px;cursor:pointer}
.hint{color:#666;font-size:12px}
.ty{font-size:10px;text-transform:uppercase;letter-spacing:.08em;padding:1px 6px;border-radius:4px;color:#0d0d0f;font-weight:700}
.t-concept{background:#6ab0f3}.t-claim{background:#d4a574}.t-evidence{background:#7bd88f}.t-question{background:#c08af3}
.sum{color:#ccc;margin:8px 0}
.layer{border:1px solid #26262b;border-radius:8px;padding:8px 10px;margin:8px 0;background:#16161a}
.layer h3{margin:0 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#9a8}
.ev{color:#7bd88f;font-style:italic;font-size:12px;margin:4px 0}.principle{color:#6ab0f3}
#panel button,.deep{background:#1d1d22;color:#bbb;border:1px solid #333;border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer;margin-top:6px}
#panel button:hover{color:#fff;border-color:#666}
.link{color:#d4a574;cursor:pointer;display:block;padding:2px 0;font-size:12px}
/* ── infographic tab (light, scoped) ── */
#tab-info{overflow-y:auto;background:#f4f2ec;color:#1c1f26;display:none}
#tab-info.on{display:block}
#tab-info *{box-sizing:border-box}
#tab-info .page{max-width:880px;margin:0 auto;padding:0 20px 48px;font-size:15px;line-height:1.55}
#tab-info header{background:linear-gradient(135deg,#1d2742,#3b2f63 60%,#7c4d2e);color:#fff;border-radius:0 0 26px 26px;padding:42px 34px 32px;margin:0 -20px}
#tab-info .kicker{font-size:11px;letter-spacing:.22em;text-transform:uppercase;opacity:.75}
#tab-info h1{font-size:clamp(24px,4.4vw,38px);line-height:1.15;margin:10px 0 6px;font-weight:800}
#tab-info .sub{opacity:.8;font-size:13px}
#tab-info .stats{display:flex;gap:12px;flex-wrap:wrap;margin:-26px 0 30px}
#tab-info .stat{flex:1;min-width:120px;background:#fff;border-radius:16px;padding:16px 18px;box-shadow:0 8px 24px rgba(25,28,40,.10)}
#tab-info .stat b{display:block;font-size:30px;font-weight:800;color:#3b2f63}
#tab-info .stat span{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#8a8377}
#tab-info h2{font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:#7c4d2e;margin:36px 0 14px;display:flex;align-items:center;gap:10px}
#tab-info h2:after{content:"";flex:1;height:1px;background:#ded8ca}
#tab-info .ideas{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
#tab-info .idea{background:#fff;border-radius:16px;padding:18px;box-shadow:0 4px 16px rgba(25,28,40,.07);position:relative}
#tab-info .idea-n{position:absolute;top:14px;right:16px;font-size:26px;font-weight:800;color:#ece7db}
#tab-info .idea h3{margin:0 38px 6px 0;font-size:16px;line-height:1.3;color:#1d2742}
#tab-info .idea p{margin:0 0 10px;font-size:13.5px;color:#4a4f5b}
#tab-info .principle{background:#f4efff;border-left:3px solid #6b4fd8;border-radius:8px;padding:8px 10px;font-size:12.5px;color:#3b2f63;margin-bottom:10px;font-weight:600}
#tab-info .chip{display:inline-block;background:#ece7db;color:#6b6354;border-radius:99px;padding:2px 10px;font-size:11px;margin:2px 4px 0 0}
#tab-info .chip.big{background:#fff;font-size:12.5px;padding:6px 14px;box-shadow:0 2px 8px rgba(25,28,40,.08);color:#3b2f63;font-weight:600}
#tab-info ol.claims{margin:0;padding:0;list-style:none;counter-reset:cl;columns:2;column-gap:18px}
#tab-info ol.claims li{counter-increment:cl;background:#fff;border-radius:12px;padding:13px 14px 13px 46px;margin:0 0 10px;font-size:13.5px;position:relative;break-inside:avoid;box-shadow:0 3px 12px rgba(25,28,40,.06)}
#tab-info ol.claims li:before{content:counter(cl,decimal-leading-zero);position:absolute;left:13px;top:12px;font-weight:800;color:#b3503f;font-size:13px}
#tab-info .quotes{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}
#tab-info .quote{background:#1d2742;color:#e9e5da;border-radius:14px;padding:16px 18px;font-size:13.5px;font-style:italic;line-height:1.6}
#tab-info footer{margin-top:42px;font-size:11px;color:#9a9385;text-align:center}
@media(max-width:640px){#tab-info ol.claims{columns:1}}
/* ── ask tab ── */
#tab-ask{flex-direction:column;background:#0f0f12}
#log{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:10px}
.msg{max-width:780px;border-radius:14px;padding:10px 14px;font-size:14px;white-space:pre-wrap;line-height:1.55}
.me{align-self:flex-end;background:#2b3a55}
.bot{align-self:flex-start;background:#1a1a1f;border:1px solid #26262b}
.bot.thinking{color:#888;font-style:italic}
.cite{display:inline-block;background:#26324a;color:#9cc0ff;border-radius:99px;padding:2px 10px;font-size:11px;margin:6px 6px 0 0;cursor:pointer;font-style:normal}
#askrow{display:flex;gap:8px;padding:12px;border-top:1px solid #26262b;flex-shrink:0}
#q{flex:1;background:#16161a;border:1px solid #333;border-radius:10px;color:#eee;padding:10px 12px;font-size:14px;outline:none}
#q:focus{border-color:#6ab0f3}
#send{background:#6ab0f3;color:#0d0d0f;border:none;border-radius:10px;padding:10px 18px;font-size:14px;font-weight:600;cursor:pointer}
#send:disabled{opacity:.4}
@media(max-width:700px){#tab-map{flex-direction:column}#side{width:auto;max-height:45%;border-left:none;border-top:1px solid #26262b}}
</style></head><body>
<nav>
<button class="t on" data-tab=map>🕸 Map</button>
<button class=t data-tab=info>📊 Infographic</button>
<span class=title>__TITLE__</span>
</nav>
<div id=workspace><div id=main>
<div id=tab-map class="tab on">
<canvas id=cv></canvas>
<div id=side>
<div class=meta>__META__ · tap a node to expand its web (+N = hidden neighbors) · <span id=visinfo></span> <button id=showall>show all</button></div>
<div id=panel class=hint>Tap a concept to begin. The map grows as you explore — and the inspector deepens layer by layer.</div>
</div>
</div>
<div id=tab-info class=tab>__INFO__</div>
</div><aside id=ask-dock>
<div class=askhdr><span>💬 Ask the graph</span><span class=badge>local · Ollama</span></div>
<div id=log><div class="msg bot">Ask this knowledge graph anything.
• "How does X connect to Y?" — answered with the real path through the graph
• "What are the hidden patterns here?" — bridge nodes, disconnected regions
• Agentic: "draft a LinkedIn post about the big idea" — returns the full piece, grounded
(engine: __API__)</div></div>
<div id=askrow><input id=q placeholder="Ask the graph — or ask it to create something…"><button id=send>Ask</button></div>
</aside></div>
<script type="application/json" id=g>__GRAPH__</script>
<script>
const G=JSON.parse(document.getElementById('g').textContent);
/* served (engine/LAN/tunnel) → same-origin chat, no CORS; opened as a file → baked engine URL */
const API=(location.protocol==='http:'||location.protocol==='https:')?location.origin:"__API__";
/* ── tabs ── */
function show(t){document.querySelectorAll('nav .t').forEach(b=>b.classList.toggle('on',b.dataset.tab===t));
document.querySelectorAll('.tab').forEach(d=>d.classList.toggle('on',d.id==='tab-'+t));
if(t==='map')rs()}
document.querySelectorAll('nav .t').forEach(b=>b.onclick=()=>show(b.dataset.tab));
/* ── map: incremental force graph ── */
const cv=document.getElementById('cv'),cx=cv.getContext('2d'),panel=document.getElementById('panel'),visinfo=document.getElementById('visinfo');
const COLOR={concept:'#6ab0f3',claim:'#d4a574',evidence:'#7bd88f',question:'#c08af3'};
let W,H,cw,ch;function rs(){cw=cv.clientWidth;ch=cv.clientHeight;W=cv.width=cw*devicePixelRatio;H=cv.height=ch*devicePixelRatio}
window.addEventListener('resize',rs);
const N=G.nodes.map((n,i)=>({...n,x:Math.cos(i*2.4)*(120+i*6),y:Math.sin(i*2.4)*(120+i*6),vx:0,vy:0}));
const byId=Object.fromEntries(N.map(n=>[n.id,n]));
const E=G.edges.filter(e=>byId[e.source]&&byId[e.target]);
const adj={};for(const e of E){(adj[e.source]=adj[e.source]||[]).push(e.target);(adj[e.target]=adj[e.target]||[]).push(e.source)}
/* INCREMENTAL: start with the concepts (the L1 skeleton); everything else appears as you explore */
const vis=new Set(N.filter(n=>n.type==='concept').map(n=>n.id));
if(!vis.size)N.forEach(n=>vis.add(n.id));
function reveal(n){(adj[n.id]||[]).forEach(i=>vis.add(i));updVis()}
function updVis(){visinfo.textContent=vis.size+'/'+N.length+' nodes shown'}
updVis();
document.getElementById('showall').onclick=()=>{N.forEach(n=>vis.add(n.id));updVis()};
let zoom=1.5,panX=0,panY=0,drag=null,sel=null,hov=null,depth=1;
function step(){const V=N.filter(n=>vis.has(n.id));
for(const a of V){for(const b of V){if(a===b)continue;const dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+0.01,f=2200/d2;a.vx+=dx*f/Math.sqrt(d2);a.vy+=dy*f/Math.sqrt(d2)}a.vx-=a.x*0.0015;a.vy-=a.y*0.0015}
for(const e of E){if(!vis.has(e.source)||!vis.has(e.target))continue;const s=byId[e.source],t=byId[e.target],dx=t.x-s.x,dy=t.y-s.y,d=Math.sqrt(dx*dx+dy*dy)+0.01,f=Math.max(-4,Math.min(4,(d-110)*0.01));s.vx+=dx/d*f;s.vy+=dy/d*f;t.vx-=dx/d*f;t.vy-=dy/d*f}
for(const n of V){if(n===drag)continue;n.vx*=0.86;n.vy*=0.86;n.x+=n.vx;n.y+=n.vy}}
const R=n=>n.type==='concept'?15:11;
function draw(){const k=devicePixelRatio;cx.setTransform(1,0,0,1,0,0);cx.clearRect(0,0,W,H);cx.setTransform(zoom*k,0,0,zoom*k,(cw/2+panX)*k,(ch/2+panY)*k);
cx.strokeStyle='#2a2a30';cx.lineWidth=1;
for(const e of E){if(!vis.has(e.source)||!vis.has(e.target))continue;const s=byId[e.source],t=byId[e.target];cx.beginPath();cx.moveTo(s.x,s.y);cx.lineTo(t.x,t.y);cx.stroke();
cx.fillStyle='#555';cx.font='7px sans-serif';cx.fillText(e.type||'',(s.x+t.x)/2,(s.y+t.y)/2)}
for(const n of N){if(!vis.has(n.id))continue;const r=R(n);cx.beginPath();cx.arc(n.x,n.y,r,0,7);cx.fillStyle=COLOR[n.type]||'#888';cx.globalAlpha=sel&&sel!==n&&hov!==n?0.45:1;cx.fill();
if(sel===n||hov===n){cx.strokeStyle='#fff';cx.lineWidth=2;cx.stroke()}cx.globalAlpha=1;
const hid=(adj[n.id]||[]).filter(i=>!vis.has(i)).length;
if(hid){cx.fillStyle='#e8b04a';cx.font='bold 9px sans-serif';cx.fillText('+'+hid,n.x-r-14,n.y+3)}
cx.fillStyle=hov===n?'#fff':'#ddd';cx.font='10px sans-serif';cx.fillText((n.name||'').slice(0,30),n.x+r+4,n.y+3)}}
function loop(){step();draw();requestAnimationFrame(loop)}
function pt(ev){const b=cv.getBoundingClientRect();return{x:((ev.clientX-b.left)-cw/2-panX)/zoom,y:((ev.clientY-b.top)-ch/2-panY)/zoom}}
function hit(p){return N.find(n=>{if(!vis.has(n.id))return false;const dx=p.x-n.x,dy=p.y-n.y,r=R(n)+6;if(dx*dx+dy*dy<r*r)return true;
const lw=Math.min(30,(n.name||'').length)*5.6;return p.x>n.x+R(n)&&p.x<n.x+R(n)+lw&&Math.abs(dy)<9})}
let panning=null,down=null,moved=false;
cv.addEventListener('pointerdown',ev=>{cv.setPointerCapture(ev.pointerId);down={x:ev.clientX,y:ev.clientY};moved=false;
const n=hit(pt(ev));if(n){drag=n}else{panning={x:ev.clientX-panX,y:ev.clientY-panY}}});
cv.addEventListener('pointermove',ev=>{if(down&&Math.hypot(ev.clientX-down.x,ev.clientY-down.y)>5)moved=true;
if(drag&&moved){const p=pt(ev);drag.x=p.x;drag.y=p.y;drag.vx=drag.vy=0}
else if(panning&&moved){panX=ev.clientX-panning.x;panY=ev.clientY-panning.y}
else if(!down){hov=hit(pt(ev));cv.style.cursor=hov?'pointer':'grab'}});
cv.addEventListener('pointerup',ev=>{
if(!moved){const n=hit(pt(ev));if(n){selNode(n,1)}else{sel=null;inspect()}}
drag=null;panning=null;down=null});
cv.addEventListener('wheel',ev=>{ev.preventDefault();zoom=Math.min(5,Math.max(0.3,zoom*(ev.deltaY<0?1.1:0.9)))},{passive:false});
function selNode(n,d){sel=n;depth=d;reveal(n);inspect()}
function esc(s){const d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML}
/* INCREMENTAL inspector: L1 → (deeper) → L3 → (deeper) → L5 — stop at the depth the moment needs */
function inspect(){const n=sel;if(!n){panel.className='hint';panel.textContent='Tap a node.';return}panel.className='';
let h=`<span class="ty t-${esc(n.type)}">${esc(n.type)}</span> <b>${esc(n.name)}</b><div class=sum>${esc(n.summary||'')}</div>`;
if(depth>=2){
if(n.principle)h+=`<div class=layer><h3>L3 · principle</h3><div class=principle>${esc(n.principle)}</div>${(n.transfer_domains||[]).map(t=>`<div class=hint>transfers → ${esc(t)}</div>`).join('')}</div>`;
if(n.limitation)h+=`<div class=layer><h3>limitation</h3>${esc(n.limitation)}</div>`;
if(!n.principle&&!n.limitation)h+=`<div class=layer><h3>L3</h3><div class=hint>no deeper layer recorded for this node</div></div>`}
if(depth>=3){const nb=E.filter(e=>e.source===n.id||e.target===n.id).map(e=>{const o=byId[e.source===n.id?e.target:e.source];return `<span class=link data-id="${esc(o.id)}">${esc(e.type)} → ${esc(o.name)}</span>`}).join('');
h+=`<div class=layer><h3>L5 · the web around it</h3>${nb||'<div class=hint>no edges</div>'}</div>`;
const evs=N.filter(o=>o.type==='evidence'&&E.some(e=>(e.source===n.id&&e.target===o.id)||(e.target===n.id&&e.source===o.id)));
if(evs.length)h+=`<div class=layer><h3>verbatim evidence</h3>${evs.map(o=>`<div class=ev>“${esc(o.summary)}”</div>`).join('')}</div>`}
if(depth<3)h+=`<button class=deep id=deep>go deeper → ${depth===1?'L3 (principle)':'L5 (the web + evidence)'}</button>`;
panel.innerHTML=h;
const d=document.getElementById('deep');if(d)d.onclick=()=>{depth++;inspect()};
panel.querySelectorAll('.link').forEach(a=>a.onclick=()=>{const o=byId[a.dataset.id];if(o){vis.add(o.id);selNode(o,1)}})}
window.dmtSelect=q=>{const n=N.find(x=>(x.name||'').toLowerCase().includes(String(q).toLowerCase()));if(n){vis.add(n.id);selNode(n,3)}return n?n.name:null};
window.dmtScreen=q=>{const n=N.find(x=>(x.name||'').toLowerCase().includes(String(q).toLowerCase()));if(!n)return null;
const b=cv.getBoundingClientRect();return{x:n.x*zoom+cw/2+panX+b.left,y:n.y*zoom+ch/2+panY+b.top,name:n.name}};
rs();loop();
/* ── ask: graph-grounded chat → engine /kg/chat ── */
const log=document.getElementById('log'),q=document.getElementById('q'),send=document.getElementById('send');
const hist=[];
function add(cls,text){const d=document.createElement('div');d.className='msg '+cls;d.textContent=text;log.appendChild(d);log.scrollTop=log.scrollHeight;return d}
async function ask(){const question=q.value.trim();if(!question)return;q.value='';send.disabled=true;
add('me',question);hist.push({role:'user',content:question});
const t=add('bot thinking','thinking — walking the graph…');
try{
const r=await fetch(API+'/v1/engine/kg/chat',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({graph:{nodes:G.nodes,edges:G.edges},question,history:hist.slice(-8),user_name:'You'})});
if(!r.ok)throw new Error('engine '+r.status);
const out=await r.json();
t.className='msg bot';t.textContent=out.answer||'(no answer)';
hist.push({role:'assistant',content:out.answer||''});
for(const id of out.cited_node_ids||[]){const n=byId[id];if(!n)continue;
const c=document.createElement('span');c.className='cite';c.textContent='🕸 '+n.name;
c.onclick=()=>{vis.add(n.id);selNode(n,3);show('map')};t.appendChild(c)}
}catch(e){t.className='msg bot';
t.textContent='Engine unreachable at '+API+' — start DreamMakeTrue (dmt.py start) or regenerate this file with DMT_API_URL pointing at a reachable engine. ('+e.message+')'}
send.disabled=false;q.focus()}
send.onclick=ask;q.addEventListener('keydown',e=>{if(e.key==='Enter')ask()});
window.dmtAsk=t=>{q.value=t;ask();return 'asked'};
</script></body></html>"""


def _infographic_body(graph: dict, title: str) -> str:
    """The infographic tab's inner HTML (styles live scoped in _VIEW_HTML). Deterministic —
    built straight from the graph, no extra LLM call. Print-friendly via the page CSS."""
    import html as _h

    e = _h.escape
    nodes = graph["nodes"]
    concepts = [n for n in nodes if n.get("type") == "concept"]
    claims = [n for n in nodes if n.get("type") == "claim"]
    evidence = [n for n in nodes if n.get("type") == "evidence"]
    transfers = sorted({t for c in concepts for t in (c.get("transfer_domains") or [])})

    # Built with explicit locals (not nested f-string lookups) — auto-formatters normalize
    # quote styles, and same-quote nesting inside an f-string is Python 3.12+ only.
    cards = []
    for i, c in enumerate(concepts[:6]):
        name, summary = e(c.get("name", "")), e(c.get("summary", ""))
        principle = c.get("principle") or ""
        p_html = f"<div class=principle>⚡ {e(principle)}</div>" if principle else ""
        t_html = "".join(
            f"<span class=chip>{e(t)}</span>"
            for t in (c.get("transfer_domains") or [])[:3]
        )
        cards.append(
            f"<div class=idea><div class=idea-n>{i + 1:02d}</div><h3>{name}</h3>"
            f"<p>{summary}</p>{p_html}{t_html}</div>"
        )
    idea_cards = "".join(cards)
    claim_rows = "".join(
        f"<li>{e(c.get('summary') or c.get('name', ''))}</li>" for c in claims[:8]
    )
    quote_cards = "".join(
        f"<div class=quote>“{e((q.get('summary') or '')[:280])}”</div>"
        for q in evidence[:6]
    )
    chips = "".join(f"<span class='chip big'>{e(t)}</span>" for t in transfers[:14])

    ideas_sec = (
        f"<h2>The Big Ideas</h2><div class=ideas>{idea_cards}</div>"
        if idea_cards
        else ""
    )
    claims_sec = (
        f"<h2>Key Claims</h2><ol class=claims>{claim_rows}</ol>" if claim_rows else ""
    )
    quotes_sec = (
        f"<h2>In Their Own Words</h2><div class=quotes>{quote_cards}</div>"
        if quote_cards
        else ""
    )
    chips_sec = (
        f"<h2>Where These Ideas Transfer</h2><div>{chips}</div>" if chips else ""
    )
    return (
        f"<div class=page><header><div class=kicker>Living Knowledge · Infographic</div>"
        f"<h1>{e(title[:140])}</h1>"
        f"<div class=sub>compressed from the source by the DreamMakeTrue engine — "
        f"every claim grounded, every quote verbatim</div></header>"
        f"<div class=stats>"
        f"<div class=stat><b>{len(concepts)}</b><span>big ideas</span></div>"
        f"<div class=stat><b>{len(claims)}</b><span>key claims</span></div>"
        f"<div class=stat><b>{len(evidence)}</b><span>verbatim quotes</span></div>"
        f"<div class=stat><b>{len(graph['edges'])}</b><span>connections</span></div>"
        f"</div>{ideas_sec}{claims_sec}{quotes_sec}{chips_sec}"
        f"<footer>generated by DreamMakeTrue · kgfy — Map tab for full depth · "
        f"Ask tab to converse with this knowledge</footer></div>"
    )


def _render_view(graph: dict, title: str, meta: str, out_path: str, slug: str) -> dict:
    """ONE self-contained tabbed artifact: Map (incremental) · Infographic · Ask (chat)."""
    page = (
        _VIEW_HTML.replace("__TITLE__", title.replace("<", "&lt;")[:120])
        .replace("__META__", meta)
        .replace("__API__", API)
        .replace("__INFO__", _infographic_body(graph, title))
        .replace(
            "__GRAPH__", json.dumps(graph, ensure_ascii=False).replace("</", "<\\/")
        )
    )
    out_path = out_path or os.path.join(
        os.path.expanduser("~/Desktop")
        if os.path.isdir(os.path.expanduser("~/Desktop"))
        else ".",
        f"dmt-map-{slug}.html",
    )
    with open(out_path, "w") as f:
        f.write(page)
    out = {
        "html": out_path,
        "tabs": ["map (incremental)", "infographic", "ask (chat + agentic)"],
        "title": title,
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
    }
    # Publish to the engine so it serves the page (same-origin Ask — works from a phone on
    # the LAN / through a tunnel as a real link). Best-effort: a down engine skips this.
    try:
        pub = _req(
            "POST",
            "/v1/engine/artifacts",
            {"name": f"{slug or 'kgfy'}.html", "html": page},
            timeout=60,
        )
        out["served_url"] = pub.get("local_url")
        out["phone_url"] = pub.get("lan_url")
    except Exception:
        out["served_url"] = None
    if sys.platform == "darwin":  # best-effort: open it for the user
        subprocess.run(["open", out_path], capture_output=True)
    return out


def cmd_view(args: list[str]) -> dict:
    out_path = ""
    if "--out" in args:
        i = args.index("--out")
        out_path = args[i + 1]
        args = args[:i] + args[i + 2 :]
    if not args:
        sys.exit("usage: dmt.py view <room_id> [--out map.html]")
    ensure_api()
    room = _room(args[0])
    tm = room.get("topic_map") or {}
    nodes = tm.get("nodes") or []
    if not nodes:
        sys.exit(f"room {args[0]} has no topic-map nodes to visualize")
    graph = {"nodes": nodes, "edges": tm.get("edges") or []}
    title = tm.get("topic") or room.get("topic") or args[0]
    meta = f"{len(nodes)} nodes · {len(graph['edges'])} edges · room {room['id']}"
    out = _render_view(graph, title, meta, out_path, room["id"][:8])
    out["webapp"] = "http://localhost:3000 (richer, live view — open the room there)"
    return out


# Extensions the engine's /upload extractor handles better than a raw read (modality parsers:
# pypdf · vision · whisper). Everything else text-ish is read directly.
_BINARY_EXT = (
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".mp3",
    ".m4a",
    ".wav",
    ".mp4",
    ".mov",
    ".webm",
    ".ipynb",
    ".docx",
    ".pptx",
)


def _upload(paths: list[str]) -> str:
    """Local binary files → extracted text via the engine's /upload (stdlib multipart)."""
    boundary = "----dmtboundary7f9c2a"
    body = bytearray()
    for p in paths:
        with open(p, "rb") as f:
            data = f.read()
        name = os.path.basename(p)
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="files"; '
            f'filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'
        ).encode()
        body += data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    r = urllib.request.Request(
        API + "/v1/engine/upload",
        data=bytes(body),
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(r, timeout=1800) as resp:
        out = json.loads(resp.read().decode())
    parts = []
    for f in out.get("files") or out.get("results") or (out if isinstance(out, list) else []):
        if f.get("text"):
            parts.append(f"\n\n===== {f.get('filename')} =====\n{f['text']}")
    return "".join(parts)


def _gather_repo(path: str, cap: int = 90_000) -> str:
    """A local repo/dir → one corpus: README first, then docs/markdown/txt, then up to 5
    binary docs (PDF etc.) through the engine's extractors."""
    parts: list[str] = []
    take: list[str] = []
    binaries: list[str] = []
    for name in sorted(os.listdir(path)):
        if name.lower().startswith("readme"):
            take.append(os.path.join(path, name))
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        for f in sorted(files):
            full = os.path.join(root, f)
            if f.endswith((".md", ".mdx", ".rst", ".txt")) and not f.lower().startswith("readme"):
                take.append(full)
            elif f.lower().endswith(_BINARY_EXT) and len(binaries) < 5:
                binaries.append(full)
    total = 0
    for p in take:
        try:
            t = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        rel = os.path.relpath(p, path)
        chunk = f"\n\n===== {rel} =====\n{t}"
        parts.append(chunk)
        total += len(chunk)
        if total > cap:
            break
    if binaries and total < cap:
        try:
            parts.append(_upload(binaries))
        except Exception as e:  # noqa: BLE001 — binaries are best-effort extras
            print(f"kgfy: binary extraction skipped ({e})", file=sys.stderr)
    return "".join(parts)[:cap]


def cmd_kgfy(args: list[str]) -> dict:
    """kgfy: ANY source → detailed living-knowledge map, one command. No room/avatars —
    straight to the topic-map engine (chunked extraction) and the interactive HTML."""
    out_path, title = "", ""
    it, rest = iter(args), []
    for a in it:
        if a == "--out":
            out_path = next(it, "")
        elif a == "--title":
            title = next(it, "")
        else:
            rest.append(a)
    if not rest:
        sys.exit("usage: dmt.py kgfy <github-url | url | file | dir> [--out map.html] [--title T]")
    src = rest[0]
    ensure_api()

    if os.path.isdir(src):  # local repo / folder → README + docs corpus (+ a few binaries)
        text = _gather_repo(src)
        title = title or os.path.basename(os.path.abspath(src))
    elif os.path.isfile(src):
        title = title or os.path.basename(src)
        if src.lower().endswith(_BINARY_EXT):  # PDF / image / audio / video / notebook …
            print(f"kgfy: extracting text from {title} via engine…", file=sys.stderr)
            text = _upload([src])[:90_000]
        else:  # plain text-ish: md, txt, html, code, …
            text = open(src, encoding="utf-8", errors="ignore").read()[:90_000]
        if not text.strip():
            sys.exit(f"no text could be extracted from {src}")
    else:  # URL (github repo / article / YouTube / podcast …) → engine ingestion (tiered)
        doc = _req("POST", "/v1/engine/ingest", {"source": src}, timeout=1800)
        text = (doc.get("text") or "")[:90_000]
        title = title or doc.get("title") or src
        if not text:
            sys.exit(f"ingestion returned no text for {src} (warnings: {doc.get('warnings')})")

    print(f"kgfy: extracting living-knowledge map from {len(text)} chars…", file=sys.stderr)
    tm = _req("POST", "/v1/engine/topic-map", {"source_text": text}, timeout=1800)
    nodes = tm.get("nodes") or []
    if not nodes:
        sys.exit(f"extraction produced no nodes (engine said: {str(tm)[:300]})")
    graph = {"nodes": nodes, "edges": tm.get("edges") or []}
    slug = "".join(c if c.isalnum() else "-" for c in title.lower())[:32].strip("-")
    meta = f"{len(nodes)} nodes · {len(graph['edges'])} edges · kgfy of {title[:60]}"
    # The engine labels pasted text "user-provided text" — prefer the real source's name then.
    topic = tm.get("topic") or ""
    if not topic or topic.lower().startswith("user-provided"):
        topic = title
    return _render_view(graph, topic, meta, out_path, slug or "kgfy")


COMMANDS = {
    "status": cmd_status,
    "start": cmd_start,
    "ingest": cmd_ingest,
    "analyze": cmd_analyze,
    "rooms": cmd_rooms,
    "room": cmd_room,
    "chat": cmd_chat,
    "express": cmd_express,
    "library": cmd_library,
    "view": cmd_view,
    "kgfy": cmd_kgfy,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    fn = COMMANDS.get(cmd)
    if not fn:
        sys.exit(f"unknown command: {cmd}\n{__doc__}")
    try:
        print(json.dumps(fn(sys.argv[2:]), indent=2, ensure_ascii=False))
    except urllib.error.HTTPError as e:
        sys.exit(f"engine error {e.code}: {e.read().decode()[:500]}")


if __name__ == "__main__":
    main()
