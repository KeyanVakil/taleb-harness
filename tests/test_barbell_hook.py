def test_barbell_allows_small_write(run_hook, tmp_path):
    path = tmp_path / "foo.py"
    r = run_hook("barbell", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": "a\nb\nc\n"},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 0


def test_barbell_rejects_large_write(run_hook, tmp_path):
    path = tmp_path / "foo.py"
    content = "\n".join(f"line {i}" for i in range(50))
    r = run_hook("barbell", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": content},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 2
    assert "Barbell violation" in r.stderr


def test_barbell_allows_large_under_spike(run_hook, tmp_path):
    spike = tmp_path / ".harness" / "spikes" / "foo.py"
    spike.parent.mkdir(parents=True)
    content = "\n".join(f"line {i}" for i in range(50))
    r = run_hook("barbell", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(spike), "content": content},
        "cwd": str(tmp_path),
    })
    assert r.returncode == 0


def test_barbell_small_edit_passes(run_hook, tmp_path):
    path = tmp_path / "foo.py"
    path.write_text("hello\nworld\n")
    r = run_hook("barbell", {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(path),
            "old_string": "hello",
            "new_string": "goodbye",
        },
        "cwd": str(tmp_path),
    })
    assert r.returncode == 0
