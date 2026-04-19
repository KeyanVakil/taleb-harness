def test_scope_passes_if_no_scope_file(run_hook, tmp_path):
    r = run_hook("scope", {
        "tool_name": "Write",
        "tool_input": {
            "file_path": str(tmp_path / "anything.py"),
            "content": "",
        },
        "cwd": str(tmp_path),
    })
    assert r.returncode == 0


def test_scope_allows_in_scope(run_hook, tmp_path):
    scope = tmp_path / ".harness" / "scope.txt"
    scope.parent.mkdir(parents=True)
    scope.write_text("src/*.py\n")
    path = tmp_path / "src" / "foo.py"
    path.parent.mkdir(parents=True)
    r = run_hook("scope", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": ""},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 0


def test_scope_blocks_out_of_scope(run_hook, tmp_path):
    scope = tmp_path / ".harness" / "scope.txt"
    scope.parent.mkdir(parents=True)
    scope.write_text("src/*.py\n")
    path = tmp_path / "other" / "foo.py"
    path.parent.mkdir(parents=True)
    r = run_hook("scope", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": ""},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 2
    assert "scope" in r.stderr.lower()
