#!/usr/bin/env python3
"""Stressor — Stop hook.

Fragility detection. After the green marker confirms the tests passed,
re-run them under perturbation: `PYTHONHASHSEED=random` + whatever
reshuffling the project's runner supports. If the suite fails under
stress, the passing result isn't actually proving much — it was order-
or seed-dependent. Block Stop with the failure tail.

Opt-in. The project provides .harness/stress_test.sh; the hook only
fires if that script exists. This avoids guessing the test runner.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

STRESS_SCRIPT = ".harness/stress_test.sh"


def _block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))


def main() -> int:
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return 0
    cwd = Path(payload.get("cwd", "."))
    script = cwd / STRESS_SCRIPT
    if not script.exists():
        return 0

    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "random"
    try:
        r = subprocess.run(
            ["bash", str(script)],
            capture_output=True, text=True,
            cwd=str(cwd), timeout=180, env=env,
        )
    except Exception:
        return 0

    if r.returncode != 0:
        tail = ((r.stdout or "") + (r.stderr or ""))[-600:]
        _block(
            f"Stressor: tests failed under reshuffled / random-seed "
            f"execution. The suite is not fragility-free. Tail:\n{tail}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
