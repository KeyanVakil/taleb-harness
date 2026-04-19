"""Antifragile feedback store.

Failures are not forgotten. Each one is appended here and reinjected into the
next turn's context. If the agent repeats a lesson, the system prompt forces
a strategy change.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Lesson:
    kind: str
    detail: str
    when: float = field(default_factory=time.time)

    def format(self) -> str:
        return f"- [{self.kind}] {self.detail}"


class LessonsLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.lessons: list[Lesson] = []

    def record(self, kind: str, detail: str) -> Lesson:
        detail = detail.strip().replace("\n", " ")[:300]
        lesson = Lesson(kind=kind, detail=detail)
        self.lessons.append(lesson)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(lesson.format() + "\n")
        return lesson

    def repeat_count(self, kind: str) -> int:
        return sum(1 for l in self.lessons if l.kind == kind)

    def is_repeating(self, threshold: int) -> tuple[bool, str | None]:
        counts = Counter(l.kind for l in self.lessons)
        for kind, n in counts.items():
            if n >= threshold:
                return True, kind
        return False, None

    def recent_summary(self, n: int = 10) -> str:
        if not self.lessons:
            return "(no lessons yet)"
        return "\n".join(l.format() for l in self.lessons[-n:])
