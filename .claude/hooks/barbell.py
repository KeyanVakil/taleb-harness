#!/usr/bin/env python3
"""Barbell: reject Write/Edit/MultiEdit diffs > SAFE_MAX lines,
unless the target lives under .harness/spikes/."""
import difflib
from _lib import before_after, fail, read_payload

SAFE_MAX = 15
SPIKE_DIR = ".harness/spikes"


def main() -> None:
    ba = before_after(read_payload())
    if ba is None:
        return
    before, after, path = ba
    if SPIKE_DIR in str(path).replace("\\", "/"):
        return
    diff = difflib.ndiff(before.splitlines(), after.splitlines())
    changed = sum(1 for l in diff if l.startswith(("+ ", "- ")))
    if changed > SAFE_MAX:
        fail(
            f"Barbell violation: {changed} lines changed (limit {SAFE_MAX}). "
            f"Split into smaller safe edits, or put this under {SPIKE_DIR}/."
        )


if __name__ == "__main__":
    main()
