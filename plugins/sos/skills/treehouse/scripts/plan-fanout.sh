#!/usr/bin/env bash
# plan-fanout.sh — turn a Lavish HTML spec into a dependency-ordered wave plan.
#
# Usage:
#   plan-fanout.sh <spec.html>
#
# Prints, for each requirement: id, parallel-group, depends, files. Then computes
# execution waves (topological by data-depends) and flags same-wave file collisions.
# This is a planning aid for the Code phase — see ../SKILL.md for the model.
set -euo pipefail

[[ $# -eq 1 && -f "$1" ]] || { echo "usage: $0 <spec.html>" >&2; exit 2; }
spec="$1"

# Extract one record per requirement: id|depends|group|files
# We read attributes off each div.req. Specs are emitted by lavish's new-spec.sh,
# so attribute order is stable; we parse defensively with per-attribute greps.
python3 - "$spec" <<'PY'
import re, sys

html = open(sys.argv[1], encoding="utf-8").read()

# Each requirement block starts at <div class="req" ... > and we read its attrs.
blocks = re.findall(r'<div\s+class="req"[^>]*>', html)
if not blocks:
    print("no requirements (div.req) found — is this a lavish spec?", file=sys.stderr)
    sys.exit(1)

def attr(tag, name):
    m = re.search(rf'{name}="([^"]*)"', tag)
    return m.group(1).strip() if m else ""

reqs = {}
for tag in blocks:
    rid = attr(tag, "id")
    if not rid:
        continue
    reqs[rid] = {
        "group": attr(tag, "data-parallel-group") or "?",
        "depends": [d for d in re.split(r"[ ,]+", attr(tag, "data-depends")) if d],
        "files": [f for f in re.split(r"[ ,]+", attr(tag, "data-files")) if f],
    }

print("=== units ===")
print(f"{'id':<10}{'group':<8}{'depends':<16}files")
for rid, r in reqs.items():
    print(f"{rid:<10}{r['group']:<8}{','.join(r['depends']) or '-':<16}{' '.join(r['files']) or '-'}")

# Topological waves: a unit is ready when all its deps are already scheduled.
print("\n=== waves (topological by data-depends) ===")
scheduled, wave_no = set(), 0
remaining = dict(reqs)
while remaining:
    wave_no += 1
    ready = [rid for rid, r in remaining.items()
             if all(d in scheduled for d in r["depends"])]
    if not ready:
        print(f"  ! dependency cycle or unknown dep among: {', '.join(remaining)}",
              file=sys.stderr)
        sys.exit(1)
    print(f"wave {wave_no}: {', '.join(ready)}")

    # Flag same-wave file collisions (two units touching the same path).
    seen = {}
    for rid in ready:
        for f in reqs[rid]["files"]:
            seen.setdefault(f, []).append(rid)
    for f, owners in seen.items():
        if len(owners) > 1:
            print(f"  ✗ collision on {f}: {', '.join(owners)} — re-wave these",
                  file=sys.stderr)

    for rid in ready:
        scheduled.add(rid)
        remaining.pop(rid)

print(f"\n{len(reqs)} units in {wave_no} wave(s). "
      "Fan out each wave concurrently; merge in dependency order after no-mistakes.")
PY
