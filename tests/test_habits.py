"""Tests for habits metadata management."""

import pytest

from habits_tracker import habits


def test_load_habits_success(tmp_path):
    """Test loading valid habits from YAML file."""
    habits_file = tmp_path / "habits.yaml"
    habits_file.write_text("""habits:
  - id: exercise
    name: Exercise
    description: 30 minutes of activity
    frequency: daily
  - id: reading
    name: Reading
    description: Read for 20 minutes
    frequency: daily
""")

    result = habits.load_habits(habits_file)

    assert len(result) == 2
    assert result[0]["id"] == "exercise"
    assert result[0]["name"] == "Exercise"
    assert result[0]["description"] == "30 minutes of activity"
    assert result[0]["frequency"] == "daily"
    assert result[1]["id"] == "reading"


def test_load_habits_empty_file(tmp_path):
    """Test loading from empty YAML file."""
    habits_file = tmp_path / "habits.yaml"
    habits_file.write_text("")

    result = habits.load_habits(habits_file)

    assert result == []


def test_load_habits_no_habits_key(tmp_path):
    """Test loading YAML without habits key."""
    habits_file = tmp_path / "habits.yaml"
    habits_file.write_text("other_key: value")

    result = habits.load_habits(habits_file)

    assert result == []


def test_load_habits_file_not_found(tmp_path):
    """Test loading from non-existent file raises error."""
    habits_file = tmp_path / "nonexistent.yaml"

    with pytest.raises(FileNotFoundError, match="Habits file not found"):
        habits.load_habits(habits_file)


def test_validate_habit_valid():
    """Test validating a complete habit."""
    habit: habits.Habit = {
        "id": "exercise",
        "name": "Exercise",
        "description": "Activity",
        "frequency": "daily",
    }

    assert habits.validate_habit(habit) is True


def test_validate_habit_missing_field():
    """Test validating habit with missing required field."""
    # Type ignore needed as we're testing invalid data
    habit: habits.Habit = {"id": "exercise", "name": "Exercise", "frequency": "daily"}  # type: ignore[typeddict-item]

    assert habits.validate_habit(habit) is False


def test_validate_habit_empty():
    """Test validating empty habit."""
    # Type ignore needed as we're testing invalid data
    habit: habits.Habit = {}  # type: ignore[typeddict-item]

    assert habits.validate_habit(habit) is False


def test_is_valid_frequency_daily():
    """Test validating daily frequency."""
    assert habits.is_valid_frequency("daily") is True


def test_is_valid_frequency_every_two_days():
    """Test validating every_two_days frequency."""
    assert habits.is_valid_frequency("every_two_days") is True


def test_is_valid_frequency_weekly_valid():
    """Test validating valid weekly:X frequencies."""
    assert habits.is_valid_frequency("weekly:1") is True
    assert habits.is_valid_frequency("weekly:2") is True
    assert habits.is_valid_frequency("weekly:3") is True
    assert habits.is_valid_frequency("weekly:4") is True
    assert habits.is_valid_frequency("weekly:5") is True
    assert habits.is_valid_frequency("weekly:6") is True


def test_is_valid_frequency_weekly_invalid():
    """Test rejecting invalid weekly frequencies."""
    assert habits.is_valid_frequency("weekly:0") is False
    assert habits.is_valid_frequency("weekly:7") is False
    assert habits.is_valid_frequency("weekly:10") is False
    assert habits.is_valid_frequency("weekly:-1") is False


def test_is_valid_frequency_invalid_format():
    """Test rejecting invalid frequency formats."""
    assert habits.is_valid_frequency("invalid") is False
    assert habits.is_valid_frequency("weekly") is False
    assert habits.is_valid_frequency("weekly:") is False
    assert habits.is_valid_frequency("weekly:abc") is False
    assert habits.is_valid_frequency("") is False
    assert habits.is_valid_frequency("3x_week") is False


def test_validate_habit_with_invalid_frequency():
    """Test validate_habit rejects habits with invalid frequency."""
    habit: habits.Habit = {
        "id": "exercise",
        "name": "Exercise",
        "description": "Activity",
        "frequency": "invalid_frequency",
    }

    assert habits.validate_habit(habit) is False


def test_validate_habit_with_valid_daily_frequency():
    """Test validate_habit accepts habits with daily frequency."""
    habit: habits.Habit = {
        "id": "exercise",
        "name": "Exercise",
        "description": "Activity",
        "frequency": "daily",
    }

    assert habits.validate_habit(habit) is True


def test_validate_habit_with_valid_weekly_frequency():
    """Test validate_habit accepts habits with weekly:X frequency."""
    habit: habits.Habit = {
        "id": "gym",
        "name": "Gym",
        "description": "Go to gym",
        "frequency": "weekly:3",
    }

    assert habits.validate_habit(habit) is True
