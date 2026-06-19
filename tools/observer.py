"""
SOS verify observer — sense the system's health without a web server.

Five check types:
  1. syntax       — py_compile each src/*.py file
  2. cli           — subprocess each CLI command, validate exit code + JSON keys
  3. modules       — importlib.import_module + optional class instantiation
  4. services      — TCP socket probe (soft checks — DOWN ≠ SOS code failure)
  5. state_files   — JSON key integrity for ~/.openclaw state files
"""

from __future__ import annotations

import importlib
import json
import py_compile
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ── Data types ────────────────────────────────────────────────────────────────


@dataclass
class CheckResult:
    id: str
    label: str
    passed: bool
    detail: str = ""
    elapsed_ms: float = 0.0


# ── 1. Python syntax ──────────────────────────────────────────────────────────


def check_syntax(src_dir: str = "src") -> list[CheckResult]:
    results: list[CheckResult] = []
    p = Path(src_dir)
    if not p.exists():
        return [
            CheckResult(
                id="syntax_dir",
                label=f"{src_dir}/ exists",
                passed=False,
                detail=f"Directory not found: {src_dir}",
            )
        ]

    for py_file in sorted(p.glob("*.py")):
        t0 = time.perf_counter()
        try:
            py_compile.compile(str(py_file), doraise=True)
            results.append(
                CheckResult(
                    id=f"syntax_{py_file.stem}",
                    label=f"syntax: {py_file.name}",
                    passed=True,
                    elapsed_ms=(time.perf_counter() - t0) * 1000,
                )
            )
        except py_compile.PyCompileError as e:
            results.append(
                CheckResult(
                    id=f"syntax_{py_file.stem}",
                    label=f"syntax: {py_file.name}",
                    passed=False,
                    detail=str(e),
                    elapsed_ms=(time.perf_counter() - t0) * 1000,
                )
            )
    return results


# ── 2. CLI commands ───────────────────────────────────────────────────────────


def check_cli_commands(spec: dict[str, Any], repo_root: str = ".") -> list[CheckResult]:
    results: list[CheckResult] = []
    python_bin = spec.get("python_bin", ".venv/bin/python")
    entry = spec.get("entry", "src/__main__.py")

    # Resolve python bin — fall back to sys.executable if venv not present
    python_path = Path(repo_root) / python_bin
    python_path_str = sys.executable if not python_path.exists() else str(python_path)

    entry_path = str(Path(repo_root) / entry)

    for cmd_spec in spec.get("commands", []):
        cmd_id = cmd_spec["id"]
        cmd_args = cmd_spec["command"].split()
        required_keys = cmd_spec.get("required_keys", [])
        expected_exit = cmd_spec.get("expected_exit", 0)
        label = f"cli: {cmd_spec['command']}"

        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                [python_path_str, entry_path] + cmd_args,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=repo_root,
            )
            elapsed = (time.perf_counter() - t0) * 1000

            # Check exit code
            if isinstance(expected_exit, list):
                exit_ok = proc.returncode in expected_exit
            else:
                exit_ok = proc.returncode == expected_exit

            if not exit_ok:
                results.append(
                    CheckResult(
                        id=cmd_id,
                        label=label,
                        passed=False,
                        detail=f"exit={proc.returncode} (expected {expected_exit})\nstderr: {proc.stderr[:300]}",
                        elapsed_ms=elapsed,
                    )
                )
                continue

            # Parse JSON output
            if required_keys:
                try:
                    data = json.loads(proc.stdout.strip())
                    missing = [k for k in required_keys if k not in data]
                    if missing:
                        results.append(
                            CheckResult(
                                id=cmd_id,
                                label=label,
                                passed=False,
                                detail=f"missing keys: {missing}\noutput preview: {proc.stdout[:300]}",
                                elapsed_ms=elapsed,
                            )
                        )
                        continue
                except json.JSONDecodeError as e:
                    results.append(
                        CheckResult(
                            id=cmd_id,
                            label=label,
                            passed=False,
                            detail=f"non-JSON output: {e}\npreview: {proc.stdout[:200]}",
                            elapsed_ms=elapsed,
                        )
                    )
                    continue

            results.append(CheckResult(id=cmd_id, label=label, passed=True, elapsed_ms=elapsed))

        except subprocess.TimeoutExpired:
            results.append(
                CheckResult(
                    id=cmd_id,
                    label=label,
                    passed=False,
                    detail="timed out after 30s",
                    elapsed_ms=(time.perf_counter() - t0) * 1000,
                )
            )
        except Exception as e:
            results.append(
                CheckResult(
                    id=cmd_id,
                    label=label,
                    passed=False,
                    detail=str(e),
                    elapsed_ms=(time.perf_counter() - t0) * 1000,
                )
            )

    return results


# ── 3. Python module imports ──────────────────────────────────────────────────


