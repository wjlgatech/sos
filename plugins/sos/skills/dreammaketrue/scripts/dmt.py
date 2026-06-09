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
