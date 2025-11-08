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


def test_export_history_old_format(tmp_path):
    """Test old export_history tests are now updated - this is a placeholder."""
    # These tests have been replaced by new export tests below
    pass


def test_compute_habit_status_daily_completed():
    """Test daily habit status when completed."""
    completions: list[tracker.Completion] = [
        {"habit_id": "exercise", "date": "2025-11-07", "completed": True}
    ]

    status = tracker.compute_habit_status("exercise", "daily", date(2025, 11, 7), completions)

    assert status == "completed"


def test_compute_habit_status_daily_failed():
    """Test daily habit status when not completed."""
    completions: list[tracker.Completion] = [
        {"habit_id": "exercise", "date": "2025-11-07", "completed": True}
    ]

    status = tracker.compute_habit_status("exercise", "daily", date(2025, 11, 8), completions)

    assert status == "failed"


def test_compute_habit_status_every_two_days_completed():
    """Test every_two_days habit when completed."""
    completions: list[tracker.Completion] = [
        {"habit_id": "gym", "date": "2025-11-07", "completed": True}
    ]

    status = tracker.compute_habit_status("gym", "every_two_days", date(2025, 11, 7), completions)

    assert status == "completed"


def test_compute_habit_status_every_two_days_not_completed():
    """Test every_two_days habit on day 1 without completion."""
    completions: list[tracker.Completion] = [
        {"habit_id": "gym", "date": "2025-11-07", "completed": True}
    ]

    status = tracker.compute_habit_status("gym", "every_two_days", date(2025, 11, 8), completions)

    assert status == "not completed"


def test_compute_habit_status_every_two_days_failed():
    """Test every_two_days habit on day 2+ without completion."""
    completions: list[tracker.Completion] = [
        {"habit_id": "gym", "date": "2025-11-07", "completed": True}
    ]

    status = tracker.compute_habit_status("gym", "every_two_days", date(2025, 11, 9), completions)

    assert status == "failed"


def test_compute_habit_status_every_two_days_no_previous():
    """Test every_two_days habit with no previous completions."""
    completions: list[tracker.Completion] = []
    
    status = tracker.compute_habit_status("gym", "every_two_days", date(2025, 11, 7), completions)
    
    assert status == "not completed"


def test_compute_habit_status_every_two_days_consecutive_failures():
    """Test every_two_days habit with consecutive days not completed."""
    # Some previous activity so we know tracking has started
    completions: list[tracker.Completion] = [
        {"habit_id": "other", "date": "2025-11-05", "completed": True}
    ]
    
    # Nov 7: first day without completion
    status_day1 = tracker.compute_habit_status("meditation", "every_two_days", date(2025, 11, 7), completions)
    assert status_day1 == "failed"  # Yesterday (Nov 6) also not completed
    
    # Nov 8: second day without completion
    status_day2 = tracker.compute_habit_status("meditation", "every_two_days", date(2025, 11, 8), completions)
    assert status_day2 == "failed"  # Yesterday (Nov 7) also not completed


def test_compute_habit_status_weekly_completed():
    """Test weekly habit when completed on that day."""
    completions: list[tracker.Completion] = [
        {"habit_id": "run", "date": "2025-11-10", "completed": True}  # Monday
    ]

    status = tracker.compute_habit_status("run", "weekly:3", date(2025, 11, 10), completions)

    assert status == "completed"


def test_compute_habit_status_weekly_not_completed_quota_met():
    """Test weekly habit not completed but quota met for the week."""
    # Week of Nov 10-16 (Mon-Sun)
    completions: list[tracker.Completion] = [
        {"habit_id": "run", "date": "2025-11-10", "completed": True},  # Monday
        {"habit_id": "run", "date": "2025-11-12", "completed": True},  # Wednesday
        {"habit_id": "run", "date": "2025-11-14", "completed": True},  # Friday
    ]

    # Tuesday - not completed but quota of 3 is met
    status = tracker.compute_habit_status("run", "weekly:3", date(2025, 11, 11), completions)

    assert status == "not completed"


