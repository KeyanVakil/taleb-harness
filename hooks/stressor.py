#!/usr/bin/env python3
"""Stressor: re-run tests under PYTHONHASHSEED=random.
Opt-in via .harness/stress_test.sh."""
import os
import subprocess
from pathlib import Path
from _lib import block, read_payload

SCRIPT = ".harness/stress_test.sh"


def main() -> None:
    payload = read_payload()
    if payload.get("stop_hook_active"):
        return
    cwd = Path(payload.get("cwd", "."))
    script = cwd / SCRIPT
    if not script.exists():
        return
    env = {**os.environ, "PYTHONHASHSEED": "random"}
    try:
        r = subprocess.run(
            ["bash", str(script)], capture_output=True, text=True,
            cwd=str(cwd), timeout=180, env=env,
        )
    except Exception:
        return
    if r.returncode != 0:
        tail = ((r.stdout or "") + (r.stderr or ""))[-600:]
        block(
            f"Stressor: tests failed under random-seed rerun. "
            f"The suite is not fragility-free.\n{tail}"
        )


if __name__ == "__main__":
    main()
