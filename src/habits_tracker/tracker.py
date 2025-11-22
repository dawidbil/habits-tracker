"""Historical data management for habit tracking."""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Literal, NotRequired, TypedDict, cast


class Completion(TypedDict):
    """Type definition for a habit completion record."""

    habit_id: str
    date: str
    completed: bool


class HistoryData(TypedDict):
    """Type definition for the history.json structure."""

    completions: list[Completion]


# Status types for habit completion
Status = Literal["completed", "not completed", "failed"]


class DayStatus(TypedDict):
    """Type definition for a single day's status."""

    date: str
    status: Status


class HabitExport(TypedDict):
    """Type definition for a habit in export format."""

    name: str
    description: str
    frequency: str
    start_date: str
    end_date: NotRequired[str]
    history: list[DayStatus]


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
        raw_data = json.load(f)

    data = cast(HistoryData, raw_data)
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


def compute_habit_status(
    habit_id: str,
    frequency: str,
    target_date: date,
    all_completions: list[Completion],
) -> Status:
    """Compute the status of a habit for a specific date.

    Args:
        habit_id: ID of the habit
        frequency: Frequency type (daily, every_two_days, weekly:X)
        target_date: Date to compute status for
        all_completions: List of all completion records

    Returns:
        Status: "completed", "not completed", or "failed"
    """
    # Get completions for this habit
    habit_completions = [c for c in all_completions if c["habit_id"] == habit_id and c["completed"]]

    # Convert date strings to date objects and sort
    completion_dates = sorted([date.fromisoformat(c["date"]) for c in habit_completions])

    # Check if completed on target date
    is_completed = target_date in completion_dates
    if is_completed:
        return "completed"

    # Daily frequency: not completed = failed
    if frequency == "daily":
        return "failed"

    # Every two days frequency
    if frequency == "every_two_days":
        # Check if yesterday was completed
        yesterday = target_date - timedelta(days=1)
        yesterday_completed = yesterday in completion_dates

        if yesterday_completed:
            # Last completion was yesterday, so today is day 1 without
            return "not completed"

        # Yesterday was not completed. Check if yesterday is the very first day
        # in the entire tracking system (before any completions for any habit)
        if all_completions:
            earliest_completion = min(date.fromisoformat(c["date"]) for c in all_completions)
            if yesterday < earliest_completion:
                # Yesterday was before tracking started, so today is day 1
                return "not completed"
        else:
            # No completions at all in the system, this is day 1
            return "not completed"

        # Yesterday was also not completed (and was being tracked), so this is day 2+ = failed
        return "failed"

    # Weekly:X frequency
    if frequency.startswith("weekly:"):
        try:
            required_count = int(frequency.split(":")[1])
        except (ValueError, IndexError):
            return "failed"

        # Get the week boundaries (Monday to Sunday)
        # weekday() returns 0 for Monday, 6 for Sunday
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)

        # Count completions in this week
        week_completions = [d for d in completion_dates if week_start <= d <= week_end]
        completion_count = len(week_completions)

        if completion_count >= required_count:
            return "not completed"
        else:
            return "failed"

    # Unknown frequency
    return "failed"


def export_history(
    history_file: Path,
    habits_file: Path,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Export history combined with metadata as JSON string.

    Args:
        history_file: Path to the history.json file
        habits_file: Path to the habits.yaml file
        start_date: Optional start date in yyyy-mm-dd format
        end_date: Optional end date in yyyy-mm-dd format

    Returns:
        JSON string with format: {habit_id: {name, description, frequency, history}}
    """
    from habits_tracker import habits as habits_module

    # Load habits metadata
    try:
        all_habits = habits_module.load_habits(habits_file)
    except FileNotFoundError:
        all_habits = []

    # Load history
    history = load_history(history_file)
    completions = history["completions"]

    # Determine default date range from completions
    if completions:
        completion_dates = [date.fromisoformat(c["date"]) for c in completions]
        earliest_completion = min(completion_dates)
        latest_completion = date.today()
    else:
        earliest_completion = date.today()
        latest_completion = date.today()

    # Parse user-provided filter dates
    filter_start = date.fromisoformat(start_date) if start_date else earliest_completion
    filter_end = date.fromisoformat(end_date) if end_date else latest_completion

    # Build export data
    export_data: dict[str, HabitExport] = {}

    for habit in all_habits:
        habit_id = habit["id"]
        habit_name = habit["name"]
        habit_desc = habit["description"]
        habit_freq = habit["frequency"]
        habit_start_str = habit["start_date"]
        habit_end_str = habit.get("end_date")

        # Parse habit's active period
        habit_start = date.fromisoformat(habit_start_str)
        habit_end = date.fromisoformat(habit_end_str) if habit_end_str else date.today()

        # Compute intersection of habit's active period and user's filter range
        range_start = max(habit_start, filter_start)
        range_end = min(habit_end, filter_end)

        # Generate history for each day in range
        day_statuses: list[DayStatus] = []
        current_date = range_start

        # Only generate history if the date range is valid
        while current_date <= range_end:
            status = compute_habit_status(
                habit_id,
                habit_freq,
                current_date,
                completions,
            )

            day_statuses.append(
                {
                    "date": current_date.isoformat(),
                    "status": status,
                }
            )

            current_date += timedelta(days=1)

        # Build export entry
        export_entry: HabitExport = {
            "name": habit_name,
            "description": habit_desc,
            "frequency": habit_freq,
            "start_date": habit_start_str,
            "history": day_statuses,
        }

        # Add end_date if present
        if habit_end_str:
            export_entry["end_date"] = habit_end_str

        export_data[habit_id] = export_entry

    return json.dumps(export_data, indent=2)
