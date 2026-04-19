from pathlib import Path

import pytest

from harness.guards import (
    GuardRejection,
    check_barbell,
    check_shell,
    diff_line_count,
)


def test_diff_count_append_one_line():
    before = "a\nb\nc\n"
    after = "a\nb\nc\nd\n"
    assert diff_line_count(before, after) == 1


def test_diff_count_replace_is_two():
    before = "a\nb\nc\n"
    after = "a\nBEE\nc\n"
    assert diff_line_count(before, after) == 2


def test_barbell_allows_small_edits():
    before = "x\n" * 10
    after = before + "y\n"
    check_barbell(Path("foo.py"), before, after, spike_active=False)


def test_barbell_rejects_large_non_spike():
    before = ""
    after = "\n".join(f"line {i}" for i in range(100))
    with pytest.raises(GuardRejection):
        check_barbell(Path("foo.py"), before, after, spike_active=False)


def test_barbell_allows_large_under_declared_spike():
    before = ""
    after = "\n".join(f"line {i}" for i in range(100))
    check_barbell(Path("foo.py"), before, after, spike_active=True)


def test_barbell_allows_large_in_spike_dir():
    before = ""
    after = "\n".join(f"line {i}" for i in range(100))
    check_barbell(
        Path(".harness/spikes/experiment.py"),
        before,
        after,
        spike_active=False,
    )


def test_shell_blocks_rm_rf():
    with pytest.raises(GuardRejection):
        check_shell("rm -rf /")


def test_shell_blocks_force_push():
    with pytest.raises(GuardRejection):
        check_shell("git push --force origin main")


def test_shell_allows_pytest():
    check_shell("pytest -q")


def test_shell_allows_python_script():
    check_shell("python -c 'print(42)'")
