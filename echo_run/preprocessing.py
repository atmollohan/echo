"""Generic preprocessing workflow runner for Echo Protocol."""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from echo_run.backend import PROJECT_ROOT, load_echo_protocol

WORKFLOW_NAME = "echo-protocol-preprocessing"
PLATE_MODE_PREMADE = "Use a premade plate"
PLATE_MODE_NEW = "Create a new plate from scratch"
PLATE_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class PreprocessingRequest:
    """Normalized form inputs for the preprocessing workflow."""

    experiment_name: str
    plate_mode: str
    premade_plate_name: str | None
    new_plate_label: str | None
    doses: int
    doses2: int
    highest_dose: float
    vol_cellextract: int
    vol_antigen: int
    samples: list[str]


@dataclass(frozen=True)
class PreprocessingResult:
    """Materialized output paths from a preprocessing run."""

    workflow_name: str
    execution_mode: str
    output_dir: Path
    protocol_csv: Path | None
    source_plate_csv: Path | None
    destination_composition_csv: Path | None
    run_manifest_json: Path
    notebook_output_path: Path | None


def get_output_dir() -> Path:
    """Return the configured output directory for generated artifacts."""
    return Path(os.environ.get("ECHO_OUTPUT_DIR", PROJECT_ROOT / "generated"))


def get_workflow_notebook_path() -> Path | None:
    """Return the optional custom preprocessing notebook path, if configured."""
    raw_path = os.environ.get("ECHO_WORKFLOW_NOTEBOOK")
    if not raw_path:
        return None
    notebook_path = Path(raw_path)
    if not notebook_path.is_absolute():
        notebook_path = PROJECT_ROOT / notebook_path
    return notebook_path


def parse_samples(raw_samples: str) -> list[str]:
    """Convert comma-separated sample input into a clean list."""
    return [sample.strip() for sample in raw_samples.split(",") if sample.strip()]


def slugify_name(raw_name: str) -> str:
    """Build a filesystem-friendly slug."""
    lowered = raw_name.strip().lower()
    slug = PLATE_SLUG_PATTERN.sub("-", lowered).strip("-")
    return slug or "echo-protocol-run"


def build_fixture_pair(premade_plate_name: str) -> tuple[Path, Path]:
    """Map a committed source plate CSV to its matching committed protocol CSV."""
    source_plate_path = PROJECT_ROOT / "data" / "raw" / premade_plate_name
    if not source_plate_path.exists():
        raise FileNotFoundError(f"Premade plate fixture not found: {premade_plate_name}")

    protocol_name = re.sub(
        r"_source_plate([A-Za-z0-9]+)\.csv$",
        r"_echo_protocol_plate\1.csv",
        premade_plate_name,
    )
    protocol_path = source_plate_path.with_name(protocol_name)
    if not protocol_path.exists():
        raise FileNotFoundError(f"Matching protocol fixture not found for {premade_plate_name}")

    return source_plate_path, protocol_path


def build_destination_composition_table(protocol_df: pd.DataFrame) -> pd.DataFrame:
    """Flatten protocol composition into a CSV that is easy to inspect later."""
    grouped = (
        protocol_df.groupby(["Destination Well", "Sample Name", "Source Well"], as_index=False)
        .agg(total_volume_nl=("Transfer Volume", "sum"))
    )

    rows: list[dict[str, object]] = []
    for destination_well, destination_df in grouped.groupby("Destination Well"):
        ordered = destination_df.sort_values(["total_volume_nl", "Sample Name"], ascending=[False, True])
        composition = " | ".join(
            f"{sample}@{source}: {volume:,} nL"
            for sample, source, volume in ordered[["Sample Name", "Source Well", "total_volume_nl"]].itertuples(index=False, name=None)
        )
        rows.append(
            {
                "Destination Well": destination_well,
                "Component Count": int(len(ordered)),
                "Total Transfer Volume (nL)": int(ordered["total_volume_nl"].sum()),
                "Composition": composition,
            }
        )

    return pd.DataFrame(rows).sort_values("Destination Well").reset_index(drop=True)


