import json


def test_budget_allows_under_limit(run_hook, tmp_path):
    path = tmp_path / "foo.py"
    r = run_hook("addition_budget", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "x\n" * 10},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 0


def test_budget_blocks_over_limit(run_hook, tmp_path):
    path = tmp_path / "foo.py"
    state = tmp_path / ".harness" / "addition_budget.json"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"budget": 300, "spent": 295}))
    r = run_hook("addition_budget", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "x\n" * 10},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 2
    assert "budget" in r.stderr.lower()


def test_budget_ignores_harness_paths(run_hook, tmp_path):
    path = tmp_path / ".harness" / "scratch.md"
    r = run_hook("addition_budget", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "x\n" * 1000},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 0
