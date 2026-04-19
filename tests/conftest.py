"""Shared test helper: invoke a hook script with Claude-Code-style JSON on stdin."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "hooks"


@pytest.fixture
def run_hook():
    def _run(name: str, payload: dict, cwd: Path | None = None):
        return subprocess.run(
            [sys.executable, str(HOOKS_DIR / f"{name}.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else str(REPO_ROOT),
        )
    return _run
