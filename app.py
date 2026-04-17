"""
Echo Protocol - Web UI.

A Streamlit app for generating Beckman Echo liquid handler protocols.
"""

from __future__ import annotations

from datetime import datetime
from time import perf_counter

from echo_run.backend import (
    DEFAULT_CONFIG,
    build_echo_protocol_summary,
    build_source_plate_remaining_summary,
    build_source_plate_summary,
    get_source_plate_map_paths,
    load_echo_protocol,
    load_source_plate_map,
    parse_plate_entry,
    suggest_source_plate_layout,
)
from echo_run.preprocessing import (
    PLATE_MODE_MANUAL,
    PLATE_MODE_PREMADE,
    PreprocessingRequest,
    build_fixture_pair,
    parse_samples,
    run_echo_protocol_preprocessing,
)

PLATE_COLORS = [
    "#2563eb",
    "#059669",
    "#dc2626",
    "#7c3aed",
    "#d97706",
    "#0f766e",
    "#be185d",
    "#4f46e5",
]
WORKFLOW_NAME = "echo-protocol-preprocessing"
REAGENT_NAMES = {"PBS", "antigen", "antigen2"}


def get_plate_wells():
    """Return list of 384 well positions A1-P24."""
    rows = list("ABCDEFGHIJKLMNOP")
    cols = list(range(1, 25))
    return [f"{r}{c}" for r in rows for c in cols]


def render_manual_plate_editor(
    st, key_prefix: str = "manual", initial_data: dict | None = None
):
    """Render an editable 384-well plate grid using data editor."""
    st.caption(
        "Edit wells below. Format: `name: volume` (e.g., `sample1: 60000`). Empty = no data."
    )

    if f"{key_prefix}_plate_data" not in st.session_state:
        if initial_data:
            st.session_state[f"{key_prefix}_plate_data"] = initial_data
        else:
            st.session_state[f"{key_prefix}_plate_data"] = {}

    plate_data = st.session_state[f"{key_prefix}_plate_data"]

    rows = list("ABCDEFGHIJKLMNOP")
    cols = list(range(1, 25))

    grid_data = []
    for row in rows:
        row_data = {"Well": row}
        for col in cols:
            well = f"{row}{col}"
            row_data[str(col)] = plate_data.get(well, "")
        grid_data.append(row_data)

    edited = st.data_editor(
        grid_data,
        column_config={
            "Well": st.column_config.TextColumn("Row", width="small", disabled=True),
            **{
                str(c): st.column_config.TextColumn(str(c), width="small") for c in cols
            },
        },
        hide_index=True,
        num_rows="fixed",
        key=f"{key_prefix}_editor",
        width="stretch",
    )

    new_plate_data = {}
    for row in rows:
        for col in cols:
            well = f"{row}{col}"
            value = edited[rows.index(row)].get(str(col), "")
            if value and value.strip():
                new_plate_data[well] = value.strip()

    if new_plate_data != plate_data:
        st.session_state[f"{key_prefix}_plate_data"] = new_plate_data

    return new_plate_data


def parse_manual_plate_data(plate_data: dict) -> dict[str, tuple[str, int]]:
    """Parse user-entered plate data into structured format."""
    result = {}
    for well, entry in plate_data.items():
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            parts = entry.split(":", 1)
            substance = parts[0].strip()
            try:
                volume = int(parts[1].strip().rstrip("nL").strip())
                result[well] = (substance, volume)
            except (ValueError, IndexError):
                pass
    return result


def source_plate_map_to_editor_data(plate_map) -> dict[str, str]:
    """Flatten a source plate DataFrame into editor-friendly well entries."""
    editor_data: dict[str, str] = {}
    for row_label, row in plate_map.iterrows():
        for column_label, cell_value in row.items():
            text = str(cell_value).strip()
            if not text:
                continue
            editor_data[f"{row_label}{column_label}"] = text
    return editor_data


def sort_wells(wells: list[str]) -> list[str]:
    """Return wells ordered by plate position."""
    return sorted(wells, key=lambda well: (well[0], int(well[1:])))


def calculate_dose_volumes(n_doses: int, max_volume_nl: int, dilution_factor: float = 3.0) -> list[int]:
    """Approximate the notebook's serial-dilution transfer volumes."""
    if n_doses <= 0:
        return []

    volumes = []
    for index in range(n_doses):
        volume = int(max_volume_nl / (dilution_factor**index))
        volumes.append(max(volume, 10))
    return volumes


