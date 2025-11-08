"""Tests for historical data management."""

import json
from datetime import date

from habits_tracker import tracker


def test_load_history_empty_file(tmp_path):
    """Test loading history from non-existent file."""
    history_file = tmp_path / "history.json"

    result = tracker.load_history(history_file)

    assert result == {"completions": []}


def test_load_history_with_data(tmp_path):
    """Test loading history with existing data."""
    history_file = tmp_path / "history.json"
    data = {
        "completions": [
            {"habit_id": "exercise", "date": "2025-11-07", "completed": True},
            {"habit_id": "meditation", "date": "2025-11-07", "completed": True},
        ]
    }
    history_file.write_text(json.dumps(data))

    result = tracker.load_history(history_file)

    assert len(result["completions"]) == 2
    assert result["completions"][0]["habit_id"] == "exercise"
    assert result["completions"][1]["habit_id"] == "meditation"


def test_save_history(tmp_path):
    """Test saving history to file."""
    history_file = tmp_path / "history.json"
    data: tracker.HistoryData = {
        "completions": [{"habit_id": "exercise", "date": "2025-11-07", "completed": True}]
    }

    tracker.save_history(history_file, data)

    assert history_file.exists()
    with history_file.open() as f:
        saved_data = json.load(f)
    assert saved_data == data


def test_save_history_creates_directory(tmp_path):
    """Test saving history creates parent directory if needed."""
    history_file = tmp_path / "subdir" / "history.json"
    data: tracker.HistoryData = {"completions": []}

    tracker.save_history(history_file, data)

    assert history_file.exists()
    assert history_file.parent.exists()


def test_mark_habits_completed(tmp_path):
    """Test marking habits as completed."""
    history_file = tmp_path / "history.json"
    habit_ids = ["exercise", "meditation"]
    target_date = date(2025, 11, 7)

    tracker.mark_habits_completed(history_file, habit_ids, target_date)

    result = tracker.load_history(history_file)
    assert len(result["completions"]) == 2
    assert result["completions"][0]["habit_id"] == "exercise"
    assert result["completions"][0]["date"] == "2025-11-07"
    assert result["completions"][0]["completed"] is True


def test_mark_habits_replaces_existing(tmp_path):
    """Test marking habits replaces existing entries for same date."""
    history_file = tmp_path / "history.json"
    target_date = date(2025, 11, 7)

    # Mark first set
    tracker.mark_habits_completed(history_file, ["exercise", "meditation"], target_date)

    # Mark different set for same date
    tracker.mark_habits_completed(history_file, ["reading"], target_date)

    result = tracker.load_history(history_file)
    # Should only have the latest marking for this date
    completions_for_date = [c for c in result["completions"] if c["date"] == "2025-11-07"]
    assert len(completions_for_date) == 1
    assert completions_for_date[0]["habit_id"] == "reading"


def test_get_completions_for_date(tmp_path):
    """Test getting completed habits for a specific date."""
    history_file = tmp_path / "history.json"
    data: tracker.HistoryData = {
        "completions": [
            {"habit_id": "exercise", "date": "2025-11-07", "completed": True},
            {"habit_id": "meditation", "date": "2025-11-07", "completed": True},
            {"habit_id": "reading", "date": "2025-11-08", "completed": True},
        ]
    }
    tracker.save_history(history_file, data)

    result = tracker.get_completions_for_date(history_file, date(2025, 11, 7))

    assert result == {"exercise", "meditation"}


def test_get_completions_for_date_no_data(tmp_path):
    """Test getting completions for date with no data."""
    history_file = tmp_path / "history.json"

    result = tracker.get_completions_for_date(history_file, date(2025, 11, 7))

    assert result == set()


def test_export_history(tmp_path):
    """Test exporting history as JSON string."""
    history_file = tmp_path / "history.json"
    data: tracker.HistoryData = {
        "completions": [{"habit_id": "exercise", "date": "2025-11-07", "completed": True}]
    }
    tracker.save_history(history_file, data)

    result = tracker.export_history(history_file)

    # Should be valid JSON
    parsed = json.loads(result)
    assert parsed == data


def test_export_history_empty(tmp_path):
    """Test exporting empty history."""
    history_file = tmp_path / "history.json"

    result = tracker.export_history(history_file)

    parsed = json.loads(result)
    assert parsed == {"completions": []}
