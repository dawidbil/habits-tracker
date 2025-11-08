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
            "[red]Error:[/red] habits.yaml not found. Run 'habits init' first.",
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

    all_habits = valid_habits

    # Get already completed habits for this date
    history_file = config.get_history_file()
    completed = tracker.get_completions_for_date(history_file, target_date)

    # Create temp file with habit list
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        temp_path = Path(tf.name)
        tf.write(f"# Mark completed habits for {target_date}\n")
        tf.write("# Add 'x' or any character before the habit ID to mark as done\n")
        tf.write("# Lines without a mark will be considered not completed\n\n")

        for habit in all_habits:
            mark_char = "x" if habit["id"] in completed else " "
            tf.write(f"[{mark_char}] {habit['id']}: {habit['name']}\n")

    # Open editor
    editor = config.get_editor()
    try:
        subprocess.run([editor, str(temp_path)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        console.print(f"[red]Error:[/red] Failed to open editor '{editor}': {e}")
        temp_path.unlink()
        sys.exit(1)

    # Parse results
    completed_ids = []
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
def init() -> None:
    """Initialize habits tracker with template files."""
    data_dir = config.get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    habits_file = config.get_habits_file()
    history_file = config.get_history_file()

    # Create habits.yaml template if it doesn't exist
    if not habits_file.exists():
        template = """habits:
  - id: exercise
    name: Exercise
    description: 30 minutes of physical activity
    frequency: daily
  - id: meditation
    name: Meditation
    description: 10 minutes of mindfulness
    frequency: daily
  - id: reading
    name: Reading
    description: Read for 20 minutes
    frequency: daily
"""
        habits_file.write_text(template)
        console.print(f"[green]✓[/green] Created {habits_file}")
    else:
        console.print(f"[yellow]→[/yellow] {habits_file} already exists")

    # Create empty history.json if it doesn't exist
    if not history_file.exists():
        tracker.save_history(history_file, {"completions": []})
        console.print(f"[green]✓[/green] Created {history_file}")
    else:
        console.print(f"[yellow]→[/yellow] {history_file} already exists")

    console.print("\n[green]Habits tracker initialized![/green]")
    console.print("Edit data/habits.yaml to customize your habits.")


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
      frequency: daily       # How often (daily, 3x_week, etc.)
""")

    console.print("[bold cyan]Commands:[/bold cyan]")
    console.print("  habits init              - Initialize with template files")
    console.print("  habits mark today        - Mark today's completed habits")
    console.print("  habits mark yesterday    - Mark yesterday's habits")
    console.print("  habits export            - Export history as JSON (for API)")
    console.print("  habits help              - Show this help\n")

    console.print("[bold cyan]Configuration:[/bold cyan]")
    console.print("  Set EDITOR in .env file or use system $EDITOR variable")
    console.print("  Default editor: nano\n")


if __name__ == "__main__":
    cli()
