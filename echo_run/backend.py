"""Backend helpers shared by the CLI and Streamlit UI."""

from __future__ import annotations

import configparser
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLATE_ENTRY_PATTERN = re.compile(r"^(?P<substance>[^:]+):\s*(?P<volume>\d+)nL$")
WELL_PATTERN = re.compile(r"^(?P<row>[A-Z]+)(?P<column>\d+)$")


def get_notebooks_dir() -> Path:
    """Return the configured notebook directory."""
    return Path(os.environ.get("ECHO_NOTEBOOKS_DIR", PROJECT_ROOT / "notebooks"))


def get_data_dir() -> Path:
    """Return the configured data directory."""
    return Path(os.environ.get("ECHO_DATA_DIR", PROJECT_ROOT / "data"))


def suggest_source_plate_layout(
    samples: list[str],
    doses: int,
    doses2: int,
    vol_cellextract: int,
    vol_antigen: int,
) -> dict[str, str]:
    """Generate a recommended source plate layout based on experiment parameters."""
    plate: dict[str, str] = {}

    rows = list("ABCDEFGHIJKLMNOP")
    cols = list(range(1, 25))

    sample_cols = min(len(samples), 12)
    for col_idx in range(sample_cols):
        col = cols[col_idx]
        sample_name = samples[col_idx]
        for row_idx in range(6):
            row = rows[row_idx]
            well = f"{row}{col}"
            plate[well] = f"{sample_name}: {vol_cellextract}nL"

    if doses2 > 0:
        antigen_row_idx = 8
        antigen_wells_needed = min(doses + doses2, 12)
        for col_idx in range(antigen_wells_needed):
            if antigen_row_idx < len(rows):
                row = rows[antigen_row_idx]
                well = f"{row}{cols[col_idx]}"
                if col_idx < doses:
                    plate[well] = f"antigen: {vol_antigen}nL"
                else:
                    plate[well] = f"antigen2: {vol_antigen}nL"

        pbs_row_idx = 8
        pbs_cols_needed = max(doses, doses2)
        for col_idx in range(pbs_cols_needed):
            row = rows[pbs_row_idx]
            well = f"{row}{cols[col_idx + doses]}"
            if well not in plate:
                plate[well] = f"PBS: {vol_antigen}nL"

    elif vol_antigen > 0:
        pbs_row_idx = 8
        for col_idx in range(doses):
            row = rows[pbs_row_idx]
            well = f"{row}{cols[col_idx]}"
            if well not in plate:
                plate[well] = f"PBS: {vol_antigen}nL"

    return plate


DEFAULT_CONFIG = {
    "experiment_name": "my_experiment",
    "doses": 6,
    "doses2": 3,
    "highest_dose": 4.0,
    "vol_cellextract": 2000,
    "vol_antigen": 2000,
    "samples": "sample1,sample2,sample3",
}


@dataclass(frozen=True)
class SanityReport:
    """Summary of the repository state needed for backend smoke checks."""

    notebooks: list[str]
    data_files: list[str]
    config_values: dict[str, object]
    selected_notebook: str | None
    streamlit_available: bool


def get_notebooks(notebooks_dir: Path | None = None) -> list[str]:
    """Get the user-facing notebook list."""
    if notebooks_dir is None:
        notebooks_dir = get_notebooks_dir()
    if not notebooks_dir.exists():
        return []
    return sorted(
        file.name
        for file in notebooks_dir.glob("*.ipynb")
        if not file.name.endswith("-checkpoint.ipynb")
    )


def normalize_ini_text(raw_text: str) -> str:
    """Support both flat INI files and [experiment]-section INI files."""
    if raw_text.lstrip().startswith("["):
        return raw_text
    return "[experiment]\n" + raw_text


def load_config_text(config_text: str) -> configparser.ConfigParser:
    """Parse uploaded or file-based config text."""
    config = configparser.ConfigParser()
    config.read_string(normalize_ini_text(config_text))
    return config


def parse_config_text(config_text: str) -> tuple[dict[str, object], str | None]:
    """Return normalized config values and selected notebook."""
    config = load_config_text(config_text)
    values = DEFAULT_CONFIG.copy()

    config_items: dict[str, str] = {}
    if config.defaults():
        config_items.update(config.defaults())
    if config.has_section("experiment"):
        config_items.update(dict(config["experiment"].items()))

    for key in ("experiment_name", "samples"):
        if key in config_items:
            values[key] = config_items[key]

    for key in ("doses", "doses2", "vol_cellextract", "vol_antigen"):
        if key in config_items:
            values[key] = int(config_items[key])

    if "highest_dose" in config_items:
        values["highest_dose"] = float(config_items["highest_dose"])

    return values, config_items.get("notebook")


