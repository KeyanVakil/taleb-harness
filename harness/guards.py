"""Runtime enforcement of the barbell and shell rules.

Persuasion in the system prompt is not enough. These guards reject actions
that violate the principles, forcing the agent to reshape them.
"""

from __future__ import annotations

import difflib
from pathlib import Path

from harness.principles import BARBELL_SAFE_MAX_LINES, BARBELL_SPIKE_PATH


class GuardRejection(Exception):
    """Raised when an action violates a principle."""


def diff_line_count(before: str, after: str) -> int:
    """Count added+removed lines between two file contents."""
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    diff = difflib.ndiff(before_lines, after_lines)
    return sum(1 for line in diff if line.startswith(("+ ", "- ")))


def _is_spike_path(path: Path) -> bool:
    norm = str(path).replace("\\", "/")
    return norm.startswith(BARBELL_SPIKE_PATH) or f"/{BARBELL_SPIKE_PATH}/" in "/" + norm


def check_barbell(
    path: Path,
    before: str,
    after: str,
    spike_active: bool,
) -> None:
    """Reject edits that are neither small-and-safe nor inside a declared spike."""
    if spike_active or _is_spike_path(path):
        return
    changed = diff_line_count(before, after)
    if changed > BARBELL_SAFE_MAX_LINES:
        raise GuardRejection(
            f"Barbell violation: change touches {changed} lines "
            f"(safe limit: {BARBELL_SAFE_MAX_LINES}). "
            f"Split into smaller safe edits, or declare a spike first."
        )


DESTRUCTIVE_PATTERNS = (
    "rm -rf ",
    "rm -fr ",
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


def check_shell(cmd: str) -> None:
    lowered = cmd.strip().lower()
    for pat in DESTRUCTIVE_PATTERNS:
        if pat in lowered:
            raise GuardRejection(
                f"Shell guard: command contains destructive pattern '{pat}'. "
                f"Refused. Ask the human operator if this is truly needed."
            )
