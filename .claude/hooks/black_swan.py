#!/usr/bin/env python3
"""Black swan: require .harness/black_swans.md with >= MIN_ITEMS bullets."""
from pathlib import Path
from _lib import block, read_payload

CHECKLIST = ".harness/black_swans.md"
MIN_ITEMS = 3


def main() -> None:
    payload = read_payload()
    if payload.get("stop_hook_active"):
        return
    path = Path(payload.get("cwd", ".")) / CHECKLIST
    if not path.exists():
        block(
            f"Black swan checklist missing. Create {CHECKLIST} with "
            f">= {MIN_ITEMS} enumerated edge cases (empty input, size "
            f"extremes, unicode, concurrency, partial failure, etc.) "
            f"and a note on how each is handled or why out of scope."
        )
    items = sum(
        1 for line in path.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith(("-", "*"))
    )
    if items < MIN_ITEMS:
        block(
            f"Black swan checklist has {items} item(s); need {MIN_ITEMS}. "
            f"Think harder about what could break."
        )


if __name__ == "__main__":
    main()
