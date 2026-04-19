import json
import time


def test_skin_blocks_when_no_marker(run_hook, tmp_path):
    r = run_hook("skin_in_the_game", {"cwd": str(tmp_path)})
    data = json.loads(r.stdout)
    assert data["decision"] == "block"
    assert "skin in the game" in data["reason"].lower()


def test_skin_passes_with_fresh_marker(run_hook, tmp_path):
    marker = tmp_path / ".harness" / "last_green_run"
    marker.parent.mkdir(parents=True)
    marker.write_text(f"{int(time.time())}\npytest -q\n")
    r = run_hook("skin_in_the_game", {"cwd": str(tmp_path)})
    assert r.returncode == 0
    assert not r.stdout.strip()


def test_skin_blocks_when_stale(run_hook, tmp_path):
    marker = tmp_path / ".harness" / "last_green_run"
    marker.parent.mkdir(parents=True)
    marker.write_text("old\n")
    import os
    old = time.time() - 24 * 3600
    os.utime(marker, (old, old))
    r = run_hook("skin_in_the_game", {"cwd": str(tmp_path)})
    data = json.loads(r.stdout)
    assert data["decision"] == "block"
