# taleb-harness

A Nassim Taleb–shaped harness for Claude Code, encoded as **hooks**, not vibes.

Most coding-agent systems put "please be careful" in a system prompt and hope. This repo ships as a **Claude Code plugin** — Claude Code enforces the principles at the **tool-call level**, rejecting any action that violates them. Prompts are persuasion. Hooks are runtime.

## Install

```bash
# one-time, global:
claude plugin install taleb-harness

# or, for local dev against this repo:
claude --plugin-dir /path/to/taleb-harness
```

Then just run `claude` in any project. Hooks fire on every tool call.

## The principles, as hooks

| Principle | Hook | Enforcement |
|---|---|---|
| **Via negativa** | `no_ghosts` (Pre) + `addition_budget` (Pre) | Rejects new `TODO`/`FIXME`/`XXX`/`HACK` markers; tracks net lines added against a session budget |
| **Skin in the game** | `skin_in_the_game` (Stop) + `stressor` (Stop) | Blocks `Stop` without a recent green test run; optional stress-test rerun with `PYTHONHASHSEED=random` |
| **Barbell** | `barbell` (Pre) + `fold_discipline` (Stop) | Rejects Write/Edit/MultiEdit with >15-line diffs unless under `.harness/spikes/`; blocks `Stop` if spikes aren't folded |
| **Antifragility** | `antifragile` (Post) | Appends test failures to `.harness/lessons.md`; stamps `.harness/last_green_run` on pass; auto-commits the tree after every green test run |
| **Lindy** | `lindy` (Pre) | Rejects edits to files unmodified >1 yr per `git log` |
| **Iatrogenics** | `scope` (Pre) | Rejects writes outside globs declared in `.harness/scope.txt` |
| **Black swan** | `black_swan` (Stop) | Requires `.harness/black_swans.md` with ≥3 enumerated edge cases |
| (shell safety) | `shell_guard` (Pre) | Blocks a list of known-destructive Bash patterns |

All hooks are standalone Python scripts with no dependencies beyond the stdlib. They are small — the longest is ~80 lines. They are tested (see `tests/`).

## What happened to the old SDK version

The first version of this repo was a Python agent loop built on the Anthropic SDK — it had its own tools, its own message loop, its own system prompt. Under Taleb's own rules, that was the wrong shape: a lot of code reimplementing what Claude Code already does. The via-negativa move was to **delete the entire loop** and ride on top of Claude Code, converting the principles into hooks that intercept Claude Code's tool calls. The result is ~7× smaller and harder to argue with.

See commit history for the old SDK-based implementation.

## Why the hook-based shape is correct

The principles should make the wrong move *impossible*, not discouraged. A 15-line cap enforced by a PreToolUse hook that exits 2 is a constraint. A sentence in a system prompt that says "prefer small edits" is a wish. The agent can ignore a wish; it can't ignore a hook.

The demo in the previous SDK version showed this working: the agent tried to write 84 lines in one shot, got rejected, re-reasoned to "declare a spike, validate design, fold back," and produced better code than it would have without the constraint. The hook-based rewrite preserves that property while deleting every piece of infrastructure we wrote to implement it.

## Configuration

- `.harness/scope.txt` — one glob per line, declared target paths for the current task
- `.harness/black_swans.md` — enumerated edge cases; ≥3 bullets required before `Stop`
- `.harness/lindy_overrides.txt` — paths allowed to bypass the Lindy guard, with reasons
- `.harness/addition_budget.json` — `{"budget": N, "spent": M}`; defaults to `{"budget": 300, "spent": 0}`
- `.harness/stress_test.sh` — opt-in script the stressor hook invokes with `PYTHONHASHSEED=random`

All state lives under `.harness/` and is gitignored. It is session-local.

## Tests

```bash
pip install pytest
pytest
```

Tests invoke each hook as a subprocess with fake Claude-Code-style JSON on stdin and check exit codes and messages.

## License

MIT
