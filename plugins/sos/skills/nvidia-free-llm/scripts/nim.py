#!/usr/bin/env python3
"""nim.py — zero-dependency probe for NVIDIA's free NIM API (integrate.api.nvidia.com).

Stdlib only. Reads NVIDIA_API_KEY from env (or --key).

Commands:
  list [filter]          list the live model catalog (no key needed), optionally filtered
  test <model> [--key K] one tiny chat completion → ok/latency/first tokens
  pick                   print the recommended model per role (chat/code/cheap/reasoning)

Examples:
  python3 nim.py list kimi
  NVIDIA_API_KEY=nvapi-... python3 nim.py test z-ai/glm-5.1
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

BASE = "https://integrate.api.nvidia.com/v1"

# Verified against the live catalog 2026-06-10 (`nim.py list`). The viral post's ids for
# GLM/Kimi were WRONG (zhipuai/* and moonshot-ai/* don't exist in this catalog).
RECOMMENDED = {
    "chat (flagship)": "z-ai/glm-5.1",
    "chat (fast)": "deepseek-ai/deepseek-v4-flash",
    "agentic": "moonshotai/kimi-k2.6",
    "code": "qwen/qwen3-coder-480b-a35b-instruct",
    "reasoning (huge)": "nvidia/nemotron-3-ultra-550b-a55b",
    "open-weights": "openai/gpt-oss-120b",
    "long-context": "minimaxai/minimax-m2.7",
}


def _get(path: str, key: str | None = None, body: dict | None = None, timeout: int = 60):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        BASE + path, data=data, headers=headers, method="POST" if body else "GET"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def cmd_list(args: list[str]) -> None:
    models = [m["id"] for m in _get("/models")["data"]]
    flt = args[0].lower() if args else ""
    hits = [m for m in models if flt in m.lower()]
    print(f"{len(hits)}/{len(models)} models" + (f" matching '{flt}'" if flt else ""))
    for m in sorted(hits):
        print(" ", m)


def cmd_test(args: list[str]) -> None:
    key = os.environ.get("NVIDIA_API_KEY", "")
    if "--key" in args:
        i = args.index("--key")
        key = args[i + 1]
        args = args[:i] + args[i + 2 :]
    if not key:
        sys.exit("need NVIDIA_API_KEY env or --key nvapi-… (free: build.nvidia.com/models)")
    model = args[0] if args else RECOMMENDED["chat (fast)"]
    t0 = time.time()
    out = _get(
        "/chat/completions",
        key,
        {
            "model": model,
            "max_tokens": 40,
            "messages": [{"role": "user", "content": "Say 'ready' and today's weekday."}],
        },
    )
    ms = int((time.time() - t0) * 1000)
    txt = out["choices"][0]["message"]["content"]
    print(json.dumps({"ok": True, "model": model, "latency_ms": ms, "reply": txt[:120]}))


def cmd_pick(_: list[str]) -> None:
    for role, model in RECOMMENDED.items():
        print(f"{role:18} {model}")


def main() -> None:
    cmds = {"list": cmd_list, "test": cmd_test, "pick": cmd_pick}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(0)
    cmds[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
