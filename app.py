"""
Echo Protocol - Web UI.

A Streamlit app for generating Beckman Echo liquid handler protocols.
"""

from __future__ import annotations

from echo_run.backend import (
    DEFAULT_CONFIG,
    build_echo_protocol_summary,
    build_source_plate_summary,
    get_echo_protocol_paths,
    get_source_plate_map_paths,
    load_echo_protocol,
    load_source_plate_map,
    parse_plate_entry,
)
from echo_run.preprocessing import (
    PLATE_MODE_NEW,
    PLATE_MODE_PREMADE,
    PreprocessingRequest,
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


def prioritize_selected_path(paths, selected_name: str | None):
    """Move the selected path to the front so it opens first in the UI."""
    if not selected_name:
        return paths

    selected = [path for path in paths if path.name == selected_name]
    remainder = [path for path in paths if path.name != selected_name]
    return selected + remainder


def main():
    import streamlit as st

    st.set_page_config(
        page_title="Echo Protocol",
        page_icon="🔬",
        layout="wide",
    )

    st.title("🔬 Echo Protocol")
    st.markdown(
        "Set up the preprocessing workflow, choose whether you are reusing a premade plate or "
        "building a new one, and preview the committed plate/protocol examples in the repo."
    )

    setup_col1, setup_col2 = st.columns(2)
    with setup_col1:
        st.success(
            "**Fixed Workflow**\n\n"
            "This screen is now focused on a single preprocessing workflow: "
            f"`{WORKFLOW_NAME}`."
        )
    with setup_col2:
        st.info(
            "**Main Decision**\n\n"
            "Tell the app whether you already have a premade plate or need to create a new one "
            "from scratch."
        )

    uploaded_values = DEFAULT_CONFIG.copy()
    source_plate_paths = get_source_plate_map_paths()
    source_plate_options = [path.name for path in source_plate_paths]
    default_plate_name = source_plate_options[0] if source_plate_options else None

    st.subheader("Workflow Setup")
    st.caption(f"Target workflow: `{WORKFLOW_NAME}`")
    workflow_col1, workflow_col2 = st.columns([1.2, 1])
    with workflow_col1:
        plate_mode = st.radio(
            "Plate starting point",
            [PLATE_MODE_PREMADE, PLATE_MODE_NEW],
            help="Choose whether the run should start from an existing prepared plate or build a new source plate layout.",
        )

    with workflow_col2:
        if plate_mode == PLATE_MODE_PREMADE:
            if source_plate_options:
                selected_plate_name = st.selectbox(
                    "Premade plate to use",
                    source_plate_options,
                    help="Choose which committed plate layout best matches the premade plate you want to run.",
                )
            else:
                selected_plate_name = None
                st.warning("No premade source plate CSVs are available in `data/raw`.")
        else:
            selected_plate_name = None
            new_plate_name = st.text_input(
                "New plate label",
                value="new_source_plate",
                help="A short label for the new plate you want the preprocessing step to build.",
            )
            st.caption(
                "Use the parameter form below to describe the new run. The preprocessing workflow "
                "should eventually build both the protocol CSV and the companion visualization CSVs."
            )

    st.subheader("Experiment Parameters")
    st.caption(f"Fixed workflow notebook: `{WORKFLOW_NAME}`")
    st.info(
        "For now, this product is assuming a single preprocessing notebook fed by form inputs and "
        "the plate mode above, instead of asking the user to choose among multiple notebooks."
    )

    col1, col2 = st.columns(2)

    with col1:
        experiment_name = st.text_input(
            "Experiment Name",
            value=uploaded_values["experiment_name"],
            help="Used in output filenames once notebook execution is wired up.",
        )
        doses = st.number_input(
            "Number of Doses",
            min_value=1,
            max_value=24,
            value=uploaded_values["doses"],
            help="Number of points in the main dose curve.",
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
            "Cell Extract Volume (nL)",
            min_value=1,
            max_value=100000,
            value=uploaded_values["vol_cellextract"],
            help="Volume of cell extract per well in nanoliters.",
        )
        vol_antigen = st.number_input(
            "Antigen Volume (nL)",
            min_value=1,
            max_value=100000,
            value=uploaded_values["vol_antigen"],
            help="Volume of antigen per well in nanoliters.",
        )
        samples = st.text_input(
            "Sample Names",
            value=uploaded_values["samples"],
            help="Comma-separated list of sample names.",
        )

    st.divider()
    st.subheader("Sample Source Plate Maps")
    st.caption(
        "These committed source plate CSVs show how the repo currently arranges reagents and test "
        "materials across a 384-well source plate. Each colored cell represents a loaded well."
    )

    if source_plate_paths:
        ordered_source_paths = prioritize_selected_path(source_plate_paths, selected_plate_name)
        plate_tabs = st.tabs([path.stem.replace("_", " ") for path in ordered_source_paths])
        for tab, source_plate_path in zip(plate_tabs, ordered_source_paths):
            with tab:
                plate_map = load_source_plate_map(source_plate_path)
                summary = build_source_plate_summary(plate_map)

                map_col, summary_col = st.columns([2.2, 1])
                with map_col:
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

                with summary_col:
                    metric_col1, metric_col2 = st.columns(2)
                    with metric_col1:
                        st.metric("Occupied Wells", summary["occupied_wells"])
                        st.metric("Substances", len(summary["substances"]))
                    with metric_col2:
                        st.metric("Empty Wells", summary["empty_wells"])
                        st.metric(
                            "Max Volume",
                            f"{summary['max_volume_nl']:,} nL" if summary["max_volume_nl"] else "n/a",
                        )

                    if summary["substances"]:
                        st.markdown("**Loaded materials**")
                        st.write(", ".join(summary["substances"]))
                    else:
                        st.info("No loaded wells were detected in this plate map.")
    else:
        st.info("No committed source plate CSVs were found under `data/raw`.")

    st.divider()
    st.subheader("Committed Echo Protocol Maps")
    st.caption(
        "These protocol CSVs show the transfer plan generated from the current notebook workflows. "
        "They help explain which destination wells receive material and which source wells are used most heavily."
    )

    echo_protocol_paths = get_echo_protocol_paths()
    if echo_protocol_paths:
        protocol_tabs = st.tabs([path.stem.replace("_", " ") for path in echo_protocol_paths])
        for tab, protocol_path in zip(protocol_tabs, echo_protocol_paths):
            with tab:
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

                st.caption(
                    f"Total transferred volume in this protocol: {summary['total_transfer_volume_nl']:,} nL"
                )

                preview_col1, preview_col2 = st.columns(2)
                with preview_col1:
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
                    st.caption(
                        "Each cell shows which sample/source components contribute to that destination well."
                    )

                with preview_col2:
                    st.markdown("**Destination plate transfer count per well**")
                    st.dataframe(
                        style_numeric_plate_grid(
                            summary["destination_count_grid"],
                            int(summary["destination_count_grid"].to_numpy().max()),
                            "#2563eb",
                        ),
                        width="stretch",
                        height=420,
                    )
                    st.caption("This view shows how many individual transfers landed in each destination well.")

                st.markdown("**How to read this protocol view**")
                st.info(
                    "Use the destination composition map to see what each well contains, and the "
                    "transfer-count view to spot dense layouts before sending the protocol forward."
                )
    else:
        st.info("No committed Echo protocol CSVs were found under `data/raw`.")

    st.divider()
    st.subheader("Questions To Shape The Product Workflow")
    st.markdown(
        "\n".join(
            [
                "1. When a user opens the product, should the very first choice always be `premade plate` versus `create a new plate`, or is there an earlier decision we should capture first?",
                "2. If the user chooses a premade plate, what information do they need to specify besides the plate itself: experiment type, sample list, concentrations, replicate pattern, or destination layout?",
                "3. If the user chooses to create a new plate from scratch, what are the minimum inputs required to build that plate correctly without opening the notebook?",
                "4. Before the user clicks Run, what exact previews or checks would make them confident enough to trust the preprocessing step?",
                "5. After Run, what deliverables should the product always create: the Echo protocol CSV, a source plate CSV, a destination composition CSV, a validation summary, or something else?",
                "6. Which errors or warnings would be most valuable to catch automatically before a grad student sends the protocol to the robot?",
                "7. For repeated experiments, would users prefer to clone a previous run, start from a saved preset, or reuse a premade plate with just a few parameter changes?",
                "8. What would make this feel like a trustworthy lab product rather than a notebook wrapper: guided steps, plain-language labels, audit trails, downloadable summaries, or stronger validation?",
            ]
        )
    )

    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        generate_btn = st.button("🚀 Generate Protocol", type="primary", width="stretch")

    if generate_btn:
        if plate_mode == PLATE_MODE_PREMADE and not selected_plate_name:
            st.error("❌ Select a premade plate before running the workflow.")
        else:
            st.info(f"📋 Running workflow: {WORKFLOW_NAME}")
            st.info(f"Plate mode: {plate_mode}")
            if plate_mode == PLATE_MODE_PREMADE:
                st.info(f"Selected premade plate: {selected_plate_name}")
            else:
                st.info(f"New plate label: {new_plate_name}")

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
                st.success("Preprocessing run completed.")
                st.caption(f"Execution mode: {result.execution_mode}")
                st.code(str(result.output_dir))
                st.markdown(
                    """
                    **Expected preprocessing outputs for this workflow are:**
                    - an Echo protocol CSV
                    - a destination composition CSV for validation and visualization
                    - a source plate CSV and run manifest for auditability
                    """
                )

                output_files = [
                    ("Echo Protocol CSV", result.protocol_csv),
                    ("Destination Composition CSV", result.destination_composition_csv),
                    ("Source Plate CSV", result.source_plate_csv),
                    ("Run Manifest JSON", result.run_manifest_json),
                ]
                for label, path in output_files:
                    if path and path.exists():
                        st.write(f"{label}: `{path.name}`")
                        st.download_button(
                            f"Download {label}",
                            data=path.read_bytes(),
                            file_name=path.name,
                            mime="text/csv" if path.suffix == ".csv" else "application/json",
                        )


if __name__ == "__main__":
    main()
