"""Tools the agent can call. Each one is a principle in executable form."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from harness.guards import GuardRejection, check_barbell, check_shell
from harness.lessons import LessonsLog
from harness.principles import BARBELL_SPIKE_PATH


@dataclass
class AgentState:
    work_dir: Path
    lessons: LessonsLog
    spike_active: bool = False
    spike_hypothesis: str = ""
    deletion_considered: bool = False
    files_touched: set[Path] = field(default_factory=set)


TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read a file from the working directory. Returns its contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path from work dir"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Write or overwrite a file. Enforces the barbell rule: if the diff "
            "exceeds the safe threshold and no spike is active, the write is "
            "rejected. Writes under .harness/spikes/ bypass the limit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_shell",
        "description": (
            "Run a shell command in the working directory. This is your skin in "
            "the game — use it to run tests, type checks, builds. Destructive "
            "commands are blocked."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cmd": {"type": "string"},
                "timeout_sec": {"type": "integer", "default": 60},
            },
            "required": ["cmd"],
        },
    },
    {
        "name": "consider_deletion",
        "description": (
            "Via negativa. Record that you've considered whether the task can be "
            "solved by DELETING code rather than adding. Call this before any "
            "non-trivial addition. Arguments: `target` (what could be removed) "
            "and `verdict` ('delete' or 'keep' with a one-line reason)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "verdict": {"type": "string"},
            },
            "required": ["target", "verdict"],
        },
    },
    {
        "name": "declare_spike",
        "description": (
            "Begin an exploratory experiment. Bypasses barbell size limits. "
            "Spike files must live under .harness/spikes/. Learnings should be "
            "folded back into safe edits; the spike itself is throwaway."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hypothesis": {
                    "type": "string",
                    "description": "What are you trying to learn? One sentence.",
                },
            },
            "required": ["hypothesis"],
        },
    },
    {
        "name": "end_spike",
        "description": "Close the spike. After this, barbell limits re-engage.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "record_lesson",
        "description": (
            "Antifragility. Record a failure or surprise so the next turn sees "
            "it. `kind` is a short tag like 'test_failed' or 'import_error'. "
            "`detail` is one line."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string"},
                "detail": {"type": "string"},
            },
            "required": ["kind", "detail"],
        },
    },
    {
        "name": "finish",
        "description": (
            "Declare the task complete. You must have run tests/checks and seen "
            "them pass. If you cannot demonstrate completion, do not call this "
            "— ask the human instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "lines_added": {"type": "integer"},
                "lines_deleted": {"type": "integer"},
            },
            "required": ["summary"],
        },
    },
]


def handle_tool(name: str, args: dict, state: AgentState) -> str:
    """Dispatch a tool call. Returns the tool_result content as a string."""
    try:
        if name == "read_file":
            return _read_file(state, args["path"])
        if name == "write_file":
            return _write_file(state, args["path"], args["content"])
        if name == "run_shell":
            return _run_shell(state, args["cmd"], args.get("timeout_sec", 60))
        if name == "consider_deletion":
            state.deletion_considered = True
            return (
                f"Recorded via-negativa check. "
                f"target={args['target']!r} verdict={args['verdict']!r}"
            )
        if name == "declare_spike":
            state.spike_active = True
            state.spike_hypothesis = args["hypothesis"]
            return (
                f"Spike open. Hypothesis: {args['hypothesis']}. "
                f"Barbell limits suspended; keep writes under {BARBELL_SPIKE_PATH}/."
            )
        if name == "end_spike":
            state.spike_active = False
            return "Spike closed. Barbell limits re-engaged."
        if name == "record_lesson":
            lesson = state.lessons.record(args["kind"], args["detail"])
            return f"Lesson recorded: {lesson.format()}"
        if name == "finish":
            return "FINISH_SIGNAL"
        return f"Unknown tool: {name}"
    except GuardRejection as e:
        state.lessons.record("guard_rejection", str(e))
        return f"REJECTED: {e}"
    except Exception as e:
        state.lessons.record("tool_error", f"{name}: {e}")
        return f"ERROR: {e}"


def _safe_path(state: AgentState, relpath: str) -> Path:
    root = state.work_dir.resolve()
    p = (root / relpath).resolve()
    if p != root and root not in p.parents:
        raise GuardRejection(f"Path escapes work_dir: {relpath}")
    return p


def _read_file(state: AgentState, relpath: str) -> str:
    p = _safe_path(state, relpath)
    if not p.exists():
        return f"(not found: {relpath})"
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"(binary file: {relpath})"


def _write_file(state: AgentState, relpath: str, content: str) -> str:
    p = _safe_path(state, relpath)
    before = p.read_text(encoding="utf-8") if p.exists() else ""
    check_barbell(Path(relpath), before, content, state.spike_active)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    state.files_touched.add(p)
    delta = len(content.splitlines()) - len(before.splitlines())
    return f"Wrote {relpath} (net line delta: {delta:+d})"


def _run_shell(state: AgentState, cmd: str, timeout: int) -> str:
    check_shell(cmd)
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=state.work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        state.lessons.record("shell_timeout", f"{cmd} (>{timeout}s)")
        return f"TIMEOUT after {timeout}s: {cmd}"
    out = (proc.stdout or "") + (proc.stderr or "")
    out = out[-4000:]
    if proc.returncode != 0:
        state.lessons.record("shell_nonzero", f"{cmd} -> rc={proc.returncode}")
    return f"exit={proc.returncode}\n{out}"
