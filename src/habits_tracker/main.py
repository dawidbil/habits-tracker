"""Main CLI entry point for habits tracker."""

import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import click
from rich.console import Console

from habits_tracker import config, habits, tracker

console = Console()


@click.group()
@click.version_option()
def cli() -> None:
    """Habits Tracker - Track your daily habits with ease."""
    pass


@cli.command()
@click.argument("when", type=click.Choice(["today", "yesterday"]))
def mark(when: str) -> None:
    """Mark habits as completed for today or yesterday.

    Opens your configured editor with a list of habits to mark.
    """
    # Determine target date
    target_date = date.today()
    if when == "yesterday":
        target_date = target_date - timedelta(days=1)

    # Load habits
    habits_file = config.get_habits_file()
    try:
        all_habits = habits.load_habits(habits_file)
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] habits.yaml not found. Run 'habits edit' to create it.",
            style="red",
        )
        sys.exit(1)

    if not all_habits:
        console.print("[yellow]Warning:[/yellow] No habits defined in habits.yaml")
        sys.exit(1)

    # Validate all habits
    valid_habits: list[habits.Habit] = []
    for habit in all_habits:
        if habits.validate_habit(habit):
            valid_habits.append(habit)
        else:
            habit_id = habit.get("id", "unknown")
            freq = habit.get("frequency", "missing")
            msg = (
                f"[yellow]Warning:[/yellow] Invalid habit '{habit_id}' "
                + f"(frequency: '{freq}'). Skipping."
            )
            console.print(msg)

    if not valid_habits:
        console.print("[red]Error:[/red] No valid habits found")
        sys.exit(1)

    # Filter habits to only include those active on the target date
    active_habits: list[habits.Habit] = []
    for habit in valid_habits:
        habit_start = date.fromisoformat(habit["start_date"])
        habit_end_str = habit.get("end_date")
        habit_end = date.fromisoformat(habit_end_str) if habit_end_str else None

        # Habit is active if: start_date <= target_date AND (no end_date OR target_date <= end_date)
        is_active = habit_start <= target_date and (habit_end is None or target_date <= habit_end)

        if is_active:
            active_habits.append(habit)

    if not active_habits:
        msg = (
            f"[yellow]Warning:[/yellow] No habits are active on {target_date}. "
            + "Check start_date and end_date in habits.yaml"
        )
        console.print(msg)
        sys.exit(1)

    all_habits = active_habits

    # Get already completed habits for this date
    history_file = config.get_history_file()
    completed = tracker.get_completions_for_date(history_file, target_date)

    # Create temp file with habit list
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        temp_path = Path(tf.name)
        _ = tf.write(f"# Mark completed habits for {target_date}\n")
        _ = tf.write("# Add 'x' or any character before the habit ID to mark as done\n")
        _ = tf.write("# Lines without a mark will be considered not completed\n\n")

        for habit in all_habits:
            mark_char = "x" if habit["id"] in completed else " "
            _ = tf.write(f"[{mark_char}] {habit['id']}: {habit['name']}\n")

    # Open editor
    editor = config.get_editor()
    try:
        _ = subprocess.run([editor, str(temp_path)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        console.print(f"[red]Error:[/red] Failed to open editor '{editor}': {e}")
        temp_path.unlink()
        sys.exit(1)

    # Parse results
    completed_ids: list[str] = []
    with temp_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if line starts with [x] or [X] or any non-space character
            if line.startswith("[") and len(line) > 2 and line[1] not in (" ", "]"):
                # Extract habit ID (between ] and :)
                try:
                    habit_id = line.split("]")[1].split(":")[0].strip()
                    completed_ids.append(habit_id)
                except IndexError:
                    continue

    # Clean up temp file
    temp_path.unlink()

    # Save to history
    tracker.mark_habits_completed(history_file, completed_ids, target_date)

    console.print(f"[green]✓[/green] Marked {len(completed_ids)} habits for {target_date}")


@cli.command()
@click.option("--start", help="Start date (yyyy-mm-dd)")
@click.option("--end", help="End date (yyyy-mm-dd)")
def export(start: str | None, end: str | None) -> None:
    """Export history data as JSON to stdout.

    This command is intended for API consumption.
    Optionally filter by start and end dates.
    """
    history_file = config.get_history_file()
    habits_file = config.get_habits_file()
    output = tracker.export_history(history_file, habits_file, start, end)
    print(output)


@cli.command()
def edit() -> None:
    """Open habits.yaml in your configured editor.

    Creates the file with a commented template if it doesn't exist.
    """
    data_dir = config.get_data_dir()
    habits_file = config.get_habits_file()

    # Create file with template if it doesn't exist
    if not habits_file.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        template = """# Habits Tracker Configuration
# Define your habits below following this structure

habits:
  # Example habit - customize or replace this
  - id: exercise              # Unique identifier (used in history tracking)
    name: Exercise            # Display name shown in the marking interface
    description: 30 minutes of physical activity  # What this habit involves
    frequency: daily          # How often this habit should be completed
    start_date: "2025-11-22"  # Date when this habit tracking begins (yyyy-mm-dd)
    # end_date: "2025-12-31"  # Optional: date when this habit tracking ends

# Valid frequency values:
# - daily: Must be completed every day
# - every_two_days: Must be completed at least once every 2 days
# - weekly:1 through weekly:6: Must be completed X times per week (Monday-Sunday)
#
# Required fields: id, name, description, frequency, start_date
# Optional fields: end_date (omit for ongoing habits)
# The 'id' must be unique and will be used to track completion history
# Dates must be in yyyy-mm-dd format
"""
        _ = habits_file.write_text(template)
        console.print(f"[green]✓[/green] Created {habits_file}")

    # Open editor
    editor = config.get_editor()
    try:
        _ = subprocess.run([editor, str(habits_file)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        console.print(f"[red]Error:[/red] Failed to open editor '{editor}': {e}")
        sys.exit(1)

    console.print(f"[green]✓[/green] Editor closed. Changes saved to {habits_file.name}")


@cli.command()
def help_cmd() -> None:
    """Show detailed help about file structure and usage."""
    console.print("\n[bold]Habits Tracker - File Structure & Usage[/bold]\n")

    console.print("[bold cyan]File Structure:[/bold cyan]")
    console.print("  data/habits.yaml    - Define your habits metadata")
    console.print("  data/history.json   - Historical completion data (auto-generated)\n")

    console.print("[bold cyan]habits.yaml Format:[/bold cyan]")
    console.print("""
  habits:
    - id: unique_id          # Short identifier
      name: Display Name     # Human-readable name
      description: Details   # What the habit involves
      frequency: daily       # How often (daily, every_two_days, weekly:X)
      start_date: "2025-11-22"  # When tracking begins (yyyy-mm-dd)
      # end_date: "2025-12-31"  # Optional: when tracking ends
""")

    console.print("[bold cyan]Commands:[/bold cyan]")
    console.print("  habits edit              - Edit habits.yaml in your configured editor")
    console.print("  habits mark today        - Mark today's completed habits")
    console.print("  habits mark yesterday    - Mark yesterday's habits")
    console.print("  habits export            - Export history as JSON (for API)")
    console.print("  habits help              - Show this help\n")

    console.print("[bold cyan]Configuration:[/bold cyan]")
    console.print("  Set EDITOR in .env file or use system $EDITOR variable")
    console.print("  Default editor: nano\n")


if __name__ == "__main__":
    cli()
