#\!/usr/bin/env bash
# One-command runner. Usage: bash run.sh path/to/article.md [out_dir]
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
ARTICLE="${1:-examples/day10_article.md}"
OUT="${2:-output_$(date +%Y%m%d_%H%M%S)}"
python3 -m pip install -r requirements.txt --break-system-packages -q 2>/dev/null || true
python3 -m linkedin_publisher.cli build "$ARTICLE" --out "$OUT"
echo "Done -> $HERE/$OUT"
