#!/usr/bin/env python3
"""Skin in the game: block Stop until a fresh green test run is recorded."""
import time
from pathlib import Path
from _lib import block, read_payload

MARKER = ".harness/last_green_run"
MAX_STALENESS_SEC = 600


def main() -> None:
    payload = read_payload()
    if payload.get("stop_hook_active"):
        return
    marker = Path(payload.get("cwd", ".")) / MARKER
    if not marker.exists():
        block(
            "Skin in the game: no green test run recorded (or a later "
            "edit invalidated it). Run your tests and see them pass "
            "before ending."
        )
    age = time.time() - marker.stat().st_mtime
    if age > MAX_STALENESS_SEC:
        block(
            f"Skin in the game: last green run was {int(age)}s ago. "
            f"Re-run tests to confirm current state."
        )


if __name__ == "__main__":
    main()
