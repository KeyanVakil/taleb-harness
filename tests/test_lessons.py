from harness.lessons import LessonsLog


def test_record_and_summary(tmp_path):
    log = LessonsLog(tmp_path / "lessons.md")
    log.record("test_failed", "assertion in test_foo")
    log.record("import_error", "no module named bar")
    summary = log.recent_summary()
    assert "test_failed" in summary
    assert "import_error" in summary
    assert (tmp_path / "lessons.md").read_text().count("\n") == 2


def test_is_repeating_fires_at_threshold(tmp_path):
    log = LessonsLog(tmp_path / "lessons.md")
    for _ in range(3):
        log.record("test_failed", "same thing")
    repeating, kind = log.is_repeating(threshold=3)
    assert repeating
    assert kind == "test_failed"


def test_is_not_repeating_under_threshold(tmp_path):
    log = LessonsLog(tmp_path / "lessons.md")
    log.record("test_failed", "x")
    log.record("type_error", "y")
    repeating, _ = log.is_repeating(threshold=3)
    assert not repeating


def test_detail_is_truncated(tmp_path):
    log = LessonsLog(tmp_path / "lessons.md")
    long = "x" * 1000
    lesson = log.record("big", long)
    assert len(lesson.detail) <= 300


def test_empty_summary(tmp_path):
    log = LessonsLog(tmp_path / "lessons.md")
    assert "no lessons" in log.recent_summary()