def parse_uploaded_config(
    uploaded_file: BinaryIO,
) -> tuple[dict[str, object], str | None]:
    """Return normalized config values from a Streamlit-uploaded file."""
    content = (
        uploaded_file.getvalue()
        if hasattr(uploaded_file, "getvalue")
        else uploaded_file.read()
    )
    return parse_config_text(content.decode("utf-8"))


def list_data_files(data_dir: Path | None = None) -> list[str]:
    """List sample data files included with the repo."""
    if data_dir is None:
        data_dir = get_data_dir()
    if not data_dir.exists():
        return []
    return sorted(
        str(path.relative_to(PROJECT_ROOT))
        for path in data_dir.rglob("*")
        if path.is_file()
    )


def get_source_plate_map_paths(data_dir: Path | None = None) -> list[Path]:
    """Return committed source plate CSVs that can be visualized in the UI."""
    if data_dir is None:
        data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    if not raw_dir.exists():
        return []
    return sorted(raw_dir.rglob("*_source_plate*.csv"))


def get_echo_protocol_paths(data_dir: Path | None = None) -> list[Path]:
    """Return committed Echo protocol CSVs that can be visualized in the UI."""
    if data_dir is None:
        data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    if not raw_dir.exists():
        return []
    return sorted(raw_dir.rglob("*_echo_protocol*.csv"))


def load_source_plate_map(csv_path: Path):
    """Load a source plate CSV as a DataFrame with blank cells normalized."""
    import pandas as pd

    plate_map = pd.read_csv(csv_path, index_col=0)
    return plate_map.fillna("")


def load_echo_protocol(csv_path: Path):
    """Load an Echo protocol CSV and normalize the extra pandas index column."""
    import pandas as pd

    protocol = pd.read_csv(csv_path)
    if "Unnamed: 0" in protocol.columns:
        protocol = protocol.drop(columns=["Unnamed: 0"])
    return protocol


def parse_plate_entry(cell_value: object) -> tuple[str | None, int | None]:
    """Extract the substance name and volume from a source plate cell."""
    text = str(cell_value).strip()
    if not text:
        return None, None
    match = PLATE_ENTRY_PATTERN.match(text)
    if not match:
        return text, None
    return match.group("substance"), int(match.group("volume"))


def build_source_plate_summary(plate_map):
    """Summarize occupied wells and loaded substances for a source plate map."""
    import pandas as pd

    summary_rows: list[dict[str, object]] = []
    grouped: dict[str, dict[str, int]] = defaultdict(
        lambda: {"wells": 0, "total_volume_nl": 0, "max_volume_nl": 0}
    )

    occupied_wells = 0
    max_volume = 0

    for row_label, row in plate_map.iterrows():
        for column_label, cell_value in row.items():
            substance, volume = parse_plate_entry(cell_value)
            if not substance:
                continue
            occupied_wells += 1
            grouped[substance]["wells"] += 1
            if volume is not None:
                grouped[substance]["total_volume_nl"] += volume
                grouped[substance]["max_volume_nl"] = max(
                    grouped[substance]["max_volume_nl"], volume
                )
                max_volume = max(max_volume, volume)

    for substance in sorted(grouped):
        stats = grouped[substance]
        summary_rows.append(
            {
                "substance": substance,
                "wells": stats["wells"],
                "total_volume_nl": stats["total_volume_nl"],
                "max_volume_nl": stats["max_volume_nl"],
            }
        )

    return {
        "occupied_wells": occupied_wells,
        "empty_wells": int(plate_map.size - occupied_wells),
        "max_volume_nl": max_volume,
        "substances": sorted(grouped),
        "summary_table": pd.DataFrame(summary_rows),
    }


def build_well_metric_grid(protocol_df, well_column: str, value_column: str):
    """Aggregate a protocol table into a row/column grid for plate visualization."""
    import pandas as pd

    metric_rows: dict[str, dict[int, int]] = defaultdict(dict)
    max_value = 0

    grouped = protocol_df.groupby(well_column)[value_column].sum()
    for well_name, metric_value in grouped.items():
        match = WELL_PATTERN.match(str(well_name))
        if not match:
            continue
        row_label = match.group("row")
        column_label = int(match.group("column"))
        value = int(metric_value)
        metric_rows[row_label][column_label] = value
        max_value = max(max_value, value)

    if not metric_rows:
        return pd.DataFrame(), 0

    sorted_rows = sorted(metric_rows)
    sorted_columns = sorted({column for row in metric_rows.values() for column in row})
    grid = pd.DataFrame(index=sorted_rows, columns=sorted_columns).fillna(0)

    for row_label, columns in metric_rows.items():
        for column_label, value in columns.items():
            grid.loc[row_label, column_label] = value

    return grid.astype(int), max_value


