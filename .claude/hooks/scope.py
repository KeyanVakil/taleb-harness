#!/usr/bin/env python3
"""Scope guard — PreToolUse hook for Write / Edit / MultiEdit.

Iatrogenics, sharpened. The agent declares the task's target paths in
.harness/scope.txt (one glob per line). Writes outside that list are
rejected. If scope.txt is absent, writes pass through (no scope declared
means no enforcement — but the Stop hook can require one if desired).
"""
from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path

SCOPE_PATH = ".harness/scope.txt"


def _load_patterns(cwd: Path) -> list[str] | None:
    p = cwd / SCOPE_PATH
    if not p.exists():
        return None
    patterns: list[str] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)
    return patterns


def _matches(path: str, patterns: list[str]) -> bool:
    norm = path.replace("\\", "/")
    for pat in patterns:
        if fnmatch.fnmatch(norm, pat):
            return True
    return False


def main() -> int:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input") or {}
    path_str = tool_input.get("file_path", "")
    if not path_str:
        return 0
    # Harness metadata is always writable.
    if ".harness" in path_str.replace("\\", "/"):
        return 0

    cwd = Path(payload.get("cwd", "."))
    patterns = _load_patterns(cwd)
    if patterns is None:
        return 0

    try:
        rel = str(Path(path_str).resolve().relative_to(cwd.resolve())).replace("\\", "/")
    except ValueError:
        rel = path_str.replace("\\", "/")

    if _matches(rel, patterns) or _matches(path_str, patterns):
        return 0

    print(
        f"Iatrogenic guard: '{rel}' is outside the declared scope "
        f"({SCOPE_PATH}). No drive-by edits. If this file is legitimately "
        f"required, append its path to {SCOPE_PATH} with a justification "
        f"comment (`# reason: ...`).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
