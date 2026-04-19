"""The main agent loop — Taleb-shaped.

Loop invariants:
  - System prompt (cached) reminds the agent of the principles every turn.
  - Lessons from prior failures are appended fresh each turn (antifragility).
  - If the same failure kind repeats, the prompt forces a strategy change.
"""

from __future__ import annotations

import json
from pathlib import Path

from anthropic import Anthropic

from harness.lessons import LessonsLog
from harness.principles import (
    LESSONS_PATH,
    MAX_TURNS,
    REPEAT_FAILURE_THRESHOLD,
    SYSTEM_PROMPT,
)
from harness.tools import TOOL_SCHEMAS, AgentState, handle_tool


MODEL = "claude-opus-4-7"


def _system_blocks(state: AgentState) -> list[dict]:
    """Stable portion is cached; lessons tail is fresh each turn."""
    blocks: list[dict] = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    recent = state.lessons.recent_summary(10)
    repeating, kind = state.lessons.is_repeating(REPEAT_FAILURE_THRESHOLD)
    tail = f"\n## Lessons so far (antifragile memory)\n{recent}\n"
    if repeating:
        tail += (
            f"\n*** STRATEGY CHANGE REQUIRED ***\n"
            f"You have hit '{kind}' {state.lessons.repeat_count(kind)} times. "
            f"Do NOT retry the same approach. Step back and try a different angle.\n"
        )
    blocks.append({"type": "text", "text": tail})
    return blocks


def _serialize_content(blocks) -> list[dict]:
    """Convert SDK block objects into plain dicts for round-tripping."""
    out: list[dict] = []
    for b in blocks:
        if hasattr(b, "model_dump"):
            out.append(b.model_dump())
        elif isinstance(b, dict):
            out.append(b)
        else:
            out.append({"type": "text", "text": str(b)})
    return out


def run(task: str, work_dir: Path, max_turns: int = MAX_TURNS) -> int:
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / ".harness").mkdir(exist_ok=True)
    lessons = LessonsLog(work_dir / LESSONS_PATH)
    state = AgentState(work_dir=work_dir, lessons=lessons)
    client = Anthropic()

    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"Task: {task}\n\n"
                "Begin. State your plan in one sentence, then act."
            ),
        }
    ]

    for turn in range(1, max_turns + 1):
        print(f"\n-- turn {turn} " + "-" * 40, flush=True)
        resp = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=_system_blocks(state),
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        for block in resp.content:
            if block.type == "text" and block.text.strip():
                print(block.text)
            elif block.type == "tool_use":
                preview = json.dumps(block.input)[:200]
                print(f"> tool: {block.name}({preview})")

        messages.append({"role": "assistant", "content": _serialize_content(resp.content)})

        if resp.stop_reason == "end_turn":
            print("\n(agent ended turn without calling finish — stopping)")
            return 1

        tool_results: list[dict] = []
        finished = False
        for block in resp.content:
            if block.type != "tool_use":
                continue
            result = handle_tool(block.name, block.input, state)
            if result == "FINISH_SIGNAL":
                summary = block.input.get("summary", "(no summary)")
                print(f"\n[done] agent declared finish: {summary}")
                finished = True
                result = "acknowledged"
            print(f"  -> {result[:300]}")
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                }
            )

        if finished:
            return 0
        if not tool_results:
            print("(no tool calls and not ended — stopping)")
            return 1

        messages.append({"role": "user", "content": tool_results})

    print(f"\n(reached max_turns={max_turns} without finishing)")
    return 2
