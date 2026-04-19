"""Shared helpers for harness hooks. Deliberately tiny."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def read_payload() -> dict:
    return json.load(sys.stdin)


def fail(reason: str) -> None:
    """Pre-hook rejection: stderr + exit 2 blocks the tool call."""
    print(reason, file=sys.stderr)
    sys.exit(2)


def block(reason: str) -> None:
    """Stop-hook rejection: JSON decision object on stdout, exit 0."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def _apply(content: str, old: str, new: str, replace_all: bool) -> str:
    if replace_all:
        return content.replace(old, new)
    idx = content.find(old)
    return content if idx == -1 else content[:idx] + new + content[idx + len(old):]


def before_after(payload: dict) -> tuple[str, str, Path] | None:
    """For Write/Edit/MultiEdit: return (before_content, after_content, path).
    Returns None for other tools or when there is no file_path."""
    tool = payload.get("tool_name", "")
    if tool not in ("Write", "Edit", "MultiEdit"):
        return None
    inp = payload.get("tool_input") or {}
    path_str = inp.get("file_path")
    if not path_str:
        return None
    path = Path(path_str)
    before = path.read_text(encoding="utf-8") if path.exists() else ""
    if tool == "Write":
        after = inp.get("content", "")
    elif tool == "Edit":
        after = _apply(before, inp.get("old_string", ""),
                       inp.get("new_string", ""), inp.get("replace_all", False))
    else:
        after = before
        for e in inp.get("edits", []):
            after = _apply(after, e.get("old_string", ""),
                           e.get("new_string", ""), e.get("replace_all", False))
    return before, after, path
