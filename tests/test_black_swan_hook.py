import json


def test_black_swan_blocks_when_missing(run_hook, tmp_path):
    r = run_hook("black_swan", {"cwd": str(tmp_path)})
    data = json.loads(r.stdout)
    assert data["decision"] == "block"
    assert "black swan" in data["reason"].lower()


def test_black_swan_blocks_when_too_few_items(run_hook, tmp_path):
    p = tmp_path / ".harness" / "black_swans.md"
    p.parent.mkdir(parents=True)
    p.write_text("- empty input\n- huge input\n")  # only 2
    r = run_hook("black_swan", {"cwd": str(tmp_path)})
    data = json.loads(r.stdout)
    assert data["decision"] == "block"


def test_black_swan_passes_with_enough(run_hook, tmp_path):
    p = tmp_path / ".harness" / "black_swans.md"
    p.parent.mkdir(parents=True)
    p.write_text(
        "- empty input: returns []\n"
        "- huge input: streams\n"
        "- unicode: covered by test\n"
    )
    r = run_hook("black_swan", {"cwd": str(tmp_path)})
    assert r.returncode == 0
    assert not r.stdout.strip()
