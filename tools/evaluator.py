"""
SOS evaluator — load specs, run all observations, return a structured EvalResult.

Quick mode (~3s):  syntax + CLI + module imports
Full mode  (~8s):  + service port probes + state file checks
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.observer import (
    CheckResult,
    check_cli_commands,
    check_module_imports,
    check_service_ports,
    check_state_files,
    check_syntax,
)

# ── Spec loader ───────────────────────────────────────────────────────────────


def _load_spec(specs_dir: str, filename: str) -> dict[str, Any]:
    path = Path(specs_dir) / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text())


# ── Result container ──────────────────────────────────────────────────────────


@dataclass
class EvalResult:
    syntax: list[CheckResult] = field(default_factory=list)
    cli: list[CheckResult] = field(default_factory=list)
    modules: list[CheckResult] = field(default_factory=list)
    services: list[CheckResult] = field(default_factory=list)
    state: list[CheckResult] = field(default_factory=list)

    def all_checks(self) -> list[CheckResult]:
        # Services are soft checks — excluded from gap score
        return self.syntax + self.cli + self.modules + self.state

    def failures(self) -> list[CheckResult]:
        return [c for c in self.all_checks() if not c.passed]

    def gap_score(self) -> float:
        checks = self.all_checks()
        if not checks:
            return 1.0
        return sum(1 for c in checks if c.passed) / len(checks)

    def passed(self) -> bool:
        return all(c.passed for c in self.all_checks())


# ── Main entry point ──────────────────────────────────────────────────────────


def run_all(
    quick: bool = False,
    repo_root: str = ".",
    specs_dir: str = "specs",
) -> EvalResult:
    result = EvalResult()

    # ── 1. Syntax ─────────────────────────────────────────────────────────────
    result.syntax = check_syntax(src_dir=str(Path(repo_root) / "src"))

    # ── 2. CLI commands ───────────────────────────────────────────────────────
    cli_spec = _load_spec(specs_dir, "cli_spec.json")
    if cli_spec:
        result.cli = check_cli_commands(cli_spec, repo_root=repo_root)

    # ── 3. Module imports ─────────────────────────────────────────────────────
    module_spec = _load_spec(specs_dir, "module_spec.json")
    if module_spec:
        result.modules = check_module_imports(module_spec, repo_root=repo_root)

    if not quick:
        # ── 4. Service ports (soft) ────────────────────────────────────────────
        services_spec = _load_spec(specs_dir, "services_spec.json")
        if services_spec:
            result.services = check_service_ports(services_spec)

        # ── 5. State file integrity ────────────────────────────────────────────
        result.state = check_state_files()

    return result
