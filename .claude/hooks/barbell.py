#!/usr/bin/env python3
"""Barbell guard — PreToolUse hook for Write / Edit / MultiEdit.

Rejects any single write whose diff exceeds the safe threshold, unless the
target path is under the spike directory. Safe edits or bold spikes; never
a medium-sized refactor.
"""
from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path

SAFE_MAX_LINES = 15
SPIKE_DIR = ".harness/spikes"


def _apply_edit(content: str, old: str, new: str, replace_all: bool) -> str:
    if replace_all:
        return content.replace(old, new)
    idx = content.find(old)
    if idx == -1:
        return content
    return content[:idx] + new + content[idx + len(old):]


def _compute_after(tool_name: str, tool_input: dict, before: str) -> str:
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return _apply_edit(
            before,
            tool_input.get("old_string", ""),
            tool_input.get("new_string", ""),
            tool_input.get("replace_all", False),
        )
    if tool_name == "MultiEdit":
        out = before
        for edit in tool_input.get("edits", []):
            out = _apply_edit(
                out,
                edit.get("old_string", ""),
                edit.get("new_string", ""),
                edit.get("replace_all", False),
            )
        return out
    return before


def _diff_lines(before: str, after: str) -> int:
    diff = difflib.ndiff(before.splitlines(), after.splitlines())
    return sum(1 for line in diff if line.startswith(("+ ", "- ")))


def main() -> int:
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    path_str = tool_input.get("file_path", "")
    if not path_str:
        return 0

    if SPIKE_DIR in path_str.replace("\\", "/"):
        return 0

    path = Path(path_str)
    before = path.read_text(encoding="utf-8") if path.exists() else ""
    after = _compute_after(tool_name, tool_input, before)
    changed = _diff_lines(before, after)

    if changed > SAFE_MAX_LINES:
        print(
            f"Barbell violation: this change touches {changed} lines "
            f"(safe limit: {SAFE_MAX_LINES}). "
            f"Either split into smaller safe edits, or put this change "
            f"under {SPIKE_DIR}/ as a declared spike.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
