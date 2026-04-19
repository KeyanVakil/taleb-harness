#!/usr/bin/env python3
"""Auto-commit — PostToolUse hook for Bash.

Optionality, sharpened. After every green test run, snapshot the tree as
a git commit. The agent cannot lose work; every turn leaves a save point.
A pre-commit hook failure aborts the snapshot silently — the agent will
notice on next inspection.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TEST_KEYWORDS = (
    "pytest", "unittest", "npm test", "npm run test",
    "cargo test", "go test", "mvn test", "gradle test",
    "bazel test", "tox", "vitest", "jest",
)


def _looks_test_like(cmd: str) -> bool:
    return any(k in cmd.lower() for k in TEST_KEYWORDS)


def _in_git_repo(cwd: Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, cwd=str(cwd), timeout=5,
        )
    except Exception:
        return False
    return r.returncode == 0 and r.stdout.strip() == "true"


def main() -> int:
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input") or {}
    cmd = tool_input.get("command", "")
    response = payload.get("tool_response") or {}
    exit_code = response.get("exit_code")
    if exit_code is None:
        exit_code = response.get("exitCode", 0)
    try:
        exit_code = int(exit_code)
    except (TypeError, ValueError):
        exit_code = 0

    if exit_code != 0 or not _looks_test_like(cmd):
        return 0

    cwd = Path(payload.get("cwd", "."))
    if not _in_git_repo(cwd):
        return 0

    try:
        subprocess.run(
            ["git", "add", "-A"], cwd=str(cwd), timeout=10, capture_output=True,
        )
        staged = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=str(cwd), timeout=10, capture_output=True,
        )
        if staged.returncode == 0:
            return 0  # nothing to commit
        subprocess.run(
            [
                "git", "commit", "-m",
                f"harness: auto-commit after green test run\n\ncmd: {cmd[:120]}",
            ],
            cwd=str(cwd), timeout=15, capture_output=True,
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
