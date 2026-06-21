#!/usr/bin/env bash
# knowledgefy_smoke.sh — end-to-end proof that /knowledgefy works: resolve dmt.py, run the
# kgfy one-shot on a tiny text fixture, and assert it produced an HTML artifact (and report the
# served URL). The engine self-heals if down (kgfy calls ensure_api). Exits non-zero on failure.
#
# Usage: plugins/sos/skills/knowledgefy/scripts/knowledgefy_smoke.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve dmt.py from the sibling dreammaketrue skill (same order the SKILL.md documents).
DMT="${DMT:-}"
for c in \
  "$DMT" \
  "$HOME/.claude/skills/dreammaketrue/scripts/dmt.py" \
  "$HOME/.hermes/skills/dreammaketrue/scripts/dmt.py" \
  "$HERE/../../dreammaketrue/scripts/dmt.py" \
  "$HOME/Documents/Projects/sos/plugins/sos/skills/dreammaketrue/scripts/dmt.py" ; do
  if [ -n "$c" ] && [ -f "$c" ]; then DMT="$c"; break; fi
done
if [ ! -f "$DMT" ]; then
  echo "FAIL: dmt.py not found. Install the dreammaketrue skill or set DMT=/path/to/dmt.py" >&2
  exit 1
fi
echo "resolved dmt.py → $DMT"

# Tiny fixture with a few concepts so topic-map extraction yields nodes.
FIX="$(mktemp -t knowledgefy_fix.XXXXXX).md"
OUT="$(mktemp -t knowledgefy_map.XXXXXX).html"
trap 'rm -f "$FIX"' EXIT
cat > "$FIX" <<'TXT'
# Compounding

Compounding is growth that feeds on itself: each period's gain becomes next period's base.
A core principle is that small, consistent inputs dominate over long horizons because the
effect is exponential, not linear. The same idea transfers from finance to learning and to
codebases — a habit, a test suite, or a knowledge base each compounds when revisited often.
The limiting factor is interruption: a reset to zero destroys the accumulated base.
TXT

echo "running: python3 dmt.py kgfy $FIX --title 'Compounding (smoke)' --out $OUT"
RESULT="$(python3 "$DMT" kgfy "$FIX" --title "Compounding (smoke)" --out "$OUT")"

# Assert: the HTML artifact exists and is non-trivial; report served_url.
python3 - "$OUT" <<'PY'
import os, sys
out = sys.argv[1]
if not (os.path.isfile(out) and os.path.getsize(out) > 1000):
    sys.exit(f"FAIL: expected a non-trivial HTML artifact at {out}")
print(f"PASS: artifact written ({os.path.getsize(out)} bytes) → {out}")
PY

# served_url is best-effort (null if the engine couldn't publish) — report, don't require.
SERVED="$(printf '%s' "$RESULT" | python3 -c 'import json,sys; print((json.load(sys.stdin) or {}).get("served_url") or "(none — engine could not publish; local file still works)")' 2>/dev/null || echo "(unparseable result)")"
echo "served_url: $SERVED"
echo "RESULT: PASS"
