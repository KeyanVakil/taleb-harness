#!/usr/bin/env python3
"""Antifragile bookkeeping — PostToolUse hook.

Bash:
  - test-like command + exit 0 → stamp .harness/last_green_run
  - test-like command + exit != 0 → append to .harness/lessons.md
Write/Edit/MultiEdit:
  - invalidate .harness/last_green_run (code has changed; re-test required)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

TEST_KEYWORDS = (
    "pytest", "unittest", "npm test", "npm run test",
    "cargo test", "go test", "mvn test", "gradle test",
    "bazel test", "tox", "vitest", "jest",
)

LESSONS_PATH = ".harness/lessons.md"
GREEN_MARKER = ".harness/last_green_run"


def _looks_test_like(cmd: str) -> bool:
    lowered = cmd.lower()
    return any(k in lowered for k in TEST_KEYWORDS)


def _coerce_int(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _handle_bash(payload: dict, cwd: Path) -> None:
    tool_input = payload.get("tool_input") or {}
    cmd = tool_input.get("command", "")
    response = payload.get("tool_response") or {}
    exit_code = (
        response.get("exit_code")
        if response.get("exit_code") is not None
        else response.get("exitCode")
        if response.get("exitCode") is not None
        else response.get("returncode", 0)
    )
    exit_code = _coerce_int(exit_code)

    if not _looks_test_like(cmd):
        return

    (cwd / ".harness").mkdir(parents=True, exist_ok=True)
    if exit_code == 0:
        (cwd / GREEN_MARKER).write_text(
            f"{int(time.time())}\n{cmd[:200]}\n",
            encoding="utf-8",
        )
    else:
        with (cwd / LESSONS_PATH).open("a", encoding="utf-8") as f:
            f.write(
                f"- [{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"test_failed: {cmd[:120]} (exit={exit_code})\n"
            )


def _handle_write(cwd: Path) -> None:
    marker = cwd / GREEN_MARKER
    if marker.exists():
        try:
            marker.unlink()
        except OSError:
            pass


def main() -> int:
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name", "")
    cwd = Path(payload.get("cwd", "."))
    try:
        if tool_name == "Bash":
            _handle_bash(payload, cwd)
        elif tool_name in ("Write", "Edit", "MultiEdit"):
            _handle_write(cwd)
    except Exception:
        pass  # bookkeeping must never break a tool call
    return 0


if __name__ == "__main__":
    sys.exit(main())
