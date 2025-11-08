"""Historical data management for habit tracking."""

import json
from datetime import date
from pathlib import Path
from typing import TypedDict


class Completion(TypedDict):
    """Type definition for a habit completion record."""

    habit_id: str
    date: str
    completed: bool


class HistoryData(TypedDict):
    """Type definition for the history.json structure."""

    completions: list[Completion]


def load_history(history_file: Path) -> HistoryData:
    """Load history from JSON file.

    Args:
        history_file: Path to the history.json file

    Returns:
        History data dictionary
    """
    if not history_file.exists():
        return {"completions": []}

    with history_file.open() as f:
        data: HistoryData = json.load(f)

    return data


def save_history(history_file: Path, history: HistoryData) -> None:
    """Save history to JSON file.

    Args:
        history_file: Path to the history.json file
        history: History data to save
    """
    # Ensure parent directory exists
    history_file.parent.mkdir(parents=True, exist_ok=True)

    with history_file.open("w") as f:
        json.dump(history, f, indent=2)


def mark_habits_completed(history_file: Path, habit_ids: list[str], target_date: date) -> None:
    """Mark habits as completed for a given date.

    Args:
        history_file: Path to the history.json file
        habit_ids: List of habit IDs to mark as completed
        target_date: Date for which to mark habits
    """
    history = load_history(history_file)
    date_str = target_date.isoformat()

    # Remove existing entries for this date (we'll replace them)
    history["completions"] = [c for c in history["completions"] if c["date"] != date_str]

    # Add new completion records
    for habit_id in habit_ids:
        history["completions"].append({"habit_id": habit_id, "date": date_str, "completed": True})

    save_history(history_file, history)


def get_completions_for_date(history_file: Path, target_date: date) -> set[str]:
    """Get completed habit IDs for a specific date.

    Args:
        history_file: Path to the history.json file
        target_date: Date to query

    Returns:
        Set of habit IDs completed on that date
    """
    history = load_history(history_file)
    date_str = target_date.isoformat()

    return {
        c["habit_id"] for c in history["completions"] if c["date"] == date_str and c["completed"]
    }


def export_history(history_file: Path) -> str:
    """Export history as JSON string.

    Args:
        history_file: Path to the history.json file

    Returns:
        JSON string of history data
    """
    history = load_history(history_file)
    return json.dumps(history, indent=2)
