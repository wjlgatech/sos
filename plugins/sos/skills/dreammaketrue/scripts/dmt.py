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
  view <room_id> [--out map.html]     room → self-contained INTERACTIVE living-knowledge
                                      graph (force layout + click-to-deepen L1→L3→L5);
                                      one HTML file, zero deps, opens automatically
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


# ── view: room → self-contained interactive living-knowledge graph (HTML) ───────
# Force-directed canvas + click-to-deepen inspector — the webapp's KnowledgeGraph,
# portable: one file, zero dependencies, works offline, shareable.

_VIEW_HTML = """<!doctype html><meta charset=utf-8><title>__TITLE__ — living knowledge</title>
<style>
:root{color-scheme:dark}body{margin:0;background:#0d0d0f;color:#e8e8e8;font:13px/1.5 -apple-system,Inter,system-ui;overflow:hidden}
#wrap{display:flex;height:100vh}#cv{flex:1;cursor:grab}
#side{width:340px;border-left:1px solid #26262b;padding:16px;overflow-y:auto;background:#121215}
h1{font-size:15px;margin:0 0 4px}.meta{color:#888;font-size:11px;margin-bottom:10px}
.hint{color:#666;font-size:12px}.ty{font-size:10px;text-transform:uppercase;letter-spacing:.08em;padding:1px 6px;border-radius:4px;color:#0d0d0f;font-weight:700}
.t-concept{background:#6ab0f3}.t-claim{background:#d4a574}.t-evidence{background:#7bd88f}.t-question{background:#c08af3}
.sum{color:#ccc;margin:8px 0}.layer{border:1px solid #26262b;border-radius:8px;padding:8px 10px;margin:8px 0;background:#16161a}
.layer h3{margin:0 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#9a8}
.ev{color:#7bd88f;font-style:italic;font-size:12px;margin:4px 0}.principle{color:#6ab0f3}
button{background:#1d1d22;color:#bbb;border:1px solid #333;border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer;margin-top:6px}
button:hover{color:#fff;border-color:#666}.link{color:#d4a574;cursor:pointer;display:block;padding:2px 0;font-size:12px}
</style>
<div id=wrap><canvas id=cv></canvas><div id=side>
<h1>__TITLE__</h1><div class=meta>__META__ · drag nodes · scroll to zoom · click a node, then “deeper” — stop at the depth the moment needs</div>
<div id=panel class=hint>Click a node to open its living-knowledge layers.</div></div></div>
<script type="application/json" id=g>__GRAPH__</script>
<script>
const G=JSON.parse(document.getElementById('g').textContent);
const cv=document.getElementById('cv'),cx=cv.getContext('2d'),panel=document.getElementById('panel');
const COLOR={concept:'#6ab0f3',claim:'#d4a574',evidence:'#7bd88f',question:'#c08af3'};
let W,H;function rs(){W=cv.width=cv.clientWidth*devicePixelRatio;H=cv.height=cv.clientHeight*devicePixelRatio}
window.addEventListener('resize',rs);
const N=G.nodes.map((n,i)=>({...n,x:Math.cos(i*2.4)*(120+i*6),y:Math.sin(i*2.4)*(120+i*6),vx:0,vy:0}));
const byId=Object.fromEntries(N.map(n=>[n.id,n]));
const E=G.edges.filter(e=>byId[e.source]&&byId[e.target]);
let zoom=1.6,panX=0,panY=0,drag=null,sel=null,depth=1;
function step(){for(const a of N){for(const b of N){if(a===b)continue;const dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+0.01,f=2200/d2;a.vx+=dx*f/Math.sqrt(d2);a.vy+=dy*f/Math.sqrt(d2)}a.vx-=a.x*0.0015;a.vy-=a.y*0.0015}
for(const e of E){const s=byId[e.source],t=byId[e.target],dx=t.x-s.x,dy=t.y-s.y,d=Math.sqrt(dx*dx+dy*dy)+0.01,f=Math.max(-4,Math.min(4,(d-110)*0.01));s.vx+=dx/d*f;s.vy+=dy/d*f;t.vx-=dx/d*f;t.vy-=dy/d*f}
for(const n of N){if(n===drag)continue;n.vx*=0.86;n.vy*=0.86;n.x+=n.vx;n.y+=n.vy}}
function draw(){cx.setTransform(1,0,0,1,0,0);cx.clearRect(0,0,W,H);cx.setTransform(zoom,0,0,zoom,W/2+panX,H/2+panY);
cx.strokeStyle='#2a2a30';cx.lineWidth=1;for(const e of E){const s=byId[e.source],t=byId[e.target];cx.beginPath();cx.moveTo(s.x,s.y);cx.lineTo(t.x,t.y);cx.stroke();
cx.fillStyle='#555';cx.font='7px sans-serif';cx.fillText(e.type||'',(s.x+t.x)/2,(s.y+t.y)/2)}
for(const n of N){const r=n.type==='concept'?13:9;cx.beginPath();cx.arc(n.x,n.y,r,0,7);cx.fillStyle=COLOR[n.type]||'#888';cx.globalAlpha=sel&&sel!==n?0.45:1;cx.fill();
if(sel===n){cx.strokeStyle='#fff';cx.lineWidth=2;cx.stroke()}cx.globalAlpha=1;
cx.fillStyle='#ddd';cx.font='9px sans-serif';cx.fillText((n.name||'').slice(0,26),n.x+r+3,n.y+3)}}
function loop(){step();draw();requestAnimationFrame(loop)}
function pt(ev){const b=cv.getBoundingClientRect();return{x:((ev.clientX-b.left)*devicePixelRatio-W/2-panX)/zoom,y:((ev.clientY-b.top)*devicePixelRatio-H/2-panY)/zoom}}
function hit(p){return N.find(n=>{const dx=n.x-p.x,dy=n.y-p.y;return dx*dx+dy*dy<200})}
let panning=null;
cv.addEventListener('pointerdown',ev=>{const p=pt(ev),n=hit(p);if(n){drag=n}else{panning={x:ev.clientX-panX/devicePixelRatio,y:ev.clientY-panY/devicePixelRatio}}});
cv.addEventListener('pointermove',ev=>{if(drag){const p=pt(ev);drag.x=p.x;drag.y=p.y;drag.vx=drag.vy=0}else if(panning){panX=(ev.clientX-panning.x)*devicePixelRatio;panY=(ev.clientY-panning.y)*devicePixelRatio}});
cv.addEventListener('pointerup',ev=>{const p=pt(ev),n=hit(p);if(drag===n&&n){sel=n;depth=1;inspect()}drag=null;panning=null});
cv.addEventListener('wheel',ev=>{ev.preventDefault();zoom=Math.min(5,Math.max(0.3,zoom*(ev.deltaY<0?1.1:0.9)))},{passive:false});
function esc(s){const d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML}
function inspect(){const n=sel;if(!n){panel.className='hint';panel.textContent='Click a node.';return}panel.className='';
let h=`<span class="ty t-${esc(n.type)}">${esc(n.type)}</span> <b>${esc(n.name)}</b><div class=sum>${esc(n.summary||'')}</div>`;
if(depth>=2&&n.principle)h+=`<div class=layer><h3>L3 · principle</h3><div class=principle>${esc(n.principle)}</div>${(n.transfer_domains||[]).map(t=>`<div class=hint>transfers → ${esc(t)}</div>`).join('')}</div>`;
if(depth>=3){const nb=E.filter(e=>e.source===n.id||e.target===n.id).map(e=>{const o=byId[e.source===n.id?e.target:e.source];return `<span class=link data-id="${esc(o.id)}">${esc(e.type)} → ${esc(o.name)}</span>`}).join('');
h+=`<div class=layer><h3>L5 · the web around it</h3>${nb||'<div class=hint>no edges</div>'}</div>`;
const evs=N.filter(o=>o.type==='evidence'&&E.some(e=>(e.source===n.id&&e.target===o.id)||(e.target===n.id&&e.source===o.id)));
if(evs.length)h+=`<div class=layer><h3>verbatim evidence</h3>${evs.map(o=>`<div class=ev>“${esc(o.summary)}”</div>`).join('')}</div>`}
if(depth<3)h+=`<button id=deep>go deeper (L${depth===1?3:5})</button>`;
panel.innerHTML=h;const d=document.getElementById('deep');if(d)d.onclick=()=>{depth++;inspect()};
panel.querySelectorAll('.link').forEach(a=>a.onclick=()=>{sel=byId[a.dataset.id];depth=1;inspect()})}
// Programmatic hook so an agent (or test) can open a node's layers without pointer math:
// dmtSelect('infinite games') → selects the first name-matching node at full depth.
window.dmtSelect=q=>{const n=N.find(x=>(x.name||'').toLowerCase().includes(String(q).toLowerCase()));if(n){sel=n;depth=3;inspect()}return n?(n.name):null};
rs();loop();
</script>"""


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
    page = (
        _VIEW_HTML.replace("__TITLE__", title.replace("<", "&lt;")[:120])
        .replace("__META__", meta)
        .replace("__GRAPH__", json.dumps(graph, ensure_ascii=False).replace("</", "<\\/"))
    )
    out_path = out_path or os.path.join(
        os.path.expanduser("~/Desktop") if os.path.isdir(os.path.expanduser("~/Desktop")) else ".",
        f"dmt-map-{room['id'][:8]}.html",
    )
    with open(out_path, "w") as f:
        f.write(page)
    if sys.platform == "darwin":  # best-effort: open it for the user
        subprocess.run(["open", out_path], capture_output=True)
    return {
        "html": out_path,
        "title": title,
        "nodes": len(nodes),
        "edges": len(graph["edges"]),
        "webapp": "http://localhost:3000 (richer, live view — open the room there)",
    }


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
