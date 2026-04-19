#!/usr/bin/env python3
"""Fold discipline — Stop hook.

Barbell, sharpened. Spikes are throwaway. If Stop is reached while
.harness/spikes/ still has files, the agent either hasn't folded the
learnings back into real code or has left contamination behind. Either
way, block Stop until spikes are folded (and deleted) or abandoned.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SPIKE_DIR = ".harness/spikes"


def _block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))


def main() -> int:
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return 0
    cwd = Path(payload.get("cwd", "."))
    spike_dir = cwd / SPIKE_DIR
    if not spike_dir.exists():
        return 0
    leftover = [p for p in spike_dir.rglob("*") if p.is_file()]
    if leftover:
        names = "\n".join(f"  - {p.relative_to(cwd)}" for p in leftover[:10])
        _block(
            f"Fold discipline: spikes must not outlive the task. "
            f"{len(leftover)} file(s) remain under {SPIKE_DIR}:\n{names}\n"
            f"Either fold the learnings into real code via small safe edits "
            f"and delete the spike, or explicitly abandon it (delete the "
            f"spike directory)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
