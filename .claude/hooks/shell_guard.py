#!/usr/bin/env python3
"""Shell guard — PreToolUse hook for Bash.

Floor, not ceiling: blocks known-destructive patterns so the agent cannot
stumble into them. The human operator is the real ceiling.
"""
from __future__ import annotations

import json
import sys

DESTRUCTIVE_PATTERNS = (
    "rm -rf /",
    "rm -fr /",
    ":(){ :|:& };:",
    "mkfs",
    "dd if=",
    "> /dev/sd",
    "git push --force",
    "git push -f ",
    "git reset --hard origin",
    "shutdown",
    "reboot",
)


def main() -> int:
    payload = json.load(sys.stdin)
    cmd = (payload.get("tool_input", {}).get("command") or "").lower()
    for pat in DESTRUCTIVE_PATTERNS:
        if pat in cmd:
            print(
                f"Shell guard: command contains destructive pattern '{pat}'. "
                f"Refused. Ask the human if this is really needed.",
                file=sys.stderr,
            )
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