def write_run_manifest(output_dir: Path, request: PreprocessingRequest, execution_mode: str) -> Path:
    """Write a JSON manifest describing the preprocessing run."""
    manifest_path = output_dir / f"{slugify_name(request.experiment_name)}_run_manifest.json"
    manifest = {
        "workflow_name": WORKFLOW_NAME,
        "execution_mode": execution_mode,
        "request": asdict(request),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def materialize_fixture_outputs(request: PreprocessingRequest, output_dir: Path) -> PreprocessingResult:
    """Copy committed fixture CSVs into an output directory for validation and review."""
    assert request.premade_plate_name is not None

    source_plate_path, protocol_path = build_fixture_pair(request.premade_plate_name)
    experiment_slug = slugify_name(request.experiment_name)

    output_source_path = output_dir / f"{experiment_slug}_source_plate.csv"
    output_protocol_path = output_dir / f"{experiment_slug}_echo_protocol.csv"
    shutil.copyfile(source_plate_path, output_source_path)
    shutil.copyfile(protocol_path, output_protocol_path)

    protocol_df = load_echo_protocol(output_protocol_path)
    composition_df = build_destination_composition_table(protocol_df)
    composition_path = output_dir / f"{experiment_slug}_destination_composition.csv"
    composition_df.to_csv(composition_path, index=False)

    manifest_path = write_run_manifest(output_dir, request, execution_mode="fixture_replay")
    return PreprocessingResult(
        workflow_name=WORKFLOW_NAME,
        execution_mode="fixture_replay",
        output_dir=output_dir,
        protocol_csv=output_protocol_path,
        source_plate_csv=output_source_path,
        destination_composition_csv=composition_path,
        run_manifest_json=manifest_path,
        notebook_output_path=None,
    )


def execute_notebook_workflow(
    request: PreprocessingRequest,
    output_dir: Path,
    notebook_path: Path,
) -> PreprocessingResult:
    """Run a parameterized preprocessing notebook via papermill."""
    try:
        import papermill as pm
    except ModuleNotFoundError as exc:
        raise RuntimeError("Papermill is required to execute the preprocessing notebook.") from exc

    notebook_output_path = output_dir / f"{slugify_name(request.experiment_name)}_preprocessing_output.ipynb"
    pm.execute_notebook(
        str(notebook_path),
        str(notebook_output_path),
        parameters={
            "workflow_name": WORKFLOW_NAME,
            "plate_mode": request.plate_mode,
            "premade_plate_name": request.premade_plate_name,
            "new_plate_label": request.new_plate_label,
            "experiment_name": request.experiment_name,
            "doses": request.doses,
            "doses2": request.doses2,
            "highest_dose": request.highest_dose,
            "vol_cellextract": request.vol_cellextract,
            "vol_antigen": request.vol_antigen,
            "samples": request.samples,
            "output_dir": str(output_dir),
        },
    )

    manifest_path = write_run_manifest(output_dir, request, execution_mode="notebook")
    protocol_path = output_dir / f"{slugify_name(request.experiment_name)}_echo_protocol.csv"
    source_plate_path = output_dir / f"{slugify_name(request.experiment_name)}_source_plate.csv"
    composition_path = output_dir / f"{slugify_name(request.experiment_name)}_destination_composition.csv"

    return PreprocessingResult(
        workflow_name=WORKFLOW_NAME,
        execution_mode="notebook",
        output_dir=output_dir,
        protocol_csv=protocol_path if protocol_path.exists() else None,
        source_plate_csv=source_plate_path if source_plate_path.exists() else None,
        destination_composition_csv=composition_path if composition_path.exists() else None,
        run_manifest_json=manifest_path,
        notebook_output_path=notebook_output_path,
    )


def run_echo_protocol_preprocessing(
    request: PreprocessingRequest,
    output_dir: Path | None = None,
    workflow_notebook_path: Path | None = None,
) -> PreprocessingResult:
    """Run the fixed preprocessing workflow from form inputs."""
    target_dir = output_dir or (get_output_dir() / slugify_name(request.experiment_name))
    target_dir.mkdir(parents=True, exist_ok=True)

    notebook_path = workflow_notebook_path or get_workflow_notebook_path()
    if notebook_path and notebook_path.exists():
        return execute_notebook_workflow(request, target_dir, notebook_path)

    if request.plate_mode == PLATE_MODE_PREMADE and request.premade_plate_name:
        return materialize_fixture_outputs(request, target_dir)

    raise NotImplementedError(
        "Creating a new plate from scratch requires a parameterized preprocessing notebook or "
        "Python implementation. Set ECHO_WORKFLOW_NOTEBOOK once that workflow exists."
    )
