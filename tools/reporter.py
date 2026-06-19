"""
SOS verify reporter — colour-coded terminal output.

Format:
  ✅  syntax: orchestrator.py              (1.2ms)
  ❌  cli: status  — missing keys: ['agent_id']
  ⚠️   service: localhost:3000  — DOWN (expected when not running)
  ────────────────────────────────────────────
  Gap score: 11/12 (0.917)   ✅ All checks passed
"""

from __future__ import annotations

from tools.evaluator import EvalResult
from tools.observer import CheckResult

# ANSI colours
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _ok(s: str) -> str:
    return f"{_GREEN}{s}{_RESET}"


def _fail(s: str) -> str:
    return f"{_RED}{s}{_RESET}"


def _warn(s: str) -> str:
    return f"{_YELLOW}{s}{_RESET}"


def _bold(s: str) -> str:
    return f"{_BOLD}{s}{_RESET}"


def _render_check(c: CheckResult, verbose: bool = False) -> str:
    elapsed = f"({c.elapsed_ms:.0f}ms)" if c.elapsed_ms else ""
    if c.passed:
        line = f"  {_ok('✅')}  {c.label:<55} {elapsed}"
        if verbose and c.detail:
            line += f"\n       {_warn(c.detail)}"
    else:
        line = f"  {_fail('❌')}  {c.label}"
        if c.detail:
            line += f"\n       {_fail(c.detail)}"
    return line


def _render_service_check(c: CheckResult) -> str:
    elapsed = f"({c.elapsed_ms:.0f}ms)" if c.elapsed_ms else ""
    if "UP" in c.label:
        return f"  {_ok('✅')}  {c.label:<55} {elapsed}"
    else:
        return f"  {_warn('⚠️')}   {c.label:<55} {elapsed}"


def print_report(result: EvalResult, verbose: bool = False) -> None:
    sections = [
        ("Syntax", result.syntax, False),
        ("CLI Commands", result.cli, False),
        ("Module Imports", result.modules, False),
        ("Service Ports (soft)", result.services, True),
        ("State Files", result.state, False),
    ]

    for title, checks, is_soft in sections:
        if not checks:
            continue
        print(f"\n{_bold(title)}")
        for c in checks:
            if is_soft:
                print(_render_service_check(c))
            else:
                print(_render_check(c, verbose=verbose))

    # Summary
    all_checks = result.all_checks()
    passed = sum(1 for c in all_checks if c.passed)
    total = len(all_checks)
    score = result.gap_score()

    print("\n  " + "─" * 44)
    if result.passed():
        print(f"  Gap score: {passed}/{total} ({score:.3f})   {_ok('✅ All checks passed')}")
    else:
        failures = result.failures()
        print(f"  Gap score: {passed}/{total} ({score:.3f})   {_fail(f'❌ {len(failures)} check(s) failed')}")
        for c in failures:
            print(f"  {_fail('✖')} {c.label}")
            if c.detail:
                for line in c.detail.splitlines()[:3]:
                    print(f"       {line}")
