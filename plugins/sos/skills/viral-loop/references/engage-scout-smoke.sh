#!/usr/bin/env bash
# Smoke test for engage-scout.mjs — asserts arg-handling, the drafts-never-sends framing,
# and that a real run emits a well-formed queue. Network-tolerant: if the search host is
# unreachable, getJson degrades to [] and the run still emits the header + exits 0.
set -u
cd "$(dirname "$0")"
S=engage-scout.mjs
fail() { echo "❌ $1"; exit 1; }

# 1. --help exits 0
node "$S" --help >/dev/null 2>&1 || fail "--help should exit 0"

# 2. no args → usage, exit 1
node "$S" >/dev/null 2>&1 && fail "no-args should exit 1 (usage)"

# 3. a real run emits the queue header + the hard-rule line, exits 0
OUT=$(node "$S" --keywords "kv cache, prefill decode disaggregation" --min-score 0.9 --limit 2 2>/dev/null) \
  || fail "a normal run should exit 0"
echo "$OUT" | grep -q "DRAFTS ONLY" || fail "queue must be framed DRAFTS ONLY"
echo "$OUT" | grep -qi "Never auto-post" || fail "hard-rule (never auto-post) must be present"

# 4. --json emits a valid report carrying the hard rule + login-walled honesty
node "$S" --keywords "llm inference" --min-score 0.9 --limit 2 --json 2>/tmp/es-smoke.json >/dev/null || fail "--json run failed"
tail -n +2 /tmp/es-smoke.json | node -e 'let d="";process.stdin.on("data",c=>d+=c).on("end",()=>{const j=JSON.parse(d);if(!j.hardRule)process.exit(1);if(!j.feasibility||!j.feasibility.loginWalled)process.exit(1)})' \
  || fail "--json report must carry hardRule + feasibility.loginWalled"

echo "✅ engage-scout smoke: all pass"
