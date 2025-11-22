# CLAUDE.md

This file provides guidance to Claude Code when working with the habits-tracker project.

## Project Overview

**Type:** Python CLI tool for habit tracking
**Location:** `/home/astro/habits-tracker`
**Python Version:** 3.12+
**Package Manager:** uv

## Description

A command-line tool for tracking daily habits with YAML-based metadata and JSON historical data. Users mark habits through an interactive editor interface, and data can be exported for API consumption.

## Architecture

### Core Components

1. **config.py** - Configuration and path management
   - Determines project paths (habits.yaml, history.json)
   - Manages editor configuration from .env
   - Falls back to $EDITOR or nano

2. **habits.py** - YAML metadata loading
   - Loads and validates habits from habits.yaml
   - Type-checked with TypedDict
   - Schema: id, name, description, frequency, start_date, end_date (optional)

3. **tracker.py** - Historical data management
   - Manages history.json (completions tracking)
   - Supports marking habits for specific dates
   - Export functionality for API integration

4. **main.py** - CLI interface (Click framework)
   - `habits edit` - Edit habits.yaml in configured editor (creates file if needed)
   - `habits mark [today|yesterday]` - Interactive marking
   - `habits export` - JSON export to stdout
   - `habits help` - File structure documentation

### Data Flow

1. User defines habits in `data/habits.yaml` (via `habits edit` command)
2. User runs `habits mark today/yesterday`
3. CLI filters habits to show only those active on the target date (based on start_date/end_date)
4. CLI opens editor with habit checklist
5. User marks completed habits with 'x'
6. CLI parses selections and updates `data/history.json`
7. API calls `habits export` to retrieve JSON data (respecting habit date ranges)

### File Structure

```
habits-tracker/
├── src/habits_tracker/     # Source code
│   ├── __init__.py        # Package metadata
│   ├── main.py            # CLI entry point
│   ├── config.py          # Configuration
│   ├── habits.py          # YAML loading
│   └── tracker.py         # History management
├── data/
│   ├── habits.yaml        # User's habit definitions
│   └── history.json       # Completion history (gitignored)
├── tests/                 # Pytest tests
├── devtools/
│   └── lint.py           # Linting script
├── pyproject.toml        # Project config
├── Makefile              # Dev commands
└── .env                  # Local config (gitignored)
```

## Configuration

### Environment Variables

- `EDITOR` - Text editor for marking habits (default: nano)
- Configured in `.env` file (created from `.env.template`)

### Data Files

**habits.yaml** - User-editable habit metadata:
```yaml
habits:
  - id: unique_id
    name: Display Name
    description: What the habit involves
    frequency: daily  # daily, every_two_days, weekly:1-6
    start_date: "2025-11-01"  # When habit tracking begins (required)
    end_date: "2025-12-31"  # When habit tracking ends (optional)
```

**history.json** - Auto-generated completion tracking:
```json
{
  "completions": [
    {"habit_id": "exercise", "date": "2025-11-07", "completed": true}
  ]
}
```

## Development Commands

```bash
# Install dependencies
make install

# Run linting (ruff, basedpyright, codespell)
make lint

# Run tests
make test

# Upgrade dependencies
make upgrade

# Build package
make build

# Clean artifacts
make clean

# Run CLI
make run
```

## Code Quality

### Tools Used

- **ruff**: Linting and formatting (configured in pyproject.toml)
- **basedpyright**: Type checking (Python 3.12)
- **codespell**: Spell checking
- **pytest**: Testing framework

### Type Checking

- All functions have type hints
- TypedDict used for structured data (Habit, Completion, etc.)
- basedpyright runs in standard mode

### Code Style

- Line length: 100 characters
- Quote style: double quotes
- Import sorting: enabled (ruff)
- Target: Python 3.12

## API Integration

The `habits export` command is designed for API consumption:

```bash
# API can call this command and capture JSON output
habits export

# Export with optional date filters
habits export --start 2025-11-01 --end 2025-11-30
```

**Output Format:**
```json
{
  "habit_id": {
    "name": "Habit Name",
    "description": "Habit description",
    "frequency": "daily",
    "start_date": "2025-11-01",
    "end_date": "2025-12-31",  # Optional field
    "history": [
      {"date": "2025-11-07", "status": "completed"},
      {"date": "2025-11-08", "status": "failed"}
    ]
  }
}
```

**Date Filtering Behavior:**
- Export respects habit's `start_date` and `end_date` (if present)
- User-provided `--start` and `--end` filters intersect with habit dates
- History only includes dates within habit's active period
- If habit has `end_date`, export stops at that date
- If no `end_date`, export continues through today

**Use case:** API running on same host calls this command via subprocess to retrieve habit data

## Dependencies

### Production

- **click** (>=8.1.0) - CLI framework
- **pyyaml** (>=6.0) - YAML parsing
- **rich** (>=13.0.0) - Terminal formatting
- **python-dotenv** (>=1.0.0) - Config management

### Development

- pytest (>=8.3.0)
- ruff (>=0.11.0)
- codespell (>=2.4.0)
- basedpyright (>=1.28.0)

## Git Workflow

- **Tracked:** Source code, pyproject.toml, uv.lock, templates
- **Gitignored:** data/history.json, .env, .venv/, __pycache__/

## Key Design Decisions

1. **Editor-based marking**: Flexible UX, works with any text editor
2. **YAML for metadata**: Human-readable, easy to edit manually
3. **JSON for history**: Machine-readable, API-friendly
4. **CLI export command**: Clean interface between tool and API
5. **Single JSON file**: Simple, no database overhead
6. **src/ layout**: Proper Python package structure
7. **uv for deps**: Modern, fast Python package management

## Common Tasks

### Adding a New Habit

Run `habits edit` to open the editor, then add:
```yaml
- id: new_habit
  name: New Habit
  description: What it involves
  frequency: daily
  start_date: "2025-11-22"  # Date when tracking begins
  # end_date: "2025-12-31"  # Optional: when to stop tracking
```

### Modifying CLI Commands

Edit `src/habits_tracker/main.py` - all Click commands defined there

### Changing Data Storage

Modify `src/habits_tracker/tracker.py` - contains all history.json logic

### Testing the Export

```bash
habits export | jq  # Pretty-print JSON output
```

## Reference Implementations

This project follows patterns from `/home/astro/marcus-bot`:
- Modern pyproject.toml structure
- uv dependency management
- devtools/lint.py pattern
- Makefile commands
- Type checking with basedpyright
