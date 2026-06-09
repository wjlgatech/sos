#!/usr/bin/env bash
# install-skills-global.sh — make the sos plugin's skills discoverable GLOBALLY to multiple
# agents on THIS machine, by symlinking them out of a clone of this repo. Run once per machine
# (clone the repo anywhere, then run this) so the same skills follow you across computers.
#
#   git clone https://github.com/wjlgatech/sos.git && cd sos
#   bash plugins/sos/scripts/install-skills-global.sh
#
# For Claude Code the supported path is usually the marketplace instead:
#   /plugin marketplace add wjlgatech/sos && /plugin install sos@wjlgatech-plugins
# This script is the portable fallback + the way to reach OTHER agents (Hermes, etc.) whose
# global skills live in their own directory.
#
# Targets (override any via env):
#   CLAUDE_SKILLS_DIR   default: ~/.claude/skills
#   HERMES_SKILLS_DIR   default: ${HERMES_HOME:-~/.hermes}/skills
#   SKILLS              space-separated skill names to install (default: all in this plugin)
#
# Idempotent: re-running refreshes the symlinks.
set -euo pipefail

# Locate this plugin's skills dir relative to the script (works from any clone location).
script_dir=$(cd "$(dirname "$0")" && pwd)
src_skills=$(cd "$script_dir/../skills" && pwd)

claude_dir="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
hermes_dir="${HERMES_SKILLS_DIR:-${HERMES_HOME:-$HOME/.hermes}/skills}"

# Default to every skill that has a SKILL.md.
if [ -z "${SKILLS:-}" ]; then
  SKILLS=$(cd "$src_skills" && for d in */; do [ -f "${d}SKILL.md" ] && printf '%s ' "${d%/}"; done)
fi

link_into() {
  agent="$1"; dest="$2"
  mkdir -p "$dest"
  for name in $SKILLS; do
    src="$src_skills/$name"
    [ -d "$src" ] || { echo "  skip $name (not found)"; continue; }
    target="$dest/$name"
    # Refresh an existing symlink; never clobber a real directory the user owns.
    if [ -L "$target" ] || [ ! -e "$target" ]; then
      ln -sfn "$src" "$target"
      echo "  ✓ $name -> $target"
    else
      echo "  ! $name exists as a non-symlink at $target — left untouched"
    fi
  done
  echo "$agent: linked into $dest"
}

# Codex has no skills dir — it discovers tools via the global ~/.codex/AGENTS.md. Point it
# at the symlinked skills directory (idempotent: skip if our marker section already exists).
wire_codex() {
  codex_md="${CODEX_AGENTS_MD:-$HOME/.codex/AGENTS.md}"
  [ -d "$(dirname "$codex_md")" ] || { echo "Codex: ~/.codex not found — skipped"; return 0; }
  if [ -f "$codex_md" ] && grep -q "sos skills directory" "$codex_md"; then
    echo "Codex: $codex_md already wired"
    return 0
  fi
  cat >> "$codex_md" <<EOF

## sos skills directory (global agent tools)

Reusable skills live at \`$claude_dir/\` (symlinks into a clone of
https://github.com/wjlgatech/sos — \`git pull\` there updates them). Each skill is a
directory with a \`SKILL.md\` (when to use + procedure) and optional \`scripts/\` (zero-dep,
runnable directly). When a task matches a skill's description, read its SKILL.md and
follow it.
EOF
  echo "Codex: wired via $codex_md"
}

echo "source skills: $src_skills"
echo "installing: $SKILLS"
echo
link_into "Claude Code" "$claude_dir"
echo
link_into "Hermes" "$hermes_dir"
echo
wire_codex
echo
echo "Done. If your Hermes skills live elsewhere, re-run with:"
echo "  HERMES_SKILLS_DIR=/path/to/hermes/skills bash $0"
echo "Skills are symlinks into this clone — 'git pull' here updates them everywhere."
