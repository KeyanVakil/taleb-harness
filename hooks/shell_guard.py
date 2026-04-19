#!/usr/bin/env python3
"""Shell guard: reject known-destructive bash patterns. Floor, not ceiling."""
from _lib import fail, read_payload

PATTERNS = (
    "rm -rf /", "rm -fr /", ":(){ :|:& };:", "mkfs", "dd if=",
    "> /dev/sd", "git push --force", "git push -f ",
    "git reset --hard origin", "shutdown", "reboot",
)


def main() -> None:
    cmd = ((read_payload().get("tool_input") or {}).get("command") or "").lower()
    for pat in PATTERNS:
        if pat in cmd:
            fail(
                f"Shell guard: destructive pattern '{pat}'. Refused. "
                f"Ask the human if this is really needed."
            )


if __name__ == "__main__":
    main()
