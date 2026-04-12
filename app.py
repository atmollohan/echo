"""
Echo Protocol - Web UI.

A Streamlit app for generating Beckman Echo liquid handler protocols.
"""

from __future__ import annotations

from echo_run.backend import (
    DEFAULT_CONFIG,
    build_echo_protocol_summary,
    build_source_plate_summary,
    get_source_plate_map_paths,
    load_echo_protocol,
    load_source_plate_map,
    parse_plate_entry,
)
from echo_run.preprocessing import (
    PLATE_MODE_NEW,
    PLATE_MODE_PREMADE,
    PLATE_MODE_MANUAL,
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


def get_plate_wells():
    """Return list of 384 well positions A1-P24."""
    rows = list("ABCDEFGHIJKLMNOP")
    cols = list(range(1, 25))
    return [f"{r}{c}" for r in rows for c in cols]


def render_manual_plate_editor(st, key_prefix: str = "manual"):
    """Render an editable 384-well plate grid using data editor."""
    st.caption("Edit wells below. Format: `name: volume` (e.g., `sample1: 60000`). Empty = no data.")

    if f"{key_prefix}_plate_data" not in st.session_state:
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

    columns = ["Well"] + [str(c) for c in cols]

    edited = st.data_editor(
        grid_data,
        column_config={
            "Well": st.column_config.TextColumn("Row", width="small", disabled=True),
            **{str(c): st.column_config.TextColumn(str(c), width="small") for c in cols},
        },
        hide_index=True,
        num_rows="fixed",
        key=f"{key_prefix}_editor",
        use_container_width=True,
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

    return (
        plate_map.style
        .map(style_cell)
        .set_properties(**{"text-align": "center", "white-space": "nowrap"})
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
        metric_grid.style
        .map(style_cell)
        .format("{:,.0f}")
        .set_properties(**{"text-align": "center", "white-space": "nowrap"})
    )


def style_composition_plate_grid(composition_grid, component_count_grid, max_components: int):
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
        composition_grid.style
        .map(style_cell)
        .apply(style_from_counts, axis=0)
        .set_properties(**{"white-space": "pre-line", "text-align": "left", "vertical-align": "top"})
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
    new_plate_label: str | None = None,
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
        rows.append(("New plate label", new_plate_label or "n/a"))

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


def render_setup_summary(st, heading: str, rows: list[tuple[str, object]], caption: str | None = None):
    """Render a compact setup summary table."""
    st.markdown(f"**{heading}**")
    if caption:
        st.caption(caption)
    st.table(
        {
            "Setting": [label for label, _value in rows],
            "Value": [value for _label, value in rows],
        }
    )


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
    st.caption("Cells are colored by substance. Darker fills indicate larger loaded volumes.")


def render_protocol_panel(st, protocol_path, heading: str):
    """Render a protocol preview focused on validation-oriented review."""
    st.markdown(f"**{heading}**")
    protocol_df = load_echo_protocol(protocol_path)
    summary = build_echo_protocol_summary(protocol_df)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric("Transfers", f"{summary['transfer_count']:,}")
    with metric_col2:
        st.metric("Samples", summary["sample_count"])
    with metric_col3:
        st.metric("Source Wells Used", summary["source_well_count"])
    with metric_col4:
        st.metric("Destination Wells Used", summary["destination_well_count"])

    st.caption(f"Total transferred volume in this protocol: {summary['total_transfer_volume_nl']:,} nL")

    st.markdown("**Destination well composition**")
    st.dataframe(
        style_composition_plate_grid(
            summary["destination_composition_grid"],
            summary["destination_component_count_grid"],
            summary["destination_max_components"],
        ),
        width="stretch",
        height=420,
    )
    st.caption("Each cell shows which sample/source components contribute to that destination well.")

    max_transfer_count = 0
    if not summary["destination_count_grid"].empty:
        max_transfer_count = int(summary["destination_count_grid"].to_numpy().max())
    st.markdown("**Destination plate transfer count per well**")
    st.dataframe(
        style_numeric_plate_grid(
            summary["destination_count_grid"],
            max_transfer_count,
            "#2563eb",
        ),
        width="stretch",
        height=420,
    )
    st.caption("This view shows how many individual transfers landed in each destination well.")

    st.info(
        "Use the destination composition map to see what each well contains, and the transfer-count "
        "view to spot dense layouts before sending the protocol forward."
    )


def main():
    import streamlit as st

    st.set_page_config(
        page_title="Echo Protocol",
        page_icon="🔬",
        layout="wide",
    )

    st.title("🔬 Echo Protocol")
    st.markdown(
        "Generate Beckman Echo liquid handler protocols without writing code. "
        "Define your source plate and experiment parameters, then export ready-to-run CSV transfer files."
    )
    st.caption("💡 Tip: Use a premade plate for quick experiments, or define a new plate manually for custom layouts.")

    uploaded_values = DEFAULT_CONFIG.copy()
    source_plate_paths = get_source_plate_map_paths()
    source_plate_options = [path.name for path in source_plate_paths]

    st.subheader("1. Experiment Parameters")
    col1, col2 = st.columns(2)

    with col1:
        experiment_name = st.text_input(
            "Experiment Name",
            value=uploaded_values["experiment_name"],
            help="Used in output filenames.",
        )
        doses = st.number_input(
            "Number of Doses",
            min_value=1,
            max_value=24,
            value=uploaded_values["doses"],
            help="Number of doses per sample.",
        )
        doses2 = st.number_input(
            "Number of Doses (Second Curve)",
            min_value=0,
            max_value=24,
            value=uploaded_values["doses2"],
            help="Number of points in the second antigen dose curve.",
        )
        highest_dose = st.number_input(
            "Highest Dose (µM)",
            min_value=0.1,
            max_value=100.0,
            value=uploaded_values["highest_dose"],
            step=0.1,
            help="Highest dose concentration in micromolar.",
        )

    with col2:
        vol_cellextract = st.number_input(
            "Sample Volume (nL)",
            min_value=1,
            max_value=100000,
            value=uploaded_values["vol_cellextract"],
            help="Volume of sample to transfer to each destination well.",
        )
        vol_antigen = st.number_input(
            "Reagent Volume (nL)",
            min_value=0,
            max_value=100000,
            value=uploaded_values["vol_antigen"],
            help="Volume of reagent (antigen/PBS) to transfer.",
        )
        samples = st.text_input(
            "Sample Names",
            value=uploaded_values["samples"],
            help="Comma-separated list of sample names.",
        )

    st.subheader("2. Plate Setup")
    workflow_col1, workflow_col2 = st.columns([1.2, 1])
    with workflow_col1:
        plate_mode = st.radio(
            "Plate source",
            [PLATE_MODE_PREMADE, PLATE_MODE_MANUAL],
            help="Choose an existing plate or define manually.",
        )

    with workflow_col2:
        if plate_mode == PLATE_MODE_PREMADE:
            selected_plate_name = None
            new_plate_name = None
            if source_plate_options:
                selected_plate_name = st.selectbox(
                    "Premade plate",
                    source_plate_options,
                    help="Choose a committed plate layout.",
                )
            else:
                st.warning("No premade source plates available.")
        else:
            selected_plate_name = None
            new_plate_name = None

    if plate_mode == PLATE_MODE_MANUAL:
        st.subheader("3. Define Source Plate")
        st.markdown(
            "Enter substances and volumes for each well. Format: `name: volume` "
            "(e.g., `sample1: 60000`). Common: `sample1`, `sample2`, `antigen`, `PBS`."
        )
        manual_plate_data = render_manual_plate_editor(st, "manual")
        parsed_manual_plate = parse_manual_plate_data(manual_plate_data)
    else:
        parsed_manual_plate = None

    st.divider()
    with st.expander("Reference Workflow Preview", expanded=False):
        if plate_mode == PLATE_MODE_PREMADE and selected_plate_name:
            st.caption(
                "This paired reference view shows the selected premade source plate and the historical "
                "protocol it should produce. Use it to understand the workflow before you run the current experiment."
            )

            selected_source_path = next((path for path in source_plate_paths if path.name == selected_plate_name), None)
            try:
                _, selected_protocol_path = build_fixture_pair(selected_plate_name)
            except (FileNotFoundError, FileExistsError) as exc:
                selected_protocol_path = None
                st.warning(str(exc))

            render_setup_summary(
                st,
                "Reference Setup",
                build_setup_summary_rows(
                    plate_mode=plate_mode,
                    experiment_name=experiment_name,
                    premade_plate_name=selected_plate_name,
                    doses=doses,
                    doses2=doses2,
                    highest_dose=highest_dose,
                    vol_cellextract=vol_cellextract,
                    vol_antigen=vol_antigen,
                    samples=samples,
                ),
                caption="These are the current run inputs for the selected premade workflow.",
            )

            if selected_source_path and selected_protocol_path:
                render_source_plate_panel(st, selected_source_path, "Reference Source Plate")
                st.markdown("**Reference Validation Output**")
                render_protocol_panel(st, selected_protocol_path, "Historical Protocol Output")
            elif selected_source_path:
                render_source_plate_panel(st, selected_source_path, "Reference Source Plate")
        elif plate_mode == PLATE_MODE_PREMADE:
            st.info("Select a premade plate to see the paired source-plate and reference-protocol preview.")
        else:
            st.info(
                "Reference source/protocol previews are available for the committed premade plate cases. "
                "Generated outputs for new plates will appear after the workflow runs."
            )

    with st.expander("Open Workflow Questions", expanded=False):
        st.markdown(
            "\n".join(
                [
                    "1. If the user chooses a premade plate, what information do they need to specify besides the plate itself: experiment type, sample list, concentrations, replicate pattern, or destination layout?",
                    "2. If the user chooses to create a new plate from scratch, what are the minimum inputs required to build that plate correctly without opening the notebook?",
                    "3. Beyond the reference source plate and setup summary, what else should be previewed before a run?",
                    "4. Which errors or warnings would be most valuable to catch automatically before a grad student sends the protocol to the robot?",
                    "5. For repeated experiments, would users prefer to clone a previous run, start from a saved preset, or reuse a premade plate with just a few parameter changes?",
                    "6. What would make this feel like a trustworthy lab product rather than a notebook wrapper: guided steps, plain-language labels, audit trails, downloadable summaries, or stronger validation?",
                ]
            )
        )

    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        generate_btn = st.button("🚀 Generate Protocol", type="primary", width="stretch")

    if "last_run_result" not in st.session_state:
        st.session_state["last_run_result"] = None

    if generate_btn:
        if plate_mode == PLATE_MODE_PREMADE and not selected_plate_name:
            st.error("❌ Select a premade plate before running the workflow.")
        elif plate_mode == PLATE_MODE_MANUAL and not parsed_manual_plate:
            st.error("❌ Define at least one well in the source plate before running.")
        else:
            st.info(f"📋 Running workflow: {WORKFLOW_NAME}")
            st.info(f"Plate mode: {plate_mode}")
            if plate_mode == PLATE_MODE_PREMADE:
                st.info(f"Selected premade plate: {selected_plate_name}")
            elif plate_mode == PLATE_MODE_NEW:
                st.info(f"New plate label: {new_plate_name}")
            else:
                st.info(f"Defined wells: {len(parsed_manual_plate)}")

            request = PreprocessingRequest(
                experiment_name=experiment_name,
                plate_mode=plate_mode,
                premade_plate_name=selected_plate_name,
                new_plate_label=new_plate_name if plate_mode == PLATE_MODE_NEW else None,
                doses=doses,
                doses2=doses2,
                highest_dose=highest_dose,
                vol_cellextract=vol_cellextract,
                vol_antigen=vol_antigen,
                samples=parse_samples(samples),
                manual_source_plate=parsed_manual_plate if plate_mode == PLATE_MODE_MANUAL else None,
            )

            try:
                with st.spinner("Running preprocessing workflow..."):
                    result = run_echo_protocol_preprocessing(request)
            except NotImplementedError as exc:
                st.warning(str(exc))
                st.info(
                    "Premade plate runs can already be validated against the committed Plate A and "
                    "Plate B fixtures. New plate generation will work once the custom preprocessing "
                    "notebook or Python implementation is connected."
                )
            except Exception as exc:
                st.error(f"Preprocessing failed: {exc}")
            else:
                st.session_state["last_run_result"] = {
                    "experiment_name": experiment_name,
                    "plate_mode": plate_mode,
                    "premade_plate_name": selected_plate_name,
                    "new_plate_label": new_plate_name if plate_mode == PLATE_MODE_NEW else None,
                    "doses": doses,
                    "doses2": doses2,
                    "highest_dose": highest_dose,
                    "vol_cellextract": vol_cellextract,
                    "vol_antigen": vol_antigen,
                    "samples": samples,
                    "execution_mode": result.execution_mode,
                    "output_dir": str(result.output_dir),
                    "protocol_csv": str(result.protocol_csv) if result.protocol_csv else None,
                    "destination_composition_csv": str(result.destination_composition_csv) if result.destination_composition_csv else None,
                    "source_plate_csv": str(result.source_plate_csv) if result.source_plate_csv else None,
                    "run_manifest_json": str(result.run_manifest_json),
                }
                st.success("Preprocessing run completed.")

    last_run_result = st.session_state.get("last_run_result")
    if last_run_result:
        st.divider()
        st.subheader("Latest Run Output")
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
                new_plate_label=last_run_result.get("new_plate_label"),
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
            render_source_plate_panel(st, generated_source_plate, "Generated Source Plate")
            st.markdown("**Generated Validation Output**")
            render_protocol_panel(st, generated_protocol, "Generated Protocol Validation Preview")
        else:
            st.info(
                "This run finished without both generated plate and protocol artifacts, so only the "
                "downloadable files are shown below."
            )

        st.markdown("**Download run artifacts**")
        output_files = [
            ("Echo Protocol CSV", last_run_result.get("protocol_csv")),
            ("Destination Composition CSV", last_run_result.get("destination_composition_csv")),
            ("Source Plate CSV", last_run_result.get("source_plate_csv")),
            ("Run Manifest JSON", last_run_result.get("run_manifest_json")),
        ]
        for label, raw_path in output_files:
            if not raw_path:
                continue
            from pathlib import Path

            path = Path(raw_path)
            if path.exists():
                st.write(f"{label}: `{path.name}`")
                st.download_button(
                    f"Download {label}",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime="text/csv" if path.suffix == ".csv" else "application/json",
                )


if __name__ == "__main__":
    main()
