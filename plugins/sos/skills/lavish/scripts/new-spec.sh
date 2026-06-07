#!/usr/bin/env bash
# new-spec.sh — emit or validate a Lavish HTML spec.
#
# Usage:
#   new-spec.sh <slug>              Create specs/<slug>.html from the typed template.
#   new-spec.sh --check <file>      Validate a spec is well-formed and complete.
#
# The HTML spec is the Plan-phase contract consumed by treehouse (Code) and
# no-mistakes (Validate). See ../SKILL.md for the schema and rationale.
set -euo pipefail

usage() { sed -n '2,9p' "$0" >&2; exit 2; }

emit() {
  local slug="$1"
  local dir="specs"
  local out="${dir}/${slug}.html"
  mkdir -p "$dir"
  if [[ -e "$out" ]]; then
    echo "refusing to overwrite existing $out" >&2
    exit 1
  fi
  cat > "$out" <<HTML
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>SPEC: ${slug}</title></head>
<body>
<article class="spec" data-slug="${slug}" data-status="draft">

  <section data-spec="objective">
    <h1>TODO: one sentence — what &amp; why</h1>
    <p data-done-when>TODO: the observable condition that means "done"</p>
  </section>

  <section data-spec="context">
    <ul>
      <li data-fact>TODO: a constraint / existing module / decision agents must respect</li>
    </ul>
  </section>

  <section data-spec="requirements">
    <div class="req" id="REQ-1"
         data-status="todo"
         data-parallel-group="A"
         data-depends=""
         data-files="src/TODO.py"
         data-tests="tests/test_TODO.py">
      <h2>TODO: what this unit must do (one reviewable PR)</h2>
      <ul class="acceptance">
        <li data-ac data-check="pytest tests/test_TODO.py::test_x">TODO: checkable criterion</li>
      </ul>
    </div>
  </section>

  <section data-spec="interfaces">
    <pre data-contract>TODO: signatures / schemas / API shapes agents must conform to</pre>
  </section>

  <section data-spec="out-of-scope">
    <ul><li data-no>TODO: explicitly NOT part of this work</li></ul>
  </section>

</article>
</body>
</html>
HTML
  echo "created $out"
  echo "next: fill the TODOs, then run: $0 --check $out"
}

check() {
  local file="$1"
  [[ -f "$file" ]] || { echo "no such file: $file" >&2; exit 1; }
  local errors=0
  err() { echo "  ✗ $1" >&2; errors=$((errors + 1)); }

  # Required structural regions.
  for region in objective requirements out-of-scope; do
    grep -q "data-spec=\"${region}\"" "$file" || err "missing <section data-spec=\"${region}\">"
  done
  grep -q "data-done-when" "$file" || err "missing a data-done-when condition"

  # Every requirement needs an id, files, tests, and at least one acceptance criterion.
  grep -q 'class="req"' "$file" || err "no requirements (div.req) found"
  grep -q "data-ac" "$file" || err "no acceptance criteria (data-ac) found"
  grep -q "data-check" "$file" || err "acceptance criteria have no data-check (not machine-checkable)"

  # No unfilled placeholders left behind.
  if grep -q "TODO" "$file"; then
    err "$(grep -c TODO "$file") unfilled TODO placeholder(s) remain"
  fi

  if [[ $errors -eq 0 ]]; then
    echo "✓ $file is a well-formed, complete Lavish spec — ready for treehouse"
  else
    echo "spec incomplete: $errors problem(s)" >&2
    exit 1
  fi
}

main() {
  [[ $# -ge 1 ]] || usage
  case "$1" in
    --check) [[ $# -eq 2 ]] || usage; check "$2" ;;
    -h|--help) usage ;;
    -*) usage ;;
    *) [[ $# -eq 1 ]] || usage; emit "$1" ;;
  esac
}

main "$@"
