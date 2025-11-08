"""Habits metadata management."""

from pathlib import Path
from typing import Literal, TypedDict

import yaml


class Habit(TypedDict):
    """Type definition for a habit."""

    id: str
    name: str
    description: str
    frequency: str


class HabitsData(TypedDict):
    """Type definition for the habits YAML structure."""

    habits: list[Habit]


# Valid frequency types
FrequencyType = Literal[
    "daily",
    "every_two_days",
    "weekly:1",
    "weekly:2",
    "weekly:3",
    "weekly:4",
    "weekly:5",
    "weekly:6",
]


def is_valid_frequency(frequency: str) -> bool:
    """Check if a frequency string is valid.

    Args:
        frequency: Frequency string to validate

    Returns:
        True if valid, False otherwise
    """
    if frequency in ("daily", "every_two_days"):
        return True

    # Check weekly:X format
    if frequency.startswith("weekly:"):
        try:
            count = int(frequency.split(":")[1])
            return 1 <= count <= 6
        except (ValueError, IndexError):
            return False

    return False


def load_habits(habits_file: Path) -> list[Habit]:
    """Load habits from YAML file.

    Args:
        habits_file: Path to the habits.yaml file

    Returns:
        List of habit dictionaries

    Raises:
        FileNotFoundError: If habits file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if not habits_file.exists():
        msg = f"Habits file not found: {habits_file}"
        raise FileNotFoundError(msg)

    with habits_file.open() as f:
        data: HabitsData = yaml.safe_load(f)

    if not data or "habits" not in data:
        return []

    return data["habits"]


def validate_habit(habit: Habit) -> bool:
    """Validate that a habit has all required fields and valid frequency.

    Args:
        habit: Habit dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["id", "name", "description", "frequency"]
    if not all(field in habit for field in required_fields):
        return False

    # Validate frequency format
    return is_valid_frequency(habit["frequency"])
