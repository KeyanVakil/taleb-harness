#!/usr/bin/env python3
"""Addition budget — PreToolUse hook for Write / Edit / MultiEdit.

Via negativa, sharpened. The session has a budget of net-added lines.
Every write that adds lines consumes it; deletions refund it. When the
budget is exhausted, further additions are rejected until the agent
deletes code elsewhere or raises the budget in
.harness/addition_budget.json with a written justification.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_BUDGET = 300
STATE_PATH = ".harness/addition_budget.json"


def _load_state(cwd: Path) -> dict:
    p = cwd / STATE_PATH
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"budget": DEFAULT_BUDGET, "spent": 0}


def _save_state(cwd: Path, state: dict) -> None:
    p = cwd / STATE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state), encoding="utf-8")


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
    # Harness metadata and spikes don't count toward the real-code budget.
    norm = path_str.replace("\\", "/")
    if ".harness/" in norm or norm.endswith(".harness"):
        return 0

    cwd = Path(payload.get("cwd", "."))
    path = Path(path_str)
    before = path.read_text(encoding="utf-8") if path.exists() else ""
    after = _compute_after(tool_name, tool_input, before)
    delta = len(after.splitlines()) - len(before.splitlines())

    state = _load_state(cwd)
    new_spent = state.get("spent", 0) + delta
    budget = state.get("budget", DEFAULT_BUDGET)

    if new_spent > budget:
        print(
            f"Via negativa budget exceeded: {new_spent} net lines added "
            f"(budget: {budget}). Before continuing, DELETE code elsewhere "
            f"to refund the budget, or raise the budget in {STATE_PATH} "
            f"with a written justification.",
            file=sys.stderr,
        )
        return 2

    state["spent"] = new_spent
    _save_state(cwd, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
