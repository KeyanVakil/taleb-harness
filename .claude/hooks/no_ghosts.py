#!/usr/bin/env python3
"""No ghosts — PreToolUse hook for Write / Edit / MultiEdit.

Bans NEW `TODO` / `FIXME` / `XXX` / `HACK` markers. They are can-kicking:
notes to a future self that will never be actioned. Taleb's rule is that
you either complete the addition or complete the deletion — no middle.

Pre-existing markers are tolerated. Only markers the agent is ADDING in
this write trigger rejection.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GHOST_PATTERN = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")


def _apply_edit(content: str, old: str, new: str, replace_all: bool) -> str:
    if replace_all:
        return content.replace(old, new)
    idx = content.find(old)
    return content if idx == -1 else content[:idx] + new + content[idx + len(old):]


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
        for e in tool_input.get("edits", []):
            out = _apply_edit(
                out,
                e.get("old_string", ""),
                e.get("new_string", ""),
                e.get("replace_all", False),
            )
        return out
    return before


def main() -> int:
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0
    tool_input = payload.get("tool_input") or {}
    path_str = tool_input.get("file_path", "")
    if not path_str:
        return 0

    path = Path(path_str)
    before = path.read_text(encoding="utf-8") if path.exists() else ""
    after = _compute_after(tool_name, tool_input, before)
    before_count = len(GHOST_PATTERN.findall(before))
    after_count = len(GHOST_PATTERN.findall(after))

    if after_count > before_count:
        added = after_count - before_count
        print(
            f"No ghosts: this change adds {added} new "
            f"TODO/FIXME/XXX/HACK marker(s). Do the thing now or delete "
            f"the concern from the code. Can-kicking is not allowed.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
