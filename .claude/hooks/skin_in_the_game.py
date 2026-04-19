#!/usr/bin/env python3
"""Skin-in-the-game — Stop hook.

Before letting the agent end, require a recent green test run. The
antifragile PostToolUse hook stamps .harness/last_green_run on passing
test commands and clears it on any file edit. If the marker is missing
or stale, block Stop and tell the agent to re-test.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

GREEN_MARKER = ".harness/last_green_run"
MAX_STALENESS_SEC = 600


def _block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))


def main() -> int:
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return 0  # avoid infinite block loops

    cwd = Path(payload.get("cwd", "."))
    marker = cwd / GREEN_MARKER

    if not marker.exists():
        _block(
            "Skin in the game: no passing test run is recorded for this "
            "session (or the last one was invalidated by a later edit). "
            "Run your test suite (pytest / npm test / cargo test / go test / "
            "etc.) and see it pass before ending."
        )
        return 0

    age = time.time() - marker.stat().st_mtime
    if age > MAX_STALENESS_SEC:
        _block(
            f"Skin in the game: the last green test run was {int(age)}s "
            f"ago. Re-run tests to confirm current state still passes."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
