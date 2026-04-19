# taleb-harness — instructions for Claude

You are operating inside a harness built on Nassim Nicholas Taleb's principles.
The principles are enforced by Claude Code hooks (`.claude/settings.json`), not
by this prompt. You cannot argue past them. Work with them.

## The principles (and the hooks that enforce them)

1. **Via negativa** — subtract before adding.
   `no_ghosts` rejects any write that adds new `TODO`/`FIXME`/`XXX`/`HACK`
   markers: either complete the addition or complete the deletion, never
   both. `addition_budget` tracks cumulative net lines added per session
   against a default budget of 300; exceeding it requires deleting elsewhere
   or raising the budget in `.harness/addition_budget.json`.
   *Before any meaningful addition, say what you considered deleting and why.*

2. **Skin in the game** — you don't know it works until it has run.
   `skin_in_the_game` (Stop hook) blocks ending until `.harness/last_green_run`
   is present and fresh. Any file edit invalidates it; re-test before ending.
   `stressor` (Stop hook, opt-in via `.harness/stress_test.sh`) re-runs the
   suite with `PYTHONHASHSEED=random` — a test suite that fails under
   reshuffle isn't actually proving much.

3. **Barbell** — safe edits or bold spikes, never medium refactors.
   `barbell` rejects any Write/Edit/MultiEdit whose diff exceeds 15 lines,
   unless the target is under `.harness/spikes/`. `fold_discipline`
   (Stop hook) rejects ending if `.harness/spikes/` is non-empty — fold
   learnings into safe edits, then delete the spike, or explicitly abandon
   it.

4. **Antifragility** — failures are signal.
   `antifragile` (PostToolUse) appends test failures to
   `.harness/lessons.md` and stamps `.harness/last_green_run` on pass.
   When you see a pattern repeat, CHANGE STRATEGY; do not retry harder.

5. **Lindy** — old code has earned its place.
   `lindy` rejects edits to files unmodified for >1 year (per `git log`).
   Soft-warns on >30 days. To override, append the path and a
   justification to `.harness/lindy_overrides.txt`.

6. **Iatrogenics** — do no harm.
   `scope` (optional) reads `.harness/scope.txt` (one glob per line) and
   rejects writes outside the declared target paths. If you genuinely need
   a new file, append it with a `# reason: ...` comment first.

7. **Optionality** — keep options open.
   `auto_commit` (PostToolUse on Bash) snapshots the tree as a git commit
   after every green test run. You cannot lose work; every turn leaves a
   save point.

8. **Black swan** — plan for tails.
   `black_swan` (Stop hook) requires `.harness/black_swans.md` with at
   least three enumerated edge cases (empty input, size extremes,
   unicode, concurrency, partial failure, etc.) and for each one a note
   on how it's handled or why it's out of scope.

## Shell safety

`shell_guard` (PreToolUse on Bash) blocks a known-destructive pattern list:
`rm -rf /`, fork bombs, `mkfs`, `dd`, `git push --force`, `git reset --hard
origin`, etc. Floor, not ceiling — the human operator is the real ceiling.

## Workflow

- State the plan in one sentence before acting.
- If scope matters, write it to `.harness/scope.txt` first.
- For new behavior: write the test, run it, see it fail, then implement.
- Run tests after every change — the Stop hook requires a recent green run.
- Before ending, write `.harness/black_swans.md` and make sure
  `.harness/spikes/` is empty.
- When a hook blocks you, reshape the action. A block is signal, not noise.
