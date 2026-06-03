#!/usr/bin/env python3
"""
Interactive production installer for Local File Search MCP Agent.

Usage (from repo root after clone):
    chmod +x install.py
    ./install.py

Flags:
    --non-interactive   Use defaults; no prompts (requires existing .env or --skip-e2e)
    --skip-e2e          Skip E2E and spot-check (no API key required)
    --yes               Accept defaults for all prompts
    --help              Show help
"""

from __future__ import annotations

import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
VENV_PYTHON = VENV_DIR / "bin" / "python"
SAMPLES_DIR = ROOT / "data" / "samples" / "zoology"
LEGACY_XLSX = SAMPLES_DIR / "species_count_2024.xlsx"
MIN_PYTHON = (3, 11)

PROVIDER_PRESETS = {
    "minimax": {
        "OPENAI_BASE_URL": "https://api.minimax.io/v1",
        "OPENAI_MODEL": "MiniMax-M2.7",
        "env_example": ".env.example",
    },
    "openai": {
        "OPENAI_BASE_URL": "https://api.openai.com/v1",
        "OPENAI_MODEL": "gpt-4o",
        "env_example": ".env.openai.example",
    },
}


def _log(msg: str) -> None:
    print(msg, flush=True)


def _header(title: str) -> None:
    _log("")
    _log("=" * 60)
    _log(title)
    _log("=" * 60)


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> int:
    _log(f"  $ {' '.join(cmd)}")
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=cwd or ROOT, env=merged, check=False).returncode


def _python_version_ok() -> bool:
    return sys.version_info >= MIN_PYTHON


def _is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        answer = input(f"{text}{suffix}: ").strip()
        if answer:
            return answer
        if default is not None:
            return default
        _log("  (required)")


