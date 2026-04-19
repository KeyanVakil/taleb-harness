#!/usr/bin/env python3
"""Lindy: reject edits to files unmodified > HARD_AGE_DAYS per git log.
Override via .harness/lindy_overrides.txt."""
import subprocess
import time
from pathlib import Path
from _lib import fail, read_payload

HARD_AGE_DAYS = 365
OVERRIDE = ".harness/lindy_overrides.txt"


def _age_days(cwd: Path, rel: str) -> float | None:
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", rel],
            capture_output=True, text=True, cwd=str(cwd), timeout=5,
        )
    except Exception:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        return (time.time() - int(r.stdout.strip())) / 86400
    except ValueError:
        return None


def main() -> None:
    payload = read_payload()
    path_str = (payload.get("tool_input") or {}).get("file_path")
    if not path_str:
        return
    cwd = Path(payload.get("cwd", "."))
    path = Path(path_str)
    if not path.exists():
        return
    try:
        rel = str(path.resolve().relative_to(cwd.resolve()))
    except ValueError:
        rel = path_str
    override = cwd / OVERRIDE
    if override.exists() and rel in override.read_text(encoding="utf-8"):
        return
    age = _age_days(cwd, rel)
    if age is not None and age > HARD_AGE_DAYS:
        fail(
            f"Lindy: {rel} has survived {int(age)} days unmodified. "
            f"It is load-bearing. Override via {OVERRIDE}."
        )


if __name__ == "__main__":
    main()
