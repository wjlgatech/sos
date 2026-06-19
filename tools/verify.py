#!/usr/bin/env python
"""
SOS verify — observe, analyze, evaluate in one command.

Usage:
    python tools/verify.py              # quick: syntax + CLI + modules (~3s)
    python tools/verify.py --full       # + service probes + state files (~8s)
    python tools/verify.py -v           # verbose (show pass detail too)

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `tools.*` imports work
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.evaluator import run_all
from tools.reporter import print_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SOS verify — check syntax, CLI contracts, module imports, service ports, and state files."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full check: adds service port probes + state file integrity (~8s)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose: show detail lines for passing checks too",
    )
    parser.add_argument(
        "--repo-root",
        default=str(_REPO_ROOT),
        help=f"Path to SOS repo root (default: {_REPO_ROOT})",
    )
    parser.add_argument(
        "--specs-dir",
        default=str(_REPO_ROOT / "specs"),
        help="Path to specs/ directory",
    )
    args = parser.parse_args()

    print(f"\nSOS verify ({'full' if args.full else 'quick'} mode)")
    print("=" * 58)

    result = run_all(
        quick=not args.full,
        repo_root=args.repo_root,
        specs_dir=args.specs_dir,
    )

    print_report(result, verbose=args.verbose)

    sys.exit(0 if result.passed() else 1)


if __name__ == "__main__":
    main()
