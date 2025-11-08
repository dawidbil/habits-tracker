"""Tests for configuration management."""

import os
from pathlib import Path

from habits_tracker import config


def test_get_project_root():
    """Test getting project root directory."""
    root = config.get_project_root()
    assert root.is_dir()
    assert (root / "pyproject.toml").exists()


def test_get_data_dir():
    """Test getting data directory path."""
    data_dir = config.get_data_dir()
    assert data_dir == config.get_project_root() / "data"


def test_get_habits_file():
    """Test getting habits.yaml file path."""
    habits_file = config.get_habits_file()
    assert habits_file == config.get_data_dir() / "habits.yaml"
    assert habits_file.name == "habits.yaml"


def test_get_history_file():
    """Test getting history.json file path."""
    history_file = config.get_history_file()
    assert history_file == config.get_data_dir() / "history.json"
    assert history_file.name == "history.json"


def test_get_editor_default(monkeypatch):
    """Test editor falls back to nano when not configured."""
    # Clear environment variables
    monkeypatch.delenv("EDITOR", raising=False)

    editor = config.get_editor()
    assert editor == "nano"


def test_get_editor_from_env(monkeypatch, tmp_path):
    """Test editor from environment variable."""
    monkeypatch.setenv("EDITOR", "vim")

    editor = config.get_editor()
    assert editor == "vim"
