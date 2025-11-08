"""Tests for habits metadata management."""

from pathlib import Path

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
    habit = {
        "id": "exercise",
        "name": "Exercise",
        "description": "Activity",
        "frequency": "daily",
    }

    assert habits.validate_habit(habit) is True


def test_validate_habit_missing_field():
    """Test validating habit with missing required field."""
    habit = {"id": "exercise", "name": "Exercise", "frequency": "daily"}

    assert habits.validate_habit(habit) is False


def test_validate_habit_empty():
    """Test validating empty habit."""
    habit = {}

    assert habits.validate_habit(habit) is False