def test_compute_habit_status_weekly_failed_quota_not_met():
    """Test weekly habit when quota not met for the week."""
    # Week of Nov 10-16 (Mon-Sun)
    completions: list[tracker.Completion] = [
        {"habit_id": "run", "date": "2025-11-10", "completed": True},  # Monday
    ]

    # Tuesday - not completed and quota of 3 is not met
    status = tracker.compute_habit_status("run", "weekly:3", date(2025, 11, 11), completions)

    assert status == "failed"


def test_compute_habit_status_weekly_across_weeks():
    """Test weekly habit considers only the target week."""
    # Different weeks
    completions: list[tracker.Completion] = [
        {"habit_id": "run", "date": "2025-11-03", "completed": True},  # Previous week
        {"habit_id": "run", "date": "2025-11-10", "completed": True},  # Current week Monday
    ]

    # Nov 11 (Tuesday) in week Nov 10-16, only 1 completion this week
    status = tracker.compute_habit_status("run", "weekly:2", date(2025, 11, 11), completions)

    assert status == "failed"


def test_compute_habit_status_weekly_quota_exceeded():
    """Test weekly habit when quota is exceeded."""
    # Week of Nov 10-16 (Mon-Sun)
    completions: list[tracker.Completion] = [
        {"habit_id": "run", "date": "2025-11-10", "completed": True},
        {"habit_id": "run", "date": "2025-11-11", "completed": True},
        {"habit_id": "run", "date": "2025-11-12", "completed": True},
        {"habit_id": "run", "date": "2025-11-13", "completed": True},
    ]

    # Friday - not completed but quota of 2 is exceeded
    status = tracker.compute_habit_status("run", "weekly:2", date(2025, 11, 14), completions)

    assert status == "not completed"


def test_export_history_basic(tmp_path):
    """Test basic export with habits and history."""
    # Create habits file
    habits_file = tmp_path / "habits.yaml"
    habits_file.write_text("""habits:
  - id: exercise
    name: Exercise
    description: 30 minutes
    frequency: daily
""")

    # Create history file
    history_file = tmp_path / "history.json"
    history_data: tracker.HistoryData = {
        "completions": [
            {"habit_id": "exercise", "date": "2025-11-07", "completed": True},
        ]
    }
    tracker.save_history(history_file, history_data)

    # Export with date range
    result = tracker.export_history(history_file, habits_file, "2025-11-07", "2025-11-08")

    parsed = json.loads(result)

    # Check structure
    assert "exercise" in parsed
    assert parsed["exercise"]["name"] == "Exercise"
    assert parsed["exercise"]["description"] == "30 minutes"
    assert parsed["exercise"]["frequency"] == "daily"
    assert len(parsed["exercise"]["history"]) == 2

    # Check day statuses
    assert parsed["exercise"]["history"][0]["date"] == "2025-11-07"
    assert parsed["exercise"]["history"][0]["status"] == "completed"
    assert parsed["exercise"]["history"][1]["date"] == "2025-11-08"
    assert parsed["exercise"]["history"][1]["status"] == "failed"


def test_export_history_with_date_filter(tmp_path):
    """Test export respects date filtering."""
    # Create habits file
    habits_file = tmp_path / "habits.yaml"
    habits_file.write_text("""habits:
  - id: reading
    name: Reading
    description: 20 minutes
    frequency: daily
""")

    # Create history with multiple dates
    history_file = tmp_path / "history.json"
    history_data: tracker.HistoryData = {
        "completions": [
            {"habit_id": "reading", "date": "2025-11-01", "completed": True},
            {"habit_id": "reading", "date": "2025-11-05", "completed": True},
            {"habit_id": "reading", "date": "2025-11-10", "completed": True},
        ]
    }
    tracker.save_history(history_file, history_data)

    # Export with limited date range
    result = tracker.export_history(history_file, habits_file, "2025-11-05", "2025-11-07")

    parsed = json.loads(result)

    # Should only have 3 days (Nov 5, 6, 7)
    assert len(parsed["reading"]["history"]) == 3
    assert parsed["reading"]["history"][0]["date"] == "2025-11-05"
    assert parsed["reading"]["history"][0]["status"] == "completed"
    assert parsed["reading"]["history"][1]["date"] == "2025-11-06"
    assert parsed["reading"]["history"][1]["status"] == "failed"
    assert parsed["reading"]["history"][2]["date"] == "2025-11-07"
    assert parsed["reading"]["history"][2]["status"] == "failed"


