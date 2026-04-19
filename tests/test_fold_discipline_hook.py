import json


def test_fold_discipline_passes_when_no_spikes(run_hook, tmp_path):
    r = run_hook("fold_discipline", {"cwd": str(tmp_path)})
    assert r.returncode == 0
    assert not r.stdout.strip()


def test_fold_discipline_blocks_when_spikes_present(run_hook, tmp_path):
    spike = tmp_path / ".harness" / "spikes" / "experiment.py"
    spike.parent.mkdir(parents=True)
    spike.write_text("junk\n")
    r = run_hook("fold_discipline", {"cwd": str(tmp_path)})
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["decision"] == "block"
    assert "spike" in data["reason"].lower()


def test_fold_discipline_respects_active_flag(run_hook, tmp_path):
    spike = tmp_path / ".harness" / "spikes" / "experiment.py"
    spike.parent.mkdir(parents=True)
    spike.write_text("junk\n")
    r = run_hook("fold_discipline", {
        "cwd": str(tmp_path),
        "stop_hook_active": True,
    })
    assert r.returncode == 0
    assert not r.stdout.strip()
