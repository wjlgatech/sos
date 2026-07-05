#!/usr/bin/env bash
# Smoke test for syndicate.mjs — asserts arg-handling, the drafts-never-sends framing,
# and that a real run emits every intent + channel + the canonical url. Deterministic;
# no network. Uses a tiny inline fixture so it runs anywhere.
set -u
cd "$(dirname "$0")"
S=syndicate.mjs
fail() { echo "❌ $1"; exit 1; }

# 1. --help exits 0
node "$S" --help >/dev/null 2>&1 || fail "--help should exit 0"

# 2. missing --url → usage, exit 1
node "$S" --from /dev/null >/dev/null 2>&1 && fail "missing --url should exit 1"

# 3. a real run on a fixture emits intents + channels + banner
FIX=$(mktemp); trap 'rm -f "$FIX"' EXIT
printf '# Test Title\n\n*A test subtitle line.*\n\nThis is the opening hook paragraph with enough length to be picked up as the teaser text.\n\n## First Section\n\n- **A genuine claim that is long enough to survive the filter and read as a point.**\n\n#Tag1 #Tag2\n' > "$FIX"
OUT=$(node "$S" --from "$FIX" --url "https://example.com/a.html" --handle demo 2>/dev/null) \
  || fail "a normal run should exit 0"

echo "$OUT" | grep -q "DRAFTS ONLY" || fail "kit must be framed DRAFTS ONLY"
echo "$OUT" | grep -qi "never posts" || fail "hard-rule (never posts) must be present"
echo "$OUT" | grep -q "twitter.com/intent/tweet" || fail "X intent missing"
echo "$OUT" | grep -q "linkedin.com/sharing/share-offsite" || fail "LinkedIn intent missing"
echo "$OUT" | grep -q "bsky.app/intent" || fail "Bluesky intent missing"
echo "$OUT" | grep -q "Import a story" || fail "Medium owned-home recipe missing"
echo "$OUT" | grep -q "https://example.com/a.html" || fail "canonical url must appear"
for h in "## LinkedIn" "## X / Twitter" "## Instagram" "## YouTube"; do
  echo "$OUT" | grep -qF "$h" || fail "channel section missing: $h"
done

echo "✅ syndicate.mjs smoke passed"