def test_export_history_multiple_habits(tmp_path):
    """Test export with multiple habits."""
    # Create habits file with multiple habits
    habits_file = tmp_path / "habits.yaml"
    habits_file.write_text("""habits:
  - id: exercise
    name: Exercise
    description: Workout
    frequency: daily
  - id: meditation
    name: Meditation
    description: Mindfulness
    frequency: every_two_days
""")

    # Create history
    history_file = tmp_path / "history.json"
    history_data: tracker.HistoryData = {
        "completions": [
            {"habit_id": "exercise", "date": "2025-11-07", "completed": True},
            {"habit_id": "meditation", "date": "2025-11-07", "completed": True},
        ]
    }
    tracker.save_history(history_file, history_data)

    # Export
    result = tracker.export_history(history_file, habits_file, "2025-11-07", "2025-11-08")

    parsed = json.loads(result)

    # Check both habits are present
    assert "exercise" in parsed
    assert "meditation" in parsed

    # Check exercise (daily) - day 2 should be failed
    assert parsed["exercise"]["history"][1]["status"] == "failed"

    # Check meditation (every_two_days) - day 2 should be not completed
    assert parsed["meditation"]["history"][1]["status"] == "not completed"


def test_export_history_weekly_habit(tmp_path):
    """Test export with weekly habit."""
    # Create habits file
    habits_file = tmp_path / "habits.yaml"
    habits_file.write_text("""habits:
  - id: gym
    name: Gym
    description: Strength training
    frequency: weekly:3
""")

    # Create history - completed 3 times in week Nov 10-16
    history_file = tmp_path / "history.json"
    history_data: tracker.HistoryData = {
        "completions": [
            {"habit_id": "gym", "date": "2025-11-10", "completed": True},  # Mon
            {"habit_id": "gym", "date": "2025-11-12", "completed": True},  # Wed
            {"habit_id": "gym", "date": "2025-11-14", "completed": True},  # Fri
        ]
    }
    tracker.save_history(history_file, history_data)

    # Export the week
    result = tracker.export_history(history_file, habits_file, "2025-11-10", "2025-11-16")

    parsed = json.loads(result)
    history = parsed["gym"]["history"]

    # Check completed days
    assert history[0]["status"] == "completed"  # Mon
    assert history[2]["status"] == "completed"  # Wed
    assert history[4]["status"] == "completed"  # Fri

    # Check non-completed days (quota met, so not completed)
    assert history[1]["status"] == "not completed"  # Tue
    assert history[3]["status"] == "not completed"  # Thu
    assert history[5]["status"] == "not completed"  # Sat
    assert history[6]["status"] == "not completed"  # Sun


def test_export_history_no_habits(tmp_path):
    """Test export with no habits defined."""
    # Create empty habits file
    habits_file = tmp_path / "habits.yaml"
    habits_file.write_text("habits: []\n")

    # Create history
    history_file = tmp_path / "history.json"
    tracker.save_history(history_file, {"completions": []})

    # Export
    result = tracker.export_history(history_file, habits_file)

    parsed = json.loads(result)

    # Should be empty dict
    assert parsed == {}


def test_export_history_no_history(tmp_path):
    """Test export with habits but no history."""
    # Create habits file
    habits_file = tmp_path / "habits.yaml"
    habits_file.write_text("""habits:
  - id: running
    name: Running
    description: Morning run
    frequency: daily
""")

    # No history file
    history_file = tmp_path / "history.json"

    # Export
    result = tracker.export_history(history_file, habits_file)

    parsed = json.loads(result)

    # Should have the habit but with today's date and failed status
    assert "running" in parsed
    assert len(parsed["running"]["history"]) == 1
    assert parsed["running"]["history"][0]["status"] == "failed"
