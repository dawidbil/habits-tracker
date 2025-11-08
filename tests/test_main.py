"""Tests for CLI commands."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from habits_tracker import main, tracker


@pytest.fixture
def runner():
    """Fixture for Click CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """Fixture to mock config paths to use temp directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    def mock_get_data_dir():
        return data_dir

    def mock_get_habits_file():
        return data_dir / "habits.yaml"

    def mock_get_history_file():
        return data_dir / "history.json"

    def mock_get_editor():
        return "nano"

    monkeypatch.setattr("habits_tracker.config.get_data_dir", mock_get_data_dir)
    monkeypatch.setattr("habits_tracker.config.get_habits_file", mock_get_habits_file)
    monkeypatch.setattr("habits_tracker.config.get_history_file", mock_get_history_file)
    monkeypatch.setattr("habits_tracker.config.get_editor", mock_get_editor)

    return data_dir


def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(main.cli, ["--version"])

    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(main.cli, ["--help"])

    assert result.exit_code == 0
    assert "Habits Tracker" in result.output
    assert "Commands:" in result.output


def test_init_command(runner, mock_config):
    """Test init command creates template files."""
    result = runner.invoke(main.cli, ["init"])

    assert result.exit_code == 0
    assert "initialized" in result.output.lower()
    assert (mock_config / "habits.yaml").exists()
    assert (mock_config / "history.json").exists()


def test_init_command_existing_files(runner, mock_config):
    """Test init command with existing files."""
    # Create files first
    runner.invoke(main.cli, ["init"])

    # Run init again
    result = runner.invoke(main.cli, ["init"])

    assert result.exit_code == 0
    assert "already exists" in result.output


def test_export_command_empty(runner, mock_config):
    """Test export command with no data."""
    result = runner.invoke(main.cli, ["export"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    # New format: empty dict when no habits defined
    assert data == {}


def test_export_command_with_data(runner, mock_config):
    """Test export command with existing data."""
    # Create a habits file
    habits_file = mock_config / "habits.yaml"
    habits_file.write_text("""habits:
  - id: exercise
    name: Exercise
    description: Workout
    frequency: daily
""")

    history_file = mock_config / "history.json"
    test_data: tracker.HistoryData = {
        "completions": [{"habit_id": "exercise", "date": "2025-11-07", "completed": True}]
    }
    tracker.save_history(history_file, test_data)

    result = runner.invoke(main.cli, ["export"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    # New format: dict with habit IDs as keys
    assert "exercise" in data
    assert data["exercise"]["name"] == "Exercise"
    assert data["exercise"]["frequency"] == "daily"
    assert len(data["exercise"]["history"]) > 0


def test_help_command(runner):
    """Test help command shows file structure info."""
    result = runner.invoke(main.cli, ["help"])

    assert result.exit_code == 0
    assert "File Structure" in result.output
    assert "habits.yaml" in result.output
    assert "history.json" in result.output


@patch("subprocess.run")
def test_mark_today_command(mock_subprocess, runner, mock_config):
    """Test mark today command."""
    # Create habits file
    habits_file = mock_config / "habits.yaml"
    habits_file.write_text("""habits:
  - id: exercise
    name: Exercise
    description: Activity
    frequency: daily
""")

    # Mock editor to mark the habit
    def mock_editor(args, **kwargs):
        temp_file = Path(args[1])
        # Read current content
        content = temp_file.read_text()
        # Mark the habit as done
        content = content.replace("[ ] exercise", "[x] exercise")
        temp_file.write_text(content)
        return MagicMock(returncode=0)

    mock_subprocess.side_effect = mock_editor

    result = runner.invoke(main.cli, ["mark", "today"])

    assert result.exit_code == 0
    assert "Marked" in result.output

    # Verify history was updated
    history_file = mock_config / "history.json"
    history = tracker.load_history(history_file)
    assert len(history["completions"]) > 0


@patch("subprocess.run")
def test_mark_yesterday_command(mock_subprocess, runner, mock_config):
    """Test mark yesterday command."""
    # Create habits file
    habits_file = mock_config / "habits.yaml"
    habits_file.write_text("""habits:
  - id: exercise
    name: Exercise
    description: Activity
    frequency: daily
""")

    # Mock editor (no changes, no habits marked)
    mock_subprocess.return_value = MagicMock(returncode=0)

    result = runner.invoke(main.cli, ["mark", "yesterday"])

    assert result.exit_code == 0


def test_mark_no_habits_file(runner, mock_config):
    """Test mark command with no habits file."""
    result = runner.invoke(main.cli, ["mark", "today"])

    assert result.exit_code == 1
    assert "not found" in result.output.lower()


def test_mark_empty_habits(runner, mock_config):
    """Test mark command with empty habits."""
    habits_file = mock_config / "habits.yaml"
    habits_file.write_text("habits: []")

    result = runner.invoke(main.cli, ["mark", "today"])

    assert result.exit_code == 1
    assert "no habits" in result.output.lower()


@patch("subprocess.run")
def test_mark_editor_failure(mock_subprocess, runner, mock_config):
    """Test mark command when editor fails."""
    habits_file = mock_config / "habits.yaml"
    habits_file.write_text("""habits:
  - id: exercise
    name: Exercise
    description: Activity
    frequency: daily
""")

    mock_subprocess.side_effect = FileNotFoundError("Editor not found")

    result = runner.invoke(main.cli, ["mark", "today"])

    assert result.exit_code == 1
    assert "error" in result.output.lower()
