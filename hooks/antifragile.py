#!/usr/bin/env python3
"""Antifragile bookkeeping — PostToolUse.

Bash + test keyword:
  exit 0 -> stamp .harness/last_green_run AND auto-commit the tree
  exit != 0 -> append to .harness/lessons.md
Write/Edit/MultiEdit:
  invalidate .harness/last_green_run (code changed, re-test required)
"""
import subprocess
import time
from pathlib import Path
from _lib import read_payload

TEST_KEYWORDS = (
    "pytest", "unittest", "npm test", "npm run test",
    "cargo test", "go test", "mvn test", "gradle test",
    "bazel test", "tox", "vitest", "jest",
)
MARKER = ".harness/last_green_run"
LESSONS = ".harness/lessons.md"


def _test_like(cmd: str) -> bool:
    return any(k in cmd.lower() for k in TEST_KEYWORDS)


def _exit_code(response: dict) -> int:
    v = response.get("exit_code", response.get("exitCode", 0))
    try:
        return int(v) if v is not None else 0
    except (TypeError, ValueError):
        return 0


def _auto_commit(cwd: Path, cmd: str) -> None:
    try:
        subprocess.run(["git", "add", "-A"], cwd=str(cwd), timeout=10,
                       capture_output=True)
        staged = subprocess.run(["git", "diff", "--cached", "--quiet"],
                                cwd=str(cwd), timeout=10, capture_output=True)
        if staged.returncode == 0:
            return
        subprocess.run(
            ["git", "commit", "-m",
             f"harness: auto-commit after green test run\n\ncmd: {cmd[:120]}"],
            cwd=str(cwd), timeout=15, capture_output=True,
        )
    except Exception:
        pass


def main() -> None:
    payload = read_payload()
    tool = payload.get("tool_name", "")
    cwd = Path(payload.get("cwd", "."))
    try:
        if tool == "Bash":
            cmd = (payload.get("tool_input") or {}).get("command", "")
            if not _test_like(cmd):
                return
            (cwd / ".harness").mkdir(parents=True, exist_ok=True)
            if _exit_code(payload.get("tool_response") or {}) == 0:
                (cwd / MARKER).write_text(
                    f"{int(time.time())}\n{cmd[:200]}\n", encoding="utf-8"
                )
                _auto_commit(cwd, cmd)
            else:
                with (cwd / LESSONS).open("a", encoding="utf-8") as f:
                    f.write(
                        f"- [{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"test_failed: {cmd[:120]}\n"
                    )
        elif tool in ("Write", "Edit", "MultiEdit"):
            marker = cwd / MARKER
            if marker.exists():
                marker.unlink()
    except Exception:
        pass  # bookkeeping must never break a tool call


if __name__ == "__main__":
    main()