def extract_premade_plate_structure(editor_data: dict[str, str]) -> dict[str, object]:
    """Split a premade plate into sample wells, reagent row, and default capacities."""
    sample_slots: list[str] = []
    sample_names: list[str] = []
    sample_volumes: list[int] = []
    reagent_rows: list[str] = []
    reagent_volumes: list[int] = []

    for well in sort_wells(list(editor_data.keys())):
        substance, volume = parse_plate_entry(editor_data[well])
        if not substance:
            continue
        if substance in REAGENT_NAMES:
            reagent_rows.append(well[0])
            if volume is not None:
                reagent_volumes.append(volume)
            continue
        sample_slots.append(well)
        sample_names.append(substance)
        if volume is not None:
            sample_volumes.append(volume)

    reagent_row = reagent_rows[0] if reagent_rows else "I"
    reagent_slots = [f"{reagent_row}{column}" for column in range(1, 25)]

    return {
        "sample_slots": sample_slots,
        "sample_names": sample_names,
        "sample_volume_nl": max(sample_volumes) if sample_volumes else 60000,
        "reagent_slots": reagent_slots,
        "reagent_capacity_nl": max(reagent_volumes) if reagent_volumes else 55000,
    }


def build_premade_plate_suggestion(
    base_editor_data: dict[str, str],
    sample_names: list[str],
    doses: int,
    doses2: int,
    vol_antigen: int,
) -> dict[str, str]:
    """Regenerate a premade-style plate while preserving its historical layout pattern."""
    structure = extract_premade_plate_structure(base_editor_data)
    layout: dict[str, str] = {}

    sample_slots = structure["sample_slots"]
    sample_volume_nl = int(structure["sample_volume_nl"])
    for well, sample_name in zip(sample_slots, sample_names):
        layout[well] = f"{sample_name}: {sample_volume_nl}nL"

    reagent_slots = structure["reagent_slots"]
    reagent_capacity_nl = max(int(structure["reagent_capacity_nl"]), 1000)
    antigen1_volumes = calculate_dose_volumes(doses, vol_antigen)
    antigen2_volumes = calculate_dose_volumes(doses2, vol_antigen)
    antigen1_pbs = [max(vol_antigen - volume, 0) for volume in antigen1_volumes]
    antigen2_pbs = [max(vol_antigen - volume, 0) for volume in antigen2_volumes]

    sample_count = len(sample_names)
    total_antigen1 = sum(antigen1_volumes) * sample_count
    total_antigen2 = sum(antigen2_volumes) * sample_count
    total_pbs = (sum(antigen1_pbs) + sum(antigen2_pbs)) * sample_count

    reagent_plan: list[tuple[str, int]] = []
    for reagent_name, total_volume in (
        ("antigen", total_antigen1),
        ("antigen2", total_antigen2),
        ("PBS", total_pbs),
    ):
        remaining = total_volume
        while remaining > 0:
            loaded_volume = min(reagent_capacity_nl, remaining)
            reagent_plan.append((reagent_name, max(loaded_volume, 1000)))
            remaining -= loaded_volume

    for well, (reagent_name, loaded_volume) in zip(reagent_slots, reagent_plan):
        layout[well] = f"{reagent_name}: {loaded_volume}nL"

    return layout


