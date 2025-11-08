# Habits Tracker

A simple CLI tool for tracking daily habits using YAML metadata and JSON history storage.

## Project Overview

Habits Tracker is a command-line tool that helps you track your daily habits. Define your habits in a YAML file, mark them as completed through an interactive editor interface, and export the data for API consumption.

## Features

- **YAML-based habit definitions**: Easy-to-edit metadata for your habits
- **Interactive marking**: Use your preferred editor to mark completed habits
- **Historical tracking**: JSON-based storage of completion history
- **API-friendly**: Export command for easy integration with other tools
- **Flexible scheduling**: Support for various habit frequencies

## Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone the repository
cd /home/astro/habits-tracker

# Install dependencies
make install

# Initialize with template files
uv run habits init
```

### Configuration

Copy `.env.template` to `.env` and customize:

```bash
cp .env.template .env
```

Set your preferred editor (optional):

```bash
EDITOR=vim
```

Falls back to `$EDITOR` environment variable, then to `nano` as default.

## Usage

### Initialize

Create template files (habits.yaml and history.json):

```bash
habits init
```

### Mark Habits

Mark habits for today:

```bash
habits mark today
```

Mark habits for yesterday:

```bash
habits mark yesterday
```

This opens your configured editor with a list of habits. Add an 'x' or any character in the brackets to mark as completed:

```
# Mark completed habits for 2025-11-08
# Add 'x' or any character before the habit ID to mark as done
# Lines without a mark will be considered not completed

[x] exercise: Exercise
[ ] meditation: Meditation
[x] reading: Reading
```

### Export for API

Export history as JSON to stdout:

```bash
habits export
```

This outputs the complete history.json content, which can be consumed by your API:

```bash
# Example API integration
curl http://localhost:8000/api/habits -d "$(habits export)"
```

### Get Help

Show detailed help about file structure:

```bash
habits help
```

## File Structure

```
habits-tracker/
├── data/
│   ├── habits.yaml      # Your habit definitions (edit this!)
│   └── history.json     # Completion history (auto-generated, gitignored)
├── src/habits_tracker/  # Source code
├── tests/               # Test suite
└── devtools/            # Development tools
```

### habits.yaml Format

```yaml
habits:
  - id: exercise
    name: Exercise
    description: 30 minutes of physical activity
    frequency: daily
  - id: meditation
    name: Meditation
    description: 10 minutes of mindfulness
    frequency: daily
```

### history.json Format

```json
{
  "completions": [
    {"habit_id": "exercise", "date": "2025-11-07", "completed": true},
    {"habit_id": "meditation", "date": "2025-11-07", "completed": true}
  ]
}
```

## Development

### Install Development Dependencies

```bash
make install
```

### Run Linting

```bash
make lint
```

### Run Tests

```bash
make test
```

### Code Quality Tools

- **ruff**: Linting and formatting
- **basedpyright**: Type checking
- **codespell**: Spell checking
- **pytest**: Testing framework

### Build Package

```bash
make build
```

## Architecture

- **Click**: CLI framework for command handling
- **PyYAML**: YAML parsing for habit metadata
- **Rich**: Terminal formatting and output
- **python-dotenv**: Configuration management

The tool follows a clean separation:
- `config.py`: Configuration and path management
- `habits.py`: YAML loading and validation
- `tracker.py`: JSON history management
- `main.py`: CLI interface and user interaction

## API Integration

The `habits export` command is designed for API consumption. Your API can call this command and capture the JSON output:

```python
# Example Python API integration
import subprocess
import json

def get_habits_data():
    result = subprocess.run(['habits', 'export'], capture_output=True, text=True)
    return json.loads(result.stdout)
```

## License

MIT
