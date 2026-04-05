"""CLI helpers for launching the Streamlit app."""

from __future__ import annotations

import argparse
import subprocess
import sys

from echo_run.backend import (
    build_sanity_report,
    get_data_dir,
    get_notebooks,
    get_notebooks_dir,
    streamlit_is_available,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Echo Lab Protocol Generator CLI")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run a backend sanity check without starting the Streamlit UI",
    )
    parser.add_argument(
        "--list-notebooks",
        action="store_true",
        help="Print the available notebook names and exit",
    )
    return parser


def run_sanity_check() -> int:
    """Run a backend-only smoke check and print a concise report."""
    report = build_sanity_report()
    print("Echo backend sanity check")
    print(f"notebook dir: {get_notebooks_dir()}")
    print(f"data dir: {get_data_dir()}")
    print(f"notebooks: {len(report.notebooks)}")
    print(f"data files: {len(report.data_files)}")
    print(f"default notebook: {report.selected_notebook}")
    print(f"streamlit installed: {'yes' if report.streamlit_available else 'no'}")
    print(f"example experiment: {report.config_values['experiment_name']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the Streamlit app through the installed console script."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_notebooks:
        for notebook in get_notebooks():
            print(notebook)
        return 0

    if args.check:
        return run_sanity_check()

    if not streamlit_is_available():
        print(
            "Streamlit is not installed. Create a virtual environment and run "
            "`pip install -e .` before starting the UI.",
            file=sys.stderr,
        )
        return 1

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.address",
        "0.0.0.0",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
