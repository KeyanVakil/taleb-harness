#!/usr/bin/env python3
"""Fold discipline: block Stop if .harness/spikes/ is non-empty."""
from pathlib import Path
from _lib import block, read_payload

SPIKE_DIR = ".harness/spikes"


def main() -> None:
    payload = read_payload()
    if payload.get("stop_hook_active"):
        return
    cwd = Path(payload.get("cwd", "."))
    spike_dir = cwd / SPIKE_DIR
    if not spike_dir.exists():
        return
    leftover = [p for p in spike_dir.rglob("*") if p.is_file()]
    if leftover:
        names = "\n".join(f"  - {p.relative_to(cwd)}" for p in leftover[:10])
        block(
            f"Fold discipline: {len(leftover)} spike file(s) remain under "
            f"{SPIKE_DIR}:\n{names}\nFold into safe edits, or delete."
        )


if __name__ == "__main__":
    main()
