#!/usr/bin/env sh
# install-claude-instructions.sh — load Paul's personal operating instructions into
# EVERY Claude Code session on THIS machine (all projects). Idempotent — safe to re-run.
#
#   curl -fsSL https://raw.githubusercontent.com/wjlgatech/sos/main/plugins/sos/scripts/install-claude-instructions.sh | sh
#   # …or, from a clone:
#   sh plugins/sos/scripts/install-claude-instructions.sh
#
# How it works (two moving parts, both in ~/.claude):
#   1. Places the canonical instructions file — plugins/sos/instructions/
#      claude-instructions.md, copied from the local clone if you run it there,
#      otherwise fetched from GitHub raw @ main — at ~/.claude/instructions-paul-wu.md.
#   2. Ensures ~/.claude/CLAUDE.md contains the import line
#      `@~/.claude/instructions-paul-wu.md`. Claude Code reads ~/.claude/CLAUDE.md
#      at the start of every session in every project, and an `@path` line is a
#      file import — so the instructions load everywhere on this machine.
#
# The repo copy is the single source of truth; ~/.claude/instructions-paul-wu.md is
# a generated copy. Edit the repo file, push, then re-run this script per machine
# (and on every new computer) to update. Nothing here is machine-specific.

set -e

RAW="https://raw.githubusercontent.com/wjlgatech/sos/main/plugins/sos/instructions/claude-instructions.md"
CLAUDE_DIR="${HOME}/.claude"
TARGET="${CLAUDE_DIR}/instructions-paul-wu.md"
GLOBAL_MD="${CLAUDE_DIR}/CLAUDE.md"
IMPORT_LINE="@~/.claude/instructions-paul-wu.md"

mkdir -p "${CLAUDE_DIR}"

# 1/2 — place the instructions file (local clone wins; else GitHub raw @ main)
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || SCRIPT_DIR=""
LOCAL_SRC="${SCRIPT_DIR%/scripts}/instructions/claude-instructions.md"
if [ -n "${SCRIPT_DIR}" ] && [ -f "${LOCAL_SRC}" ]; then
  cp "${LOCAL_SRC}" "${TARGET}"
  echo "→ 1/2  Copied local clone → ${TARGET}"
else
  curl -fsSL "${RAW}" -o "${TARGET}"
  echo "→ 1/2  Fetched GitHub raw → ${TARGET}"
fi

# 2/2 — ensure the global CLAUDE.md imports it (append once, never duplicate)
if [ -f "${GLOBAL_MD}" ] && grep -qF "${IMPORT_LINE}" "${GLOBAL_MD}"; then
  echo "→ 2/2  Import already present in ${GLOBAL_MD}"
else
  printf '\n## Personal operating instructions (Paul Wu — synced from wjlgatech/sos)\n\n%s\n' "${IMPORT_LINE}" >>"${GLOBAL_MD}"
  echo "→ 2/2  Added import to ${GLOBAL_MD}"
fi

echo ""
echo "✓ Done. Every Claude Code session on this machine now loads the instructions"
echo "  (restart any open session to pick them up)."
echo "  Canonical source: github.com/wjlgatech/sos → plugins/sos/instructions/"
echo "  Update: edit + push the repo file, then re-run this script on each machine."
