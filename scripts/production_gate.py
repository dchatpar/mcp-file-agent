#!/usr/bin/env python3
"""Run all pre-deploy checks in order; exit non-zero on first failure."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS: list[tuple[str, list[str], bool]] = [
    ("Generate sample data", [sys.executable, "scripts/generate_samples.py"], False),
    ("Ruff lint", ["ruff", "check", "src", "tests", "scripts", "install.py"], False),
    ("Pytest (full suite)", [sys.executable, "-m", "pytest", "-q"], False),
    ("Security tests", [sys.executable, "-m", "pytest", "tests/test_security.py", "-q"], False),
    ("E2E agent (5 checks)", [sys.executable, "-u", "scripts/e2e_verify.py"], True),
    (
        "Assignment spot-check (3 queries)",
        [sys.executable, "-u", "scripts/spotcheck_assignment.py"],
        True,
    ),
]


def _log(msg: str) -> None:
    print(msg, flush=True)


def _run_step(name: str, cmd: list[str], needs_api_key: bool, skip_e2e: bool) -> tuple[bool, float]:
    if needs_api_key and skip_e2e:
        _log(f"  SKIP: {name} (--skip-e2e)")
        return True, 0.0
    if needs_api_key:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        import os

        if not os.getenv("OPENAI_API_KEY"):
            _log(f"  SKIP: {name} (OPENAI_API_KEY not set)")
            return True, 0.0

    _log(f"  $ {' '.join(cmd)}")
    start = time.perf_counter()
    result = subprocess.run(cmd, cwd=ROOT, check=False)
    elapsed = time.perf_counter() - start
    ok = result.returncode == 0
    return ok, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pre-deploy checks")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip E2E and spot-check")
    args = parser.parse_args()
    skip_e2e = args.skip_e2e or os.getenv("INSTALL_SKIP_E2E") == "1"

    total = len(STEPS)
    _log(f"Production gate ({total} steps) - root: {ROOT}")
    if skip_e2e:
        _log("  (E2E / spot-check skipped)")
    _log("")

    results: list[tuple[str, bool, float]] = []
    for i, (name, cmd, needs_key) in enumerate(STEPS, start=1):
        _log(f"[{i}/{total}] {name}")
        ok, elapsed = _run_step(name, cmd, needs_key, skip_e2e)
        status = "PASS" if ok else "FAIL"
        _log(f"      {status} ({elapsed:.1f}s)")
        results.append((name, ok, elapsed))
        if not ok:
            _log("")
            _log("Production gate FAILED - fix the step above and re-run.")
            return 1
        _log("")

    _log("=" * 60)
    _log("Production gate PASSED")
    for name, ok, elapsed in results:
        _log(f"  {name}: PASS ({elapsed:.1f}s)")
    _log("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