def _prompt_yes_no(text: str, default: bool = True) -> bool:
    default_s = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{text} [{default_s}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        _log("  Enter y or n.")


def _prompt_choice(text: str, choices: dict[str, str], default_key: str) -> str:
    keys = "/".join(choices.keys())
    labels = ", ".join(f"{k}={v}" for k, v in choices.items())
    _log(f"  ({labels})")
    while True:
        answer = input(f"{text} [{default_key}]: ").strip().lower()
        if not answer:
            return default_key
        if answer in choices:
            return answer
        _log(f"  Choose one of: {keys}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Local File Search MCP Agent to production-ready state."
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="No prompts; use defaults and existing .env",
    )
    parser.add_argument(
        "--skip-e2e",
        action="store_true",
        help="Skip E2E and spot-check (no API key needed)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Accept default answers for all prompts",
    )
    return parser.parse_args()


def run_wizard(args: argparse.Namespace) -> dict:
    """Collect install configuration via interactive prompts."""
    interactive = not args.non_interactive and _is_tty() and not args.yes
    config: dict = {
        "provider": "minimax",
        "api_key": "",
        "search_root": "data/samples/zoology",
        "run_e2e": not args.skip_e2e,
        "build_docker": False,
        "env_action": "create",
    }

    env_path = ROOT / ".env"
    if env_path.exists():
        try:
            from dotenv import dotenv_values

            existing = dotenv_values(env_path)
            if existing.get("OPENAI_API_KEY"):
                config["api_key"] = existing["OPENAI_API_KEY"]
                if interactive:
                    action = _prompt_choice(
                        "Existing .env with API key found. keep/merge/overwrite?",
                        {"k": "keep", "m": "merge", "o": "overwrite"},
                        "k",
                    )
                    config["env_action"] = {"k": "keep", "m": "merge", "o": "overwrite"}[
                        action
                    ]
                else:
                    config["env_action"] = "keep"
        except ImportError:
            pass

    if not interactive:
        if config["env_action"] != "keep" and not config["api_key"]:
            _log("Non-interactive mode: set OPENAI_API_KEY in .env or use --skip-e2e")
        return config

    _header("Install wizard")
    _log("Answer a few questions to configure the agent.\n")

    provider_key = _prompt_choice(
        "LLM provider",
        {"m": "minimax", "o": "openai"},
        "m",
    )
    config["provider"] = {"m": "minimax", "o": "openai"}[provider_key]
    if config["env_action"] in ("create", "overwrite", "merge"):
        config["api_key"] = getpass.getpass("OPENAI_API_KEY (hidden, Enter to skip): ")
    config["search_root"] = _prompt(
        "SEARCH_ROOT (sample / search directory)",
        "data/samples/zoology",
    )
    if not args.skip_e2e:
        config["run_e2e"] = _prompt_yes_no(
            "Run full E2E + spot-check now (~1-2 min, uses API)?",
            default=True,
        )
    if shutil.which("docker"):
        config["build_docker"] = _prompt_yes_no(
            "Build Docker image after verification?",
            default=False,
        )
    if not _prompt_yes_no("Proceed with install?", default=True):
        _log("Install cancelled.")
        sys.exit(0)

    return config


def heal_excel_duplicate() -> list[str]:
    healed: list[str] = []
    if LEGACY_XLSX.exists():
        LEGACY_XLSX.unlink()
        healed.append(f"Removed broken duplicate {LEGACY_XLSX.name}")
    return healed


def heal_sample_count() -> list[str]:
    healed: list[str] = []
    if not SAMPLES_DIR.exists():
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    count = sum(1 for p in SAMPLES_DIR.iterdir() if p.is_file())
    if count != 8:
        healed.append(f"Sample count was {count}, regenerating to 8 files")
        rc = _run([sys.executable, "scripts/generate_samples.py"])
        if rc != 0:
            raise RuntimeError("generate_samples.py failed")
    return healed


def ensure_venv() -> None:
    if not _python_version_ok():
        _log(f"ERROR: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required.")
        _log("  sudo apt install python3.12 python3.12-venv")
        sys.exit(1)

    if not VENV_PYTHON.exists():
        _log("Creating virtual environment .venv ...")
        rc = _run([sys.executable, "-m", "venv", str(VENV_DIR)])
        if rc != 0:
            _log("ERROR: venv creation failed. Try: sudo apt install python3-venv")
            sys.exit(1)

    rc = _run(
        [str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]
    )
    if rc != 0:
        raise RuntimeError("pip upgrade failed")


def install_dependencies(retry: bool = True) -> None:
    rc = _run([str(VENV_PYTHON), "-m", "pip", "install", "-e", ".[dev]"])
    if rc != 0 and retry:
        _log("Retrying pip install after upgrade...")
        _run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"])
        rc = _run([str(VENV_PYTHON), "-m", "pip", "install", "-e", ".[dev]"])
    if rc != 0:
        raise RuntimeError("pip install -e '.[dev]' failed")


def write_env(config: dict) -> None:
    env_path = ROOT / ".env"
    if config["env_action"] == "keep" and env_path.exists():
        _log("Keeping existing .env")
        return

    preset = PROVIDER_PRESETS[config["provider"]]
    example = ROOT / preset["env_example"]
    if not example.exists():
        example = ROOT / ".env.example"

    lines: list[str] = []
    if config["env_action"] == "merge" and env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    def set_var(key: str, value: str) -> None:
        nonlocal lines
        prefix = f"{key}="
        lines = [ln for ln in lines if not ln.startswith(prefix)]
        lines.append(f"{prefix}{value}")

    if config["env_action"] in ("create", "overwrite") and example.exists():
        lines = [
            ln
            for ln in example.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]

    set_var("OPENAI_BASE_URL", preset["OPENAI_BASE_URL"])
    set_var("OPENAI_MODEL", preset["OPENAI_MODEL"])
    set_var("SEARCH_ROOT", config["search_root"])
    set_var("FILE_SEARCH_ROOT", config["search_root"])
    if config["api_key"]:
        set_var("OPENAI_API_KEY", config["api_key"])

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        env_path.chmod(0o600)
    except OSError:
        pass
    _log(f"Wrote {env_path}")


def run_production_gate(skip_e2e: bool) -> int:
    cmd = [str(VENV_PYTHON), "-u", "scripts/production_gate.py"]
    if skip_e2e:
        cmd.append("--skip-e2e")
    return _run(cmd)


def build_docker() -> None:
    if not shutil.which("docker"):
        _log("Docker not installed; skipping build.")
        return
    rc = _run(["docker", "compose", "build"])
    if rc != 0:
        _log("WARNING: docker compose build failed (non-fatal)")


def print_summary(config: dict, gate_ok: bool) -> None:
    _header("Production install summary")
    _log(f"  Root:        {ROOT}")
    _log(f"  Venv:        {VENV_DIR}")
    sample_count = 0
    if SAMPLES_DIR.exists():
        sample_count = sum(1 for p in SAMPLES_DIR.iterdir() if p.is_file())
    _log(f"  Samples:     {SAMPLES_DIR} ({sample_count} files)")
    _log(f"  Provider:    {config['provider']}")
    _log(f"  Gate:        {'PASS' if gate_ok else 'FAIL'}")
    _log("")
    _log("  Run CLI:     source .venv/bin/activate && file-search-agent")
    _log("  Re-verify:   python -u scripts/production_gate.py")
    _log("  Docs:        docs/DEPLOYMENT.md")
    _log("  systemd:     deploy/file-search-agent.service.example")
    _log("=" * 60)


def main() -> int:
    args = parse_args()
    _header("Local File Search MCP Agent - Production Installer")
    _log(f"Repository: {ROOT}\n")

    config = run_wizard(args)
    skip_e2e = args.skip_e2e or not config.get("run_e2e", True)

    all_healed: list[str] = []
    _header("Phase 1 - Auto-heal")
    all_healed.extend(heal_excel_duplicate())
    for msg in all_healed:
        _log(f"  [healed] {msg}")

    _header("Phase 2 - Virtual environment")
    ensure_venv()

    _header("Phase 3 - Dependencies")
    install_dependencies()

    _header("Phase 4 - Configuration")
    write_env(config)

    _header("Phase 5 - Sample data")
    sample_healed = heal_sample_count()
    all_healed.extend(sample_healed)
    for msg in sample_healed:
        _log(f"  [healed] {msg}")

    _header("Phase 6 - Production gate")
    if skip_e2e:
        _log("  (E2E / spot-check skipped)")
    gate_rc = run_production_gate(skip_e2e)
    if gate_rc != 0:
        _log("Gate failed; attempting heal + retry once...")
        heal_excel_duplicate()
        heal_sample_count()
        gate_rc = run_production_gate(skip_e2e)

    if config.get("build_docker"):
        _header("Phase 7 - Docker")
        build_docker()

    print_summary(config, gate_rc == 0)
    return 0 if gate_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
