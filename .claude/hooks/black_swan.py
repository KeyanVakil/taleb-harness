#!/usr/bin/env python3
"""Black swan checklist — Stop hook.

Before ending, require an enumerated list of edge cases that could break
the code — empty input, extreme size, unicode, concurrency, partial
failure, whatever applies — each with a note on how it's handled or why
it's out of scope.

Forces explicit thought about tails rather than optimism about the
happy path. Lives at .harness/black_swans.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CHECKLIST_PATH = ".harness/black_swans.md"
MIN_ITEMS = 3


def _block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))


def main() -> int:
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return 0
    cwd = Path(payload.get("cwd", "."))
    p = cwd / CHECKLIST_PATH
    if not p.exists():
        _block(
            f"Black swan checklist missing. Before ending, create "
            f"{CHECKLIST_PATH} listing at least {MIN_ITEMS} enumerated "
            f"edge cases that could break this code (empty input, size "
            f"extremes, unicode, concurrency, partial failure, etc.) and "
            f"for each one say how it's handled or why it's out of scope."
        )
        return 0
    text = p.read_text(encoding="utf-8")
    items = sum(
        1 for line in text.splitlines()
        if line.lstrip().startswith(("-", "*"))
    )
    if items < MIN_ITEMS:
        _block(
            f"Black swan checklist has only {items} item(s) "
            f"({CHECKLIST_PATH}); need at least {MIN_ITEMS}. "
            f"Think harder about what could break."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
