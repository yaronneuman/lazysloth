#!/usr/bin/env python3
"""
Test runner script for FastParrot.

This script provides convenient ways to run tests with different configurations.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def run_tests(test_type=None, verbose=False, coverage=False, markers=None):
    """Run tests with specified options."""
    project_root = Path(__file__).parent.parent

    # Base pytest command
    cmd_parts = ["python", "-m", "pytest"]

    # Add test paths
    if test_type == "unit":
        cmd_parts.append("tests/unit")
    elif test_type == "integration":
        cmd_parts.append("tests/integration")
    elif test_type:
        cmd_parts.append(f"tests/{test_type}")
    else:
        cmd_parts.append("tests")

    # Add options
    if verbose:
        cmd_parts.append("-v")

    if coverage:
        cmd_parts.extend(["--cov=lazysloth", "--cov-report=term-missing"])

    if markers:
        for marker in markers:
            cmd_parts.extend(["-m", marker])

    # Join command
    cmd = " ".join(cmd_parts)
    print(f"Running: {cmd}")

    success, stdout, stderr = run_command(cmd, cwd=project_root)

    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)

    return success


def install_test_deps():
    """Install test dependencies."""
    cmd = "pip install -e .[test]"
    print(f"Installing test dependencies: {cmd}")

    success, stdout, stderr = run_command(cmd)

    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)

    return success


def lint_code():
    """Run code linting."""
    commands = [
        "python -m flake8 lazysloth tests --max-line-length=100 --ignore=E501,W503",
        "python -m black --check lazysloth tests",
        "python -m isort --check-only lazysloth tests",
    ]

    all_passed = True
    for cmd in commands:
        print(f"Running: {cmd}")
        success, stdout, stderr = run_command(cmd)

        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        if not success:
            all_passed = False

    return all_passed


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="FastParrot Test Runner")

    parser.add_argument(
        "command",
        choices=["test", "install-deps", "lint", "all"],
        help="Command to run",
    )

    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage reporting"
    )

    parser.add_argument(
        "-m", "--markers", nargs="*", help="Run tests with specific markers"
    )

    args = parser.parse_args()

    if args.command == "install-deps":
        success = install_test_deps()
    elif args.command == "lint":
        success = lint_code()
    elif args.command == "test":
        success = run_tests(
            test_type=args.type if args.type != "all" else None,
            verbose=args.verbose,
            coverage=args.coverage,
            markers=args.markers,
        )
    elif args.command == "all":
        print("=== Installing dependencies ===")
        success = install_test_deps()

        if success:
            print("\n=== Running linter ===")
            success = lint_code()

        if success:
            print("\n=== Running tests ===")
            success = run_tests(
                test_type=args.type if args.type != "all" else None,
                verbose=args.verbose,
                coverage=True,  # Always use coverage for "all" command
                markers=args.markers,
            )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