def check_module_imports(spec: dict[str, Any], repo_root: str = ".") -> list[CheckResult]:
    results: list[CheckResult] = []
    src_dir = spec.get("src_dir", "src")
    abs_src = str(Path(repo_root) / src_dir)

    # Temporarily add src to sys.path
    inserted = False
    if abs_src not in sys.path:
        sys.path.insert(0, abs_src)
        inserted = True

    try:
        for mod_spec in spec.get("modules", []):
            mod_id = mod_spec["id"]
            mod_name = mod_spec["module"]
            class_name = mod_spec.get("class")
            label = f"import: {mod_name}" + (f".{class_name}" if class_name else "")

            t0 = time.perf_counter()
            try:
                mod = importlib.import_module(mod_name)
                elapsed = (time.perf_counter() - t0) * 1000

                if class_name:
                    cls = getattr(mod, class_name, None)
                    if cls is None:
                        results.append(
                            CheckResult(
                                id=mod_id,
                                label=label,
                                passed=False,
                                detail=f"class {class_name} not found in {mod_name}",
                                elapsed_ms=elapsed,
                            )
                        )
                        continue

                results.append(CheckResult(id=mod_id, label=label, passed=True, elapsed_ms=elapsed))

            except ImportError as e:
                results.append(
                    CheckResult(
                        id=mod_id,
                        label=label,
                        passed=False,
                        detail=str(e),
                        elapsed_ms=(time.perf_counter() - t0) * 1000,
                    )
                )
            except Exception as e:
                results.append(
                    CheckResult(
                        id=mod_id,
                        label=label,
                        passed=False,
                        detail=f"{type(e).__name__}: {e}",
                        elapsed_ms=(time.perf_counter() - t0) * 1000,
                    )
                )
    finally:
        if inserted and abs_src in sys.path:
            sys.path.remove(abs_src)

    return results


# ── 4. TCP service probes (soft — DOWN is not a SOS failure) ──────────────────


def check_service_ports(spec: dict[str, Any]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for svc in spec.get("services", []):
        svc_id = svc["id"]
        host = svc.get("host", "localhost")
        port = svc["port"]
        required = svc.get("required", False)
        label = f"service: {host}:{port} ({svc_id})"

        t0 = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=2):
                up = True
        except OSError:
            up = False
        elapsed = (time.perf_counter() - t0) * 1000

        if required and not up:
            results.append(
                CheckResult(
                    id=svc_id,
                    label=label,
                    passed=False,
                    detail=f"port {port} not reachable (required=True)",
                    elapsed_ms=elapsed,
                )
            )
        else:
            # Soft check: report status but never fail because services may intentionally be down
            results.append(
                CheckResult(
                    id=svc_id,
                    label=label + (" ✓ UP" if up else " — DOWN (expected when not running)"),
                    passed=True,  # soft: always passes unless required=True
                    detail=""
                    if up
                    else f"port {port} unreachable — SOS monitors this as a target, not a dependency",
                    elapsed_ms=elapsed,
                )
            )

    return results


# ── 5. State file integrity ───────────────────────────────────────────────────


def check_state_files(
    state_dir: str | None = None,
    required_keys_per_file: dict[str, list[str]] | None = None,
) -> list[CheckResult]:
    """Check JSON state files in ~/.openclaw/workspace/self-optimization/state/."""
    results: list[CheckResult] = []

    if state_dir is None:
        state_dir = str(Path.home() / ".openclaw" / "workspace" / "self-optimization" / "state")

    p = Path(state_dir)
    if not p.exists():
        results.append(
            CheckResult(
                id="state_dir",
                label=f"state dir: {state_dir}",
                passed=True,  # Soft — not yet initialised is fine
                detail="state directory not yet created (first run?)",
            )
        )
        return results

    for json_file in sorted(p.glob("*.json")):
        label = f"state: {json_file.name}"
        t0 = time.perf_counter()
        try:
            data = json.loads(json_file.read_text())
            elapsed = (time.perf_counter() - t0) * 1000

            # Check required keys if specified
            req_keys = (required_keys_per_file or {}).get(json_file.name, [])
            missing = [k for k in req_keys if k not in data]
            if missing:
                results.append(
                    CheckResult(
                        id=f"state_{json_file.stem}",
                        label=label,
                        passed=False,
                        detail=f"missing keys: {missing}",
                        elapsed_ms=elapsed,
                    )
                )
            else:
                results.append(
                    CheckResult(
                        id=f"state_{json_file.stem}",
                        label=label,
                        passed=True,
                        elapsed_ms=elapsed,
                    )
                )
        except json.JSONDecodeError as e:
            results.append(
                CheckResult(
                    id=f"state_{json_file.stem}",
                    label=label,
                    passed=False,
                    detail=f"corrupted JSON: {e}",
                    elapsed_ms=(time.perf_counter() - t0) * 1000,
                )
            )

    if not results:
        results.append(
            CheckResult(
                id="state_empty",
                label=f"state dir: {state_dir}",
                passed=True,
                detail="no state files yet (first run?)",
            )
        )

    return results