def build_destination_composition_grid(protocol_df):
    """Build a destination-well grid showing the composition of each well."""
    import pandas as pd

    composition_rows: dict[str, dict[int, str]] = defaultdict(dict)
    component_count_rows: dict[str, dict[int, int]] = defaultdict(dict)
    max_components = 0

    grouped = protocol_df.groupby(
        ["Destination Well", "Sample Name", "Source Well"], as_index=False
    ).agg(total_volume_nl=("Transfer Volume", "sum"))

    for destination_well, sub_df in grouped.groupby("Destination Well"):
        match = WELL_PATTERN.match(str(destination_well))
        if not match:
            continue

        row_label = match.group("row")
        column_label = int(match.group("column"))
        ordered = sub_df.sort_values(
            ["total_volume_nl", "Sample Name"], ascending=[False, True]
        )
        lines = [
            f"{sample}@{source}: {volume:,} nL"
            for sample, source, volume in ordered[
                ["Sample Name", "Source Well", "total_volume_nl"]
            ].itertuples(index=False, name=None)
        ]

        composition_rows[row_label][column_label] = "\n".join(lines)
        component_count_rows[row_label][column_label] = len(lines)
        max_components = max(max_components, len(lines))

    if not composition_rows:
        return pd.DataFrame(), pd.DataFrame(), 0

    sorted_rows = sorted(composition_rows)
    sorted_columns = sorted(
        {column for row in composition_rows.values() for column in row}
    )

    composition_grid = pd.DataFrame(index=sorted_rows, columns=sorted_columns).fillna(
        ""
    )
    component_count_grid = pd.DataFrame(
        index=sorted_rows, columns=sorted_columns
    ).fillna(0)

    for row_label, columns in composition_rows.items():
        for column_label, value in columns.items():
            composition_grid.loc[row_label, column_label] = value

    for row_label, columns in component_count_rows.items():
        for column_label, value in columns.items():
            component_count_grid.loc[row_label, column_label] = value

    return composition_grid, component_count_grid.astype(int), max_components


def build_echo_protocol_summary(protocol_df):
    """Summarize committed Echo protocol CSVs for UI inspection."""

    (
        destination_composition_grid,
        destination_component_count_grid,
        destination_max_components,
    ) = build_destination_composition_grid(protocol_df)
    destination_count_grid, _ = build_well_metric_grid(
        protocol_df.assign(transfer_count=1),
        "Destination Well",
        "transfer_count",
    )
    source_count_grid, source_max_count = build_well_metric_grid(
        protocol_df.assign(transfer_count=1),
        "Source Well",
        "transfer_count",
    )

    return {
        "transfer_count": int(len(protocol_df)),
        "sample_count": int(protocol_df["Sample Name"].nunique()),
        "source_well_count": int(protocol_df["Source Well"].nunique()),
        "destination_well_count": int(protocol_df["Destination Well"].nunique()),
        "total_transfer_volume_nl": int(protocol_df["Transfer Volume"].sum()),
        "destination_composition_grid": destination_composition_grid,
        "destination_component_count_grid": destination_component_count_grid,
        "destination_max_components": destination_max_components,
        "destination_count_grid": destination_count_grid,
        "source_count_grid": source_count_grid,
        "source_max_count": source_max_count,
    }


def streamlit_is_available() -> bool:
    """Check whether the runtime dependency needed for the UI is importable."""
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def build_sanity_report(
    config_path: Path | None = None,
    notebooks_dir: Path | None = None,
    data_dir: Path | None = None,
) -> SanityReport:
    """Create a backend-only sanity report without importing Streamlit UI code."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config.example.ini"
    if notebooks_dir is None:
        notebooks_dir = get_notebooks_dir()
    if data_dir is None:
        data_dir = get_data_dir()

    config_values, selected_notebook = parse_config_text(
        config_path.read_text(encoding="utf-8")
    )
    return SanityReport(
        notebooks=get_notebooks(notebooks_dir),
        data_files=list_data_files(data_dir),
        config_values=config_values,
        selected_notebook=selected_notebook,
        streamlit_available=streamlit_is_available(),
    )
