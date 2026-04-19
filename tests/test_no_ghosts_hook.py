def test_no_ghosts_rejects_new_todo(run_hook, tmp_path):
    path = tmp_path / "foo.py"
    r = run_hook("no_ghosts", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "# TODO: fix later\n"},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 2
    assert "No ghosts" in r.stderr


def test_no_ghosts_rejects_new_fixme(run_hook, tmp_path):
    path = tmp_path / "foo.py"
    r = run_hook("no_ghosts", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "x = 1  # FIXME broken\n"},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 2


def test_no_ghosts_allows_clean_write(run_hook, tmp_path):
    path = tmp_path / "foo.py"
    r = run_hook("no_ghosts", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "print('hi')\n"},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 0


def test_no_ghosts_tolerates_preexisting(run_hook, tmp_path):
    path = tmp_path / "foo.py"
    path.write_text("# TODO: existing\nold = 1\n")
    r = run_hook("no_ghosts", {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(path),
            "old_string": "old = 1",
            "new_string": "new = 2",
        },
        "cwd": str(tmp_path),
    })
    assert r.returncode == 0
