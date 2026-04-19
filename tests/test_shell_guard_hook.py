def test_shell_guard_allows_pytest(run_hook):
    r = run_hook("shell_guard", {
        "tool_name": "Bash",
        "tool_input": {"command": "pytest -q"},
    })
    assert r.returncode == 0


def test_shell_guard_blocks_rm_rf_root(run_hook):
    r = run_hook("shell_guard", {
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /"},
    })
    assert r.returncode == 2
    assert "destructive" in r.stderr.lower()


def test_shell_guard_blocks_force_push(run_hook):
    r = run_hook("shell_guard", {
        "tool_name": "Bash",
        "tool_input": {"command": "git push --force origin main"},
    })
    assert r.returncode == 2
