"""CLI helpers for launching the Streamlit app."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from echo_run.backend import (
    build_sanity_report,
    get_data_dir,
    get_notebooks,
    get_notebooks_dir,
    streamlit_is_available,
)
from echo_run.preprocessing import (
    PLATE_MODE_NEW,
    PLATE_MODE_PREMADE,
    PreprocessingRequest,
    parse_samples,
    run_echo_protocol_preprocessing,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Echo Protocol CLI")
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
    parser.add_argument(
        "--run-preprocessing",
        action="store_true",
        help="Run the fixed preprocessing workflow without launching the Streamlit UI",
    )
    parser.add_argument(
        "--plate-mode",
        choices=[PLATE_MODE_PREMADE, PLATE_MODE_NEW],
        default=PLATE_MODE_PREMADE,
        help="Choose whether the preprocessing run starts from a premade plate or a new plate",
    )
    parser.add_argument(
        "--premade-plate",
        default=None,
        help="Fixture source plate CSV to use when running in premade plate mode",
    )
    parser.add_argument(
        "--new-plate-label",
        default=None,
        help="Label to use when running the new plate workflow",
    )
    parser.add_argument("--experiment-name", default="cli_run", help="Experiment name for generated outputs")
    parser.add_argument("--doses", type=int, default=6, help="Number of doses in the main curve")
    parser.add_argument("--doses2", type=int, default=3, help="Number of doses in the second curve")
    parser.add_argument("--highest-dose", type=float, default=4.0, help="Highest dose in micromolar")
    parser.add_argument("--vol-cellextract", type=int, default=2000, help="Cell extract volume in nL")
    parser.add_argument("--vol-antigen", type=int, default=2000, help="Antigen volume in nL")
    parser.add_argument(
        "--samples",
        default="sample1,sample2,sample3",
        help="Comma-separated sample names",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory for preprocessing artifacts",
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


def run_preprocessing_from_cli(args: argparse.Namespace) -> int:
    """Run the fixed preprocessing workflow using CLI-supplied parameters."""
    request = PreprocessingRequest(
        experiment_name=args.experiment_name,
        plate_mode=args.plate_mode,
        premade_plate_name=args.premade_plate,
        new_plate_label=args.new_plate_label,
        doses=args.doses,
        doses2=args.doses2,
        highest_dose=args.highest_dose,
        vol_cellextract=args.vol_cellextract,
        vol_antigen=args.vol_antigen,
        samples=parse_samples(args.samples),
    )
    result = run_echo_protocol_preprocessing(
        request,
        output_dir=Path(args.output_dir) if args.output_dir else None,
    )

    print(f"workflow: {result.workflow_name}")
    print(f"execution mode: {result.execution_mode}")
    print(f"output dir: {result.output_dir}")
    if result.protocol_csv:
        print(f"protocol csv: {result.protocol_csv}")
    if result.source_plate_csv:
        print(f"source plate csv: {result.source_plate_csv}")
    if result.destination_composition_csv:
        print(f"destination composition csv: {result.destination_composition_csv}")
    print(f"run manifest: {result.run_manifest_json}")
    if result.notebook_output_path:
        print(f"executed notebook: {result.notebook_output_path}")
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

    if args.run_preprocessing:
        return run_preprocessing_from_cli(args)

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