def infer_premade_parameters(selected_plate_name: str, protocol_path) -> dict[str, object]:
    """Infer UI defaults from a historical premade plate and its protocol."""
    protocol_df = load_echo_protocol(protocol_path)
    source_plate_path, _ = build_fixture_pair(selected_plate_name)
    source_plate_map = load_source_plate_map(source_plate_path)
    source_editor_data = source_plate_map_to_editor_data(source_plate_map)
    sample_names = extract_premade_plate_structure(source_editor_data)["sample_names"]

    sample_transfers = protocol_df[~protocol_df["Sample Name"].isin(REAGENT_NAMES)]
    reagent_transfers = protocol_df[protocol_df["Sample Name"].isin(REAGENT_NAMES)]

    doses = 6
    doses2 = 0
    if sample_names:
        sample_count = len(sample_names)
        doses = max(
            1,
            int((reagent_transfers["Sample Name"] == "antigen").sum() / sample_count),
        )
        doses2 = int((reagent_transfers["Sample Name"] == "antigen2").sum() / sample_count)

    experiment_name = selected_plate_name.replace("_source_plate", "_").replace(".csv", "")
    return {
        "experiment_name": experiment_name.strip("_") or DEFAULT_CONFIG["experiment_name"],
        "doses": doses,
        "doses2": doses2,
        "highest_dose": DEFAULT_CONFIG["highest_dose"],
        "vol_cellextract": int(sample_transfers["Transfer Volume"].max())
        if not sample_transfers.empty
        else DEFAULT_CONFIG["vol_cellextract"],
        "vol_antigen": int(reagent_transfers["Transfer Volume"].max())
        if not reagent_transfers.empty
        else DEFAULT_CONFIG["vol_antigen"],
        "samples": ",".join(sample_names) if sample_names else DEFAULT_CONFIG["samples"],
    }


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a hex color into an rgba() string for CSS."""
    stripped = hex_color.lstrip("#")
    red = int(stripped[0:2], 16)
    green = int(stripped[2:4], 16)
    blue = int(stripped[4:6], 16)
    return f"rgba({red}, {green}, {blue}, {alpha:.2f})"


def style_source_plate_map(plate_map, max_volume_nl: int, substances: list[str]):
    """Return a color-coded styler for a committed source plate grid."""
    substance_colors = {
        substance: PLATE_COLORS[index % len(PLATE_COLORS)]
        for index, substance in enumerate(substances)
    }

    def style_cell(cell_value: object) -> str:
        substance, volume = parse_plate_entry(cell_value)
        if not substance:
            return "background-color: #f8fafc; color: #94a3b8;"

        base_color = substance_colors.get(substance, "#475569")
        alpha = 0.25
        if volume is not None and max_volume_nl:
            alpha = 0.25 + (0.55 * (volume / max_volume_nl))

        return (
            f"background-color: {_hex_to_rgba(base_color, min(alpha, 0.85))}; "
            "color: #0f172a; font-weight: 600;"
        )

    return plate_map.style.map(style_cell).set_properties(
        **{"text-align": "center", "white-space": "nowrap"}
    )


def style_numeric_plate_grid(metric_grid, max_value: int, color: str):
    """Return a color-coded styler for numeric well metrics."""

    def style_cell(cell_value: object) -> str:
        value = int(cell_value)
        if value <= 0:
            return "background-color: #f8fafc; color: #94a3b8;"

        alpha = 0.20
        if max_value:
            alpha = 0.20 + (0.65 * (value / max_value))
        return (
            f"background-color: {_hex_to_rgba(color, min(alpha, 0.90))}; "
            "color: #0f172a; font-weight: 600;"
        )

    return (
        metric_grid.style.map(style_cell)
        .format("{:,.0f}")
        .set_properties(**{"text-align": "center", "white-space": "nowrap"})
    )


def style_composition_plate_grid(
    composition_grid, component_count_grid, max_components: int
):
    """Return a styled destination composition grid."""

    def style_cell(cell_value: object) -> str:
        if not str(cell_value).strip():
            return "background-color: #f8fafc; color: #94a3b8;"
        return ""

    def style_from_counts(_column):
        styles = []
        for row_label in composition_grid.index:
            count = int(component_count_grid.loc[row_label, _column.name])
            if count <= 0:
                styles.append("background-color: #f8fafc; color: #94a3b8;")
                continue
            alpha = 0.20
            if max_components:
                alpha = 0.20 + (0.65 * (count / max_components))
            styles.append(
                f"background-color: {_hex_to_rgba('#0f766e', min(alpha, 0.90))}; "
                "color: #0f172a; font-weight: 600;"
            )
        return styles

    return (
        composition_grid.style.map(style_cell)
        .apply(style_from_counts, axis=0)
        .set_properties(
            **{"white-space": "pre-line", "text-align": "left", "vertical-align": "top"}
        )
    )


def build_setup_summary_rows(
    *,
    plate_mode: str,
    experiment_name: str,
    doses: int,
    doses2: int,
    highest_dose: float,
    vol_cellextract: int,
    vol_antigen: int,
    samples: str,
    premade_plate_name: str | None = None,
    manual_well_count: int | None = None,
):
    """Build ordered setup rows for reference and generated-run summaries."""
    sample_list = parse_samples(samples)
    rows = [
        ("Experiment", experiment_name),
        ("Plate mode", plate_mode),
    ]

    if plate_mode == PLATE_MODE_PREMADE:
        rows.append(("Selected premade plate", premade_plate_name or "n/a"))
    else:
        rows.append(
            (
                "Manual source plate",
                f"{manual_well_count} defined wells"
                if manual_well_count is not None
                else "custom layout",
            )
        )

    rows.extend(
        [
            ("Doses", doses),
            ("Second curve doses", doses2),
            ("Highest dose", f"{highest_dose:g} µM"),
            ("Cell extract volume", f"{vol_cellextract:,} nL"),
            ("Antigen volume", f"{vol_antigen:,} nL"),
            ("Sample count", len(sample_list)),
            ("Samples", ", ".join(sample_list) if sample_list else "n/a"),
        ]
    )
    return rows


def render_setup_summary(
    st, heading: str, rows: list[tuple[str, object]], caption: str | None = None
):
    """Render a compact setup summary table."""
    st.markdown(f"**{heading}**")
    if caption:
        st.caption(caption)
    st.table(
        {
            "Setting": [label for label, _value in rows],
            "Value": [str(value) for _label, value in rows],
        }
    )


def render_download_artifacts(st, output_files: list[tuple[str, str, str | None]]):
    """Render downloadable run artifacts with clearer labels."""
    st.markdown("**Downloads**")
    st.caption("Choose the file you want to keep from this run.")

    for title, description, raw_path in output_files:
        if not raw_path:
            continue
        from pathlib import Path

        path = Path(raw_path)
        if not path.exists():
            continue

        info_col, action_col = st.columns([3, 1])
        with info_col:
            st.markdown(f"- **{title}**")
            st.caption(f"{description} File: `{path.name}`")
        with action_col:
            st.download_button(
                "Download",
                data=path.read_bytes(),
                file_name=path.name,
                mime="text/csv" if path.suffix == ".csv" else "application/json",
                width="stretch",
                help=f"Download {title.lower()} to your computer.",
                key=f"download_{title}_{path.name}",
            )


def format_duration(seconds: float) -> str:
    """Return a friendly duration string."""
    if seconds < 1:
        return f"{seconds:.2f} seconds"
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    minutes = int(seconds // 60)
    remaining = seconds % 60
    return f"{minutes}m {remaining:.1f}s"


def render_source_plate_panel(st, source_plate_path, heading: str):
    """Render a source plate map with summary metrics."""
    st.markdown(f"**{heading}**")
    plate_map = load_source_plate_map(source_plate_path)
    summary = build_source_plate_summary(plate_map)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric("Occupied Wells", summary["occupied_wells"])
    with metric_col2:
        st.metric("Empty Wells", summary["empty_wells"])
    with metric_col3:
        st.metric("Substances", len(summary["substances"]))
    with metric_col4:
        st.metric(
            "Max Volume",
            f"{summary['max_volume_nl']:,} nL" if summary["max_volume_nl"] else "n/a",
        )

    if summary["substances"]:
        st.caption(f"Loaded materials: {', '.join(summary['substances'])}")
    else:
        st.info("No loaded wells were detected in this plate map.")

    st.dataframe(
        style_source_plate_map(
            plate_map,
            summary["max_volume_nl"],
            summary["substances"],
        ),
        width="stretch",
        height=560,
    )
    st.caption(
        "Cells are colored by substance. Darker fills indicate larger loaded volumes."
    )


def render_source_plate_table(st, source_plate_path, heading: str):
    """Render a source plate map as a plain table for easy well-by-well reading."""
    st.markdown(f"**{heading}**")
    plate_map = load_source_plate_map(source_plate_path)
    st.dataframe(
        plate_map.fillna(""),
        width="stretch",
        height=560,
    )
    st.caption(
        "This view matches the manual plate builder so each well can be read directly in plate context."
    )


def render_source_plate_reference_details(st, source_plate_path):
    """Render summary details for a premade source plate beneath the workflow views."""
    plate_map = load_source_plate_map(source_plate_path)
    summary = build_source_plate_summary(plate_map)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric("Occupied Wells", summary["occupied_wells"])
    with metric_col2:
        st.metric("Empty Wells", summary["empty_wells"])
    with metric_col3:
        st.metric("Substances", len(summary["substances"]))
    with metric_col4:
        st.metric(
            "Max Volume",
            f"{summary['max_volume_nl']:,} nL" if summary["max_volume_nl"] else "n/a",
        )

    if summary["summary_table"].empty:
        st.info("No loaded wells were detected in this plate map.")
        return

    details_table = summary["summary_table"].rename(
        columns={
            "substance": "Substance",
            "wells": "Wells",
            "total_volume_nl": "Total Volume (nL)",
            "max_volume_nl": "Max Volume (nL)",
        }
    )
    st.dataframe(details_table, width="stretch", hide_index=True)


def render_protocol_panel(st, protocol_path, heading: str, source_plate_path=None):
    """Render a protocol preview focused on validation-oriented review."""
    st.markdown(f"**{heading}**")
    protocol_df = load_echo_protocol(protocol_path)
    summary = build_echo_protocol_summary(protocol_df)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric("Transfers", f"{summary['transfer_count']:,}")
    with metric_col2:
        st.metric("Source Wells Used", summary["source_well_count"])
    with metric_col3:
        st.metric("Destination Wells Used", summary["destination_well_count"])
    with metric_col4:
        st.metric(
            "Transferred Volume",
            f"{summary['total_transfer_volume_nl']:,} nL",
        )

    st.markdown("**Generated Echo protocol**")
    st.dataframe(
        protocol_df,
        width="stretch",
        height=320,
    )
    st.caption(
        "Review the actual transfer rows that were generated before opening the destination composition view."
    )

    with st.expander("Destination well composition", expanded=False):
        st.dataframe(
            style_composition_plate_grid(
                summary["destination_composition_grid"],
                summary["destination_component_count_grid"],
                summary["destination_max_components"],
            ),
            width="stretch",
            height=420,
        )
        st.caption(
            "Each cell shows which sample/source components contribute to that destination well."
        )

    if source_plate_path:
        remaining_summary = build_source_plate_remaining_summary(
            load_source_plate_map(source_plate_path),
            protocol_df,
        )
        st.markdown("**Source Plate Leftover Volume**")
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric(
                "Volume Remaining",
                f"{remaining_summary['total_remaining_volume_nl']:,} nL",
                help="Total volume still left in loaded source wells after this protocol.",
            )
        with metric_col2:
            st.metric(
                "Reusable Wells",
                remaining_summary["reusable_well_count"],
                help="Loaded source wells that still have volume remaining after transfers.",
            )

        if not remaining_summary["summary_table"].empty:
            st.dataframe(
                remaining_summary["summary_table"],
                width="stretch",
                hide_index=True,
            )
        with st.expander("Leftover volume by source well", expanded=False):
            st.dataframe(
                remaining_summary["wells_table"],
                width="stretch",
                hide_index=True,
            )

def main():
    import streamlit as st

    st.set_page_config(
        page_title="Echo Protocol",
        page_icon="🔬",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        [data-testid="stHeaderActionElements"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🔬 Echo Protocol")
    st.markdown(
        "Generate Beckman Echo liquid handler protocols without writing code. "
        "Define your source plate and experiment parameters, then export ready-to-run CSV transfer files."
    )
    st.caption(
        "💡 Tip: Use a premade plate for quick experiments, or define a new plate manually for custom layouts."
    )

    form_defaults = {
        "experiment_name_input": str(DEFAULT_CONFIG["experiment_name"]),
        "doses_input": int(DEFAULT_CONFIG["doses"]),
        "doses2_input": int(DEFAULT_CONFIG["doses2"]),
        "highest_dose_input": float(DEFAULT_CONFIG["highest_dose"]),
        "vol_cellextract_input": int(DEFAULT_CONFIG["vol_cellextract"]),
        "vol_antigen_input": int(DEFAULT_CONFIG["vol_antigen"]),
        "samples_input": str(DEFAULT_CONFIG["samples"]),
    }
    for key, value in form_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    source_plate_paths = get_source_plate_map_paths()
    source_plate_options = [path.name for path in source_plate_paths]

    st.subheader("1. Choose Your Plate")

    st.markdown("**How would you like to set up your source plate?**")
    plate_col1, plate_col2 = st.columns(2)

    with plate_col1:
        st.info("📋 **Use a Premade Plate**")
        st.caption("Start with a previously used plate layout as reference")
    with plate_col2:
        st.info("🆕 **Create a New Plate**")
        st.caption("Define your own custom plate layout from scratch")

    plate_mode = st.segmented_control(
        "Plate Source",
        {"premade": "📋 Premade Plate", "manual": "🆕 New Plate"},
        default="manual",
        help="Choose an existing plate or define manually.",
    )

    if plate_mode == "premade":
        plate_mode = PLATE_MODE_PREMADE
    else:
        plate_mode = PLATE_MODE_MANUAL

    if plate_mode == PLATE_MODE_PREMADE:
        if source_plate_options:
            selected_plate_name = st.selectbox(
                "Select a premade plate to use",
                source_plate_options,
                help="Choose a committed plate layout to inspect, edit, and regenerate from.",
            )
        else:
            st.warning("No premade source plates available.")
            selected_plate_name = None
    else:
        selected_plate_name = None
    premade_editor_seed: dict[str, str] | None = None
    parsed_premade_plate = None
    parsed_manual_plate = None

    if plate_mode == PLATE_MODE_PREMADE and selected_plate_name:
        try:
            selected_source_path, selected_protocol_path = build_fixture_pair(
                selected_plate_name
            )
            premade_plate_map = load_source_plate_map(selected_source_path)
            premade_editor_seed = source_plate_map_to_editor_data(premade_plate_map)

            if st.session_state.get("premade_editor_source") != selected_plate_name:
                st.session_state["premade_plate_data"] = premade_editor_seed
                st.session_state["premade_editor_source"] = selected_plate_name
                inferred = infer_premade_parameters(
                    selected_plate_name,
                    selected_protocol_path,
                )
                st.session_state["experiment_name_input"] = str(inferred["experiment_name"])
                st.session_state["doses_input"] = int(inferred["doses"])
                st.session_state["doses2_input"] = int(inferred["doses2"])
                st.session_state["highest_dose_input"] = float(inferred["highest_dose"])
                st.session_state["vol_cellextract_input"] = int(inferred["vol_cellextract"])
                st.session_state["vol_antigen_input"] = int(inferred["vol_antigen"])
                st.session_state["samples_input"] = str(inferred["samples"])

            st.markdown("### 📋 Reference Workflow")
            st.caption(
                "Use the source plate table and the paired historical protocol together to understand how a previously run plate flows into the Echo output."
            )

            render_source_plate_table(
                st, selected_source_path, "Premade Source Plate Layout"
            )
            render_protocol_panel(
                st,
                selected_protocol_path,
                "Historical Protocol for This Plate",
                source_plate_path=selected_source_path,
            )

            with st.expander("Plate Details and Substance Summary", expanded=False):
                render_source_plate_reference_details(st, selected_source_path)

        except (FileNotFoundError, FileExistsError) as exc:
            st.warning(str(exc))

    st.divider()
    st.subheader("2. Experiment Parameters")

    if plate_mode == PLATE_MODE_PREMADE and selected_plate_name:
        st.info(
            "These premade parameter defaults are being derived from the selected source plate and its historical protocol. This inference should be validated with end users before it is treated as final workflow behavior."
        )

    col1, col2 = st.columns(2)

    with col1:
        experiment_name = st.text_input(
            "Experiment Name",
            help="Used in output filenames.",
            key="experiment_name_input",
        )
        doses = st.number_input(
            "Number of Doses",
            min_value=1,
            max_value=24,
            help="Number of doses per sample.",
            key="doses_input",
        )
        doses2 = st.number_input(
            "Number of Doses (Second Curve)",
            min_value=0,
            max_value=24,
            help="Number of points in the second antigen dose curve.",
            key="doses2_input",
        )
        highest_dose = st.number_input(
            "Highest Dose (µM)",
            min_value=0.1,
            max_value=100.0,
            step=0.1,
            help="Highest dose concentration in micromolar.",
            key="highest_dose_input",
        )

    with col2:
        vol_cellextract = st.number_input(
            "Sample Volume (nL)",
            min_value=1,
            max_value=100000,
            help="Volume of sample to transfer to each destination well.",
            key="vol_cellextract_input",
        )
        vol_antigen = st.number_input(
            "Reagent Volume (nL)",
            min_value=0,
            max_value=100000,
            help="Volume of reagent (antigen/PBS) to transfer.",
            key="vol_antigen_input",
        )
        samples = st.text_input(
            "Sample Names",
            help="Comma-separated list of sample names.",
            key="samples_input",
        )

    sample_list = parse_samples(samples)

    if plate_mode == PLATE_MODE_PREMADE and selected_plate_name and premade_editor_seed:
        st.markdown("**Quick Plate Setup**")
        action_col1, action_col2 = st.columns([1, 2])
        with action_col1:
            if st.button(
                "Apply Suggestion",
                key="apply_premade_suggestion",
                width="stretch",
                help="Use the current parameter values to rebuild the premade plate in its historical layout pattern.",
            ):
                suggested_layout = build_premade_plate_suggestion(
                    premade_editor_seed,
                    sample_list,
                    doses,
                    doses2,
                    vol_antigen,
                )
                st.session_state["premade_plate_data"] = suggested_layout
                st.rerun()
        with action_col2:
            st.caption(
                "Use the current parameters to auto-build a refreshed version of the selected premade plate."
            )

    if plate_mode == PLATE_MODE_PREMADE and selected_plate_name and premade_editor_seed:
        st.subheader("3. Adjust Source Plate")
        st.caption(
            "Start from the selected premade plate and make any well-by-well fixes you need before running."
        )

        control_col1, control_col2 = st.columns([1, 2])
        with control_col1:
            if st.button(
                "Reset to Premade",
                key="reset_premade_plate",
                help="Restore the original committed premade source plate layout.",
            ):
                st.session_state["premade_plate_data"] = premade_editor_seed.copy()
                st.rerun()
        with control_col2:
            st.caption(
                "Reset brings back the original historical plate layout."
            )

        premade_plate_data = render_manual_plate_editor(
            st,
            "premade",
            st.session_state.get("premade_plate_data", premade_editor_seed),
        )
        parsed_premade_plate = parse_manual_plate_data(premade_plate_data)
    elif plate_mode == PLATE_MODE_MANUAL:
        st.subheader("3. Define Source Plate")

        if sample_list:
            st.markdown("**Quick Plate Setup**")
            col_apply, col_note = st.columns([1, 2])
            with col_apply:
                if st.button(
                    "Apply Suggestion",
                    key="apply_suggestion",
                    width="stretch",
                    help="Use the current parameter values to auto-fill a suggested manual plate layout.",
                ):
                    suggested_layout = suggest_source_plate_layout(
                        sample_list, doses, doses2, vol_cellextract, vol_antigen
                    )
                    st.session_state["manual_plate_data"] = suggested_layout
                    st.rerun()
            with col_note:
                st.caption(
                    f"Use the current parameters to auto-fill a suggested layout for {len(sample_list)} samples."
                )
            initial_for_editor = st.session_state.get("manual_plate_data")
        else:
            initial_for_editor = st.session_state.get("manual_plate_data")

        st.markdown(
            "Enter substances and volumes for each well. Format: `name: volume` "
            "(e.g., `sample1: 60000`). Common: `sample1`, `sample2`, `antigen`, `PBS`."
        )

        manual_plate_data = render_manual_plate_editor(st, "manual", initial_for_editor)
        parsed_manual_plate = parse_manual_plate_data(manual_plate_data)

    st.divider()
    st.subheader("4. Run Protocol")

    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        generate_btn = st.button(
            "🚀 Generate Protocol",
            type="primary",
            width="stretch",
            help="Run the preprocessing workflow and produce the source plate, protocol CSV, and review files.",
        )

    if "last_run_result" not in st.session_state:
        st.session_state["last_run_result"] = None

    if generate_btn:
        if plate_mode == PLATE_MODE_PREMADE and not selected_plate_name:
            st.error("❌ Select a premade plate before running the workflow.")
        elif plate_mode == PLATE_MODE_PREMADE and not parsed_premade_plate:
            st.error("❌ Define at least one well in the premade source plate before running.")
        elif plate_mode == PLATE_MODE_MANUAL and not parsed_manual_plate:
            st.error("❌ Define at least one well in the source plate before running.")
        else:
            st.info(f"📋 Running workflow: {WORKFLOW_NAME}")
            st.info(f"Plate mode: {plate_mode}")
            if plate_mode == PLATE_MODE_PREMADE:
                st.info(f"Selected premade plate: {selected_plate_name}")
                st.info(f"Editable wells: {len(parsed_premade_plate)}")
            else:
                st.info(f"Defined wells: {len(parsed_manual_plate)}")

            source_plate_for_run = (
                parsed_premade_plate
                if plate_mode == PLATE_MODE_PREMADE
                else parsed_manual_plate
                if plate_mode == PLATE_MODE_MANUAL
                else None
            )

            request = PreprocessingRequest(
                experiment_name=experiment_name,
                plate_mode=plate_mode,
                premade_plate_name=selected_plate_name,
                new_plate_label=None,
                doses=doses,
                doses2=doses2,
                highest_dose=highest_dose,
                vol_cellextract=vol_cellextract,
                vol_antigen=vol_antigen,
                samples=parse_samples(samples),
                manual_source_plate=source_plate_for_run,
            )

            try:
                start_time = perf_counter()
                with st.spinner("Running preprocessing workflow..."):
                    result = run_echo_protocol_preprocessing(request)
                run_duration_seconds = perf_counter() - start_time
            except NotImplementedError as exc:
                st.warning(str(exc))
                st.info(
                    "Premade plate runs can already be validated against the committed Plate A and "
                    "Plate B fixtures. Manual source plate runs use the built-in Python workflow."
                )
            except Exception as exc:
                st.error(f"Preprocessing failed: {exc}")
            else:
                st.session_state["last_run_result"] = {
                    "experiment_name": experiment_name,
                    "plate_mode": plate_mode,
                    "premade_plate_name": selected_plate_name,
                    "manual_well_count": len(parsed_premade_plate)
                    if plate_mode == PLATE_MODE_PREMADE
                    else len(parsed_manual_plate)
                    if plate_mode == PLATE_MODE_MANUAL
                    else None,
                    "doses": doses,
                    "doses2": doses2,
                    "highest_dose": highest_dose,
                    "vol_cellextract": vol_cellextract,
                    "vol_antigen": vol_antigen,
                    "samples": samples,
                    "execution_mode": result.execution_mode,
                    "output_dir": str(result.output_dir),
                    "protocol_csv": str(result.protocol_csv)
                    if result.protocol_csv
                    else None,
                    "destination_composition_csv": str(
                        result.destination_composition_csv
                    )
                    if result.destination_composition_csv
                    else None,
                    "source_plate_csv": str(result.source_plate_csv)
                    if result.source_plate_csv
                    else None,
                    "run_manifest_json": str(result.run_manifest_json),
                    "completed_at": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                    "run_duration": format_duration(run_duration_seconds),
                }
                st.success("Preprocessing run completed.")

    last_run_result = st.session_state.get("last_run_result")
    if last_run_result:
        st.divider()
        st.subheader("Latest Run Output")
        st.success(
            f"Protocol run completed at {last_run_result['completed_at']} in {last_run_result['run_duration']}. Review the results below and download the files when you're ready."
        )
        st.caption(
            f"Execution mode: `{last_run_result['execution_mode']}`. Review the generated source plate "
            "and protocol together before downloading the final files."
        )
        st.code(last_run_result["output_dir"])

        render_setup_summary(
            st,
            "Run Setup",
            build_setup_summary_rows(
                plate_mode=last_run_result["plate_mode"],
                experiment_name=last_run_result["experiment_name"],
                premade_plate_name=last_run_result.get("premade_plate_name"),
                manual_well_count=last_run_result.get("manual_well_count"),
                doses=last_run_result["doses"],
                doses2=last_run_result["doses2"],
                highest_dose=last_run_result["highest_dose"],
                vol_cellextract=last_run_result["vol_cellextract"],
                vol_antigen=last_run_result["vol_antigen"],
                samples=last_run_result["samples"],
            ),
        )

        generated_source_plate = last_run_result.get("source_plate_csv")
        generated_protocol = last_run_result.get("protocol_csv")

        if generated_source_plate and generated_protocol:
            render_source_plate_panel(st, generated_source_plate, "Source Plate")
            st.markdown("**Protocol Validation Output**")
            render_protocol_panel(
                st,
                generated_protocol,
                "Protocol Validation Preview",
                source_plate_path=generated_source_plate,
            )
        else:
            st.info(
                "This run finished without both generated plate and protocol artifacts, so only the "
                "downloadable files are shown below."
            )

        output_files = [
            (
                "Echo Protocol CSV",
                "Robot-ready transfer instructions for the Echo run.",
                last_run_result.get("protocol_csv"),
            ),
            (
                "Source Plate CSV",
                "The source plate layout used for this run.",
                last_run_result.get("source_plate_csv"),
            ),
            (
                "Destination Composition CSV",
                "A review table showing what landed in each destination well.",
                last_run_result.get("destination_composition_csv"),
            ),
            (
                "Run Manifest JSON",
                "A machine-readable record of the parameters used for this run.",
                last_run_result.get("run_manifest_json"),
            ),
        ]
        render_download_artifacts(st, output_files)


if __name__ == "__main__":
    main()
