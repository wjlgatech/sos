#!/usr/bin/env sh
# install-doc-sync.sh — install the "log + sync docs on every feature change" guard
# into the current git repo. Stack-aware (husky / plain git hook / pre-commit-framework)
# and idempotent. See ~/.claude/CLAUDE.md → "Log + sync docs on every feature change".
#
#   cd <repo> && ~/.claude/scripts/install-doc-sync.sh
#
# Installs:
#   - CHANGELOG.md            (Keep a Changelog skeleton, if absent)
#   - scripts/changelog.sh    (helper to add [Unreleased] entries)
#   - a pre-commit guard      (blocks feature commit w/o changelog; nudges for docs)

set -e
root=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "not a git repo" >&2; exit 1; }
cd "$root"
MARK="# >>> doc-sync guard >>>"  # idempotency marker

# ── 1. CHANGELOG.md ─────────────────────────────────────────────────────────
if [ ! -f CHANGELOG.md ]; then
  cat > CHANGELOG.md <<'EOF'
# Changelog

All notable changes are logged here — for humans **and** agents.
Format follows [Keep a Changelog](https://keepachangelog.com/). Newest first.

## [Unreleased]

### Added

### Changed

### Fixed
EOF
  echo "+ CHANGELOG.md"
else
  echo "= CHANGELOG.md (kept)"
fi

# ── 2. scripts/changelog.sh ─────────────────────────────────────────────────
mkdir -p scripts
cat > scripts/changelog.sh <<'EOF'
#!/usr/bin/env sh
# changelog.sh — add a line to CHANGELOG.md under ## [Unreleased].
#   scripts/changelog.sh "<line>"
#   scripts/changelog.sh --changed "<line>"   # --added(default)|--changed|--fixed|--removed|--rejected
set -e
section="Added"
case "$1" in
  --added) section="Added"; shift ;; --changed) section="Changed"; shift ;;
  --fixed) section="Fixed"; shift ;; --removed) section="Removed"; shift ;;
  --rejected) section="Investigated / Rejected"; shift ;;
esac
line="$*"
[ -n "$line" ] || { echo "usage: scripts/changelog.sh [--added|--changed|--fixed|--removed|--rejected] \"<line>\"" >&2; exit 2; }
root=$(git rev-parse --show-toplevel); cl="$root/CHANGELOG.md"
[ -f "$cl" ] || { echo "no CHANGELOG.md at repo root" >&2; exit 1; }
grep -Fq -- "- $line" "$cl" && { echo "changelog: already present, skipping"; exit 0; }
awk -v sec="### $section" -v entry="- $line" '
  BEGIN{u=0;d=0}
  /^## \[Unreleased\]/{print;u=1;next}
  u&&!d&&$0==sec{print;print entry;d=1;next}
  u&&!d&&/^## /{print sec;print entry;print "";print;u=0;d=1;next}
  {print}
  END{if(u&&!d){print sec;print entry}}' "$cl" > "$cl.tmp" && mv "$cl.tmp" "$cl"
git add "$cl"; echo "changelog: + [$section] $line"
EOF
chmod +x scripts/changelog.sh
echo "+ scripts/changelog.sh"

# The guard body, shared by every install target.
guard_body() {
cat <<'EOF'
# >>> doc-sync guard >>>
# Feature code (src/lib/app/packages, tests excluded) must carry a CHANGELOG.md
# [Unreleased] entry, and is nudged to update README / agent guide / docs.
# Bypass once: SKIP_DOC_SYNC=1 git commit ...
staged=$(git diff --cached --name-only --diff-filter=ACM)
code=$(printf '%s\n' "$staged" | grep -E '^(apps/[^/]+/src/|packages/[^/]+/|src/|lib/|app/)' | grep -vE '\.(test|spec)\.|/__tests__/|/tests?/' || true)
if [ -n "$code" ] && [ "$SKIP_DOC_SYNC" != "1" ]; then
  log_ok=$(printf '%s\n'  "$staged" | grep -E '^CHANGELOG\.md$' || true)
  docs_ok=$(printf '%s\n' "$staged" | grep -E '^(README\.md|CLAUDE\.md|AGENTS\.md|docs/)' || true)
  if [ -z "$log_ok" ]; then
    echo "✋ Feature code changed but CHANGELOG.md has no new entry."
    echo "   Add one:  scripts/changelog.sh \"<what changed>\"   (bypass: SKIP_DOC_SYNC=1)"
    exit 1
  fi
  [ -z "$docs_ok" ] && echo "⚠ Feature code changed but no doc touched (README / CLAUDE.md / AGENTS.md / docs)."
fi
# <<< doc-sync guard <<<
EOF
}

# ── 3. Install the guard into the right hook mechanism ──────────────────────
already() { [ -f "$1" ] && grep -Fq "$MARK" "$1"; }

if [ -f .husky/pre-commit ]; then
  if already .husky/pre-commit; then echo "= husky guard (present)"; else
    printf '\n%s\n' "$(guard_body)" >> .husky/pre-commit; echo "+ husky pre-commit guard"; fi
elif [ -d .husky ]; then
  { echo '#!/usr/bin/env sh'; echo; guard_body; } > .husky/pre-commit
  chmod +x .husky/pre-commit; echo "+ .husky/pre-commit (new)"
elif [ -f .pre-commit-config.yaml ]; then
  echo "! pre-commit-framework repo — it owns .git/hooks/pre-commit."
  echo "  Add this local hook to .pre-commit-config.yaml, then \`pre-commit install\`:"
  cat <<'YAML'

  - repo: local
    hooks:
      - id: doc-sync
        name: docs-sync guard (changelog + docs)
        entry: scripts/doc-sync-check.sh
        language: script
        pass_filenames: false
        always_run: true
YAML
  # ship the standalone checker the YAML references
  { echo '#!/usr/bin/env sh'; echo 'set -e'; guard_body; } > scripts/doc-sync-check.sh
  chmod +x scripts/doc-sync-check.sh; echo "+ scripts/doc-sync-check.sh (referenced by the snippet)"
else
  hook=.git/hooks/pre-commit
  if already "$hook"; then echo "= git hook guard (present)"; else
    if [ -f "$hook" ]; then printf '\n%s\n' "$(guard_body)" >> "$hook"
    else { echo '#!/usr/bin/env sh'; echo; guard_body; } > "$hook"; fi
    chmod +x "$hook"; echo "+ .git/hooks/pre-commit guard"; fi
fi

echo "doc-sync: installed in $(basename "$root")."
