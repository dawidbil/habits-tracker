"""Configuration management for habits tracker."""

import os
from pathlib import Path

from dotenv import load_dotenv


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """Get the data directory path."""
    return get_project_root() / "data"


def get_habits_file() -> Path:
    """Get the habits.yaml file path."""
    return get_data_dir() / "habits.yaml"


def get_history_file() -> Path:
    """Get the history.json file path."""
    return get_data_dir() / "history.json"


def get_editor() -> str:
    """Get the configured editor, falling back to environment variable or default."""
    # Load .env file if it exists
    env_file = get_project_root() / ".env"
    if env_file.exists():
        _ = load_dotenv(env_file)

    # Try project .env first, then system EDITOR, then default
    editor = os.getenv("EDITOR")
    if not editor:
        editor = "nano"  # Safe default

    return editor
