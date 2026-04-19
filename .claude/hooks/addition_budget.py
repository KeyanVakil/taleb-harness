#!/usr/bin/env python3
"""Addition budget: cap net lines added per session.
State: .harness/addition_budget.json = {"budget": N, "spent": M}."""
import json
from pathlib import Path
from _lib import before_after, fail, read_payload

DEFAULT_BUDGET = 300
STATE = ".harness/addition_budget.json"


def main() -> None:
    payload = read_payload()
    ba = before_after(payload)
    if ba is None:
        return
    before, after, path = ba
    if ".harness/" in str(path).replace("\\", "/"):
        return  # harness metadata is exempt
    cwd = Path(payload.get("cwd", "."))
    state_path = cwd / STATE
    state = (
        json.loads(state_path.read_text(encoding="utf-8"))
        if state_path.exists() else {"budget": DEFAULT_BUDGET, "spent": 0}
    )
    delta = len(after.splitlines()) - len(before.splitlines())
    new_spent = state.get("spent", 0) + delta
    budget = state.get("budget", DEFAULT_BUDGET)
    if new_spent > budget:
        fail(
            f"Via negativa budget exceeded: {new_spent} net lines added "
            f"(budget {budget}). Delete elsewhere to refund, or raise the "
            f"budget in {STATE}."
        )
    state["spent"] = new_spent
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state), encoding="utf-8")


if __name__ == "__main__":
    main()
