# taleb-harness

A coding-agent harness that treats Nassim Nicholas Taleb's principles as **architecture**, not vibes.

Most agent harnesses put "be careful" in the system prompt and hope. This one puts the rules in the runtime. When the model tries to violate a principle, the harness rejects the action and the failure feeds back into the next turn.

## The principles, as code

| Principle | Encoding |
|---|---|
| **Via negativa** — subtract, don't add | The agent must call `consider_deletion` before non-trivial additions. Net line delta is surfaced on every write. |
| **Skin in the game** | Writes are followed by `run_shell`. No `finish` is allowed without running the code. |
| **Barbell** | Writes are either SAFE (≤15 lines diff) or SPIKE (under `.harness/spikes/`, declared first). The "medium refactor" is mechanically rejected. |
| **Antifragility** | Every failure is recorded to `.harness/lessons.md` and reinjected into the prompt. Repeated failures trigger a forced strategy change. |
| **Lindy** | System prompt biases toward stdlib and established libraries. |
| **Iatrogenics** | System prompt forbids drive-by refactors. |
| **Optionality** | Commit-frequently guidance. Each turn aims to leave the tree runnable. |

The `harness/principles.py` file is the source of truth — prompt + constants in one place. Guards in `harness/guards.py` enforce what the prompt asks for.

## Install

```bash
pip install -e .
export ANTHROPIC_API_KEY=sk-...
```

## Use

```bash
harness "add a function `median` to stats.py and a test for it"
```

The agent will, roughly:

1. Consider whether the task can be solved by deletion (`consider_deletion`).
2. Write a failing test first.
3. Make a safe (≤15 line) edit.
4. Run the test (`run_shell`).
5. On failure, record a lesson and try again — with a forced strategy change if the same failure repeats.
6. `finish` only after seeing the test pass.

## Why this shape

Taleb's project is about *how systems learn from error*. A coding agent that cannot feel pain from its own bugs is a forecasting machine pretending to build software. This harness makes the agent bear the consequences of what it writes, prefer deletion, avoid the middle ground, and treat every failure as signal rather than noise to retry through.

The barbell in particular is the interesting constraint: "just do a 100-line refactor" is the shape of most agent failures. Disallowing it mechanically — either split into many tiny safe steps, or declare a throwaway spike — forces a cleaner decomposition.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
