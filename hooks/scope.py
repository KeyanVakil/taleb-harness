#!/usr/bin/env python3
"""Scope: reject writes outside globs in .harness/scope.txt.
No scope file = no enforcement."""
import fnmatch
from pathlib import Path
from _lib import fail, read_payload

SCOPE = ".harness/scope.txt"


def main() -> None:
    payload = read_payload()
    path_str = (payload.get("tool_input") or {}).get("file_path", "")
    if not path_str or ".harness" in path_str.replace("\\", "/"):
        return
    cwd = Path(payload.get("cwd", "."))
    scope_file = cwd / SCOPE
    if not scope_file.exists():
        return
    patterns = [
        ln.strip() for ln in scope_file.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    try:
        rel = str(Path(path_str).resolve().relative_to(cwd.resolve())).replace("\\", "/")
    except ValueError:
        rel = path_str.replace("\\", "/")
    if any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(path_str, p) for p in patterns):
        return
    fail(
        f"Iatrogenic guard: '{rel}' is outside the declared scope ({SCOPE}). "
        f"Append the path with a `# reason:` comment to allow."
    )


if __name__ == "__main__":
    main()
