#!/usr/bin/env sh
# install-goal-10x.sh — make /goal-10x (and the rest of the sos plugin) available
# on ANY machine, across ALL Claude Code projects. Idempotent — safe to re-run.
#
#   curl -fsSL https://raw.githubusercontent.com/wjlgatech/sos/main/plugins/sos/scripts/install-goal-10x.sh | sh
#   # …or, from a clone:
#   sh plugins/sos/scripts/install-goal-10x.sh
#
# What it does (all via the official `claude` CLI + a user-level command file):
#   1. Registers the wjlgatech/sos GitHub repo as a plugin marketplace.
#   2. Installs the `sos` plugin at user scope  → gives you /sos:goal-10x,
#      /sos:ship-loop, /sos:lavish, /sos:treehouse, /sos:no-mistakes, + skills.
#   3. Symlinks ~/.claude/commands/goal-10x.md → the installed plugin's command,
#      so the BARE name /goal-10x works too. The symlink tracks the marketplace
#      clone, so `claude plugin marketplace update wjlgatech-plugins` refreshes
#      both names with no drift.
#
# Re-run on every new computer. Requires the `claude` CLI on PATH and network
# access to github.com. Nothing here is machine-specific.

set -e

REPO="wjlgatech/sos"
MARKET="wjlgatech-plugins"          # marketplace `name` from .claude-plugin/marketplace.json
PLUGIN="sos@${MARKET}"
CLAUDE_DIR="${HOME}/.claude"
CMD_LINK="${CLAUDE_DIR}/commands/goal-10x.md"
SRC="${CLAUDE_DIR}/plugins/marketplaces/${MARKET}/plugins/sos/commands/goal-10x.md"

command -v claude >/dev/null 2>&1 || {
  echo "✗ The 'claude' CLI is not on PATH. Install Claude Code first: https://claude.com/claude-code" >&2
  exit 1
}

echo "→ 1/3  Registering marketplace ${REPO}…"
# `add` errors if already present; treat that as success (idempotent).
claude plugin marketplace add "${REPO}" 2>&1 | grep -vi "already" || true
claude plugin marketplace update "${MARKET}" >/dev/null 2>&1 || true

echo "→ 2/3  Installing plugin ${PLUGIN} (user scope)…"
claude plugin install "${PLUGIN}" --scope user 2>&1 | grep -vi "already installed" || true

echo "→ 3/3  Linking bare /goal-10x → live plugin command…"
if [ ! -f "${SRC}" ]; then
  echo "✗ Expected command file not found at:" >&2
  echo "    ${SRC}" >&2
  echo "  The plugin install may have failed — re-run, or use /sos:goal-10x instead." >&2
  exit 1
fi
mkdir -p "${CLAUDE_DIR}/commands"
# Back up a pre-existing real file once (not our own symlink) so we never clobber blindly.
if [ -e "${CMD_LINK}" ] && [ ! -L "${CMD_LINK}" ]; then
  mv "${CMD_LINK}" "${CMD_LINK}.stale-backup"
  echo "  (backed up existing ${CMD_LINK} → ${CMD_LINK}.stale-backup)"
fi
ln -sf "${SRC}" "${CMD_LINK}"

echo ""
echo "✓ Done. Restart Claude Code, then use either:"
echo "    /goal-10x      (bare name, via ~/.claude/commands symlink)"
echo "    /sos:goal-10x  (namespaced, via the installed plugin)"
echo ""
echo "  Update later with:  claude plugin marketplace update ${MARKET}"
