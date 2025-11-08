"""Linting and code quality checks."""

import subprocess
import sys

# Define source paths
SRC_PATHS = ["src", "tests", "devtools"]
DOC_PATHS = ["README.md", "CLAUDE.md"]


def run_command(name: str, command: list[str]) -> bool:
    """Run a command and return success status.

    Args:
        name: Name of the tool being run
        command: Command and arguments to execute

    Returns:
        True if command succeeded, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"Running {name}...")
    print(f"{'=' * 60}")

    result = subprocess.run(command, check=False)

    if result.returncode == 0:
        print(f"✓ {name} passed")
        return True
    else:
        print(f"✗ {name} failed")
        return False


def main() -> int:
    """Run all linting tools.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    results = []

    # Run codespell
    results.append(
        run_command(
            "codespell",
            ["codespell", *SRC_PATHS, *DOC_PATHS, "--skip", "uv.lock"],
        )
    )

    # Run ruff check
    results.append(
        run_command(
            "ruff check",
            ["ruff", "check", *SRC_PATHS],
        )
    )

    # Run ruff format
    results.append(
        run_command(
            "ruff format",
            ["ruff", "format", "--check", *SRC_PATHS],
        )
    )

    # Run basedpyright
    results.append(
        run_command(
            "basedpyright",
            ["basedpyright", *SRC_PATHS],
        )
    )

    # Summary
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if all(results):
        print("\n✓ All checks passed!")
        return 0
    else:
        print("\n✗ Some checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
