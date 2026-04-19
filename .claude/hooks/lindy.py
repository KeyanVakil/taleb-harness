#!/usr/bin/env python3
"""Lindy guard — PreToolUse hook for Write / Edit / MultiEdit.

A file that has survived unmodified for a long time is load-bearing by
revealed preference. The Lindy effect says its life expectancy is *longer*
than a fresh file's, not shorter. So edits to it require explicit override.

Sources: `git log -1 --format=%ct -- <path>`. Untracked files are ignored.
Brand-new files have no history; no concern.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HARD_AGE_DAYS = 365
SOFT_AGE_DAYS = 30
OVERRIDE_FILE = ".harness/lindy_overrides.txt"


def _file_age_days(cwd: Path, rel: str) -> float | None:
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", rel],
            capture_output=True, text=True, cwd=str(cwd), timeout=5,
        )
    except Exception:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        ts = int(r.stdout.strip())
    except ValueError:
        return None
    return (time.time() - ts) / 86400


def _is_overridden(cwd: Path, path: str) -> bool:
    override = cwd / OVERRIDE_FILE
    if not override.exists():
        return False
    try:
        return path in override.read_text(encoding="utf-8")
    except OSError:
        return False


def main() -> int:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input") or {}
    path_str = tool_input.get("file_path", "")
    if not path_str:
        return 0

    cwd = Path(payload.get("cwd", "."))
    path = Path(path_str)
    if not path.exists():
        return 0

    try:
        rel = str(path.resolve().relative_to(cwd.resolve()))
    except ValueError:
        rel = str(path)

    if _is_overridden(cwd, rel):
        return 0

    age = _file_age_days(cwd, rel)
    if age is None:
        return 0

    if age > HARD_AGE_DAYS:
        print(
            f"Lindy guard: {rel} has survived {int(age)} days unmodified. "
            f"It has earned its place. To edit it, append the path and a "
            f"reason to {OVERRIDE_FILE}.",
            file=sys.stderr,
        )
        return 2
    if age > SOFT_AGE_DAYS:
        print(
            f"Lindy note: {rel} was last touched {int(age)} days ago. "
            f"Proceed, but tread carefully.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
