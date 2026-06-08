#!/usr/bin/env bash
# freellmapi.sh — stand up / probe a local FreeLLMAPI proxy.
#
# Usage:
#   freellmapi.sh up                 Clone (if needed) + docker compose up -d, wait for health.
#   freellmapi.sh status             Check the endpoint is live and list models.
#   freellmapi.sh test [KEY]         Send a sample chat completion (KEY or $FREELLMAPI_KEY).
#
# Env:
#   FREELLMAPI_URL   base url (default http://localhost:3001)
#   FREELLMAPI_KEY   unified bearer key (freellmapi-...), for `test`
#   FREELLMAPI_DIR   where to clone (default ./freellmapi)
#
# See ../SKILL.md. Scope: personal experimentation only — not production.
set -euo pipefail

URL="${FREELLMAPI_URL:-http://localhost:3001}"
DIR="${FREELLMAPI_DIR:-freellmapi}"

usage() { sed -n '2,15p' "$0" >&2; exit 2; }

up() {
  command -v docker >/dev/null 2>&1 || { echo "docker is required" >&2; exit 1; }
  if [ ! -d "$DIR/.git" ]; then
    git clone https://github.com/tashfeenahmed/freellmapi.git "$DIR"
  fi
  cd "$DIR"
  if [ ! -f .env ]; then
    command -v openssl >/dev/null 2>&1 || { echo "openssl required to mint ENCRYPTION_KEY" >&2; exit 1; }
    printf 'ENCRYPTION_KEY=%s\nPORT=3001\n' "$(openssl rand -hex 32)" > .env
    echo "wrote .env with a fresh ENCRYPTION_KEY"
  fi
  docker compose up -d
  echo "waiting for $URL ..."
  for _ in $(seq 1 30); do
    if curl -fsS "$URL" >/dev/null 2>&1; then
      echo "✓ dashboard up at $URL — add provider keys there, then copy your freellmapi-... key"
      return 0
    fi
    sleep 2
  done
  echo "⚠ proxy did not become healthy in time; check: docker compose logs" >&2
  exit 1
}

status() {
  echo "probing $URL ..."
  if curl -fsS "$URL/v1/models" 2>/dev/null; then
    echo; echo "✓ endpoint live"
  elif curl -fsS "$URL" >/dev/null 2>&1; then
    echo "✓ dashboard reachable at $URL (models list needs a key or providers configured)"
  else
    echo "✗ nothing answering at $URL — run: $0 up" >&2
    exit 1
  fi
}

test_chat() {
  local key="${1:-${FREELLMAPI_KEY:-}}"
  [ -n "$key" ] || { echo "need a unified key: $0 test freellmapi-... (or set FREELLMAPI_KEY)" >&2; exit 2; }
  curl -fsS "$URL/v1/chat/completions" \
    -H "Authorization: Bearer $key" \
    -H "Content-Type: application/json" \
    -d '{"model":"auto","messages":[{"role":"user","content":"Reply with exactly: ok"}]}'
  echo
}

[ $# -ge 1 ] || usage
case "$1" in
  up) up ;;
  status) status ;;
  test) shift; test_chat "${1:-}" ;;
  -h|--help) usage ;;
  *) usage ;;
esac
