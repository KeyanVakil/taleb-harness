"""CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from harness.agent import run


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="harness",
        description=(
            "Taleb-shaped coding agent: via negativa, skin in the game, "
            "barbell, antifragile."
        ),
    )
    p.add_argument("task", help="The task for the agent, in plain English.")
    p.add_argument(
        "--dir",
        "-d",
        type=Path,
        default=Path.cwd(),
        help="Working directory (default: cwd).",
    )
    p.add_argument(
        "--max-turns",
        type=int,
        default=40,
        help="Safety cap on agent loop iterations.",
    )
    args = p.parse_args(argv)
    return run(args.task, args.dir.resolve(), max_turns=args.max_turns)


if __name__ == "__main__":
    sys.exit(main())
