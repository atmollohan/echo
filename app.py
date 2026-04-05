"""
Echo Lab Protocol Generator - Web UI
A Streamlit app for generating Beckman Echo liquid handler protocols.
"""

from echo_run.backend import DEFAULT_CONFIG, get_notebooks, parse_uploaded_config

def main():
    import streamlit as st

    st.set_page_config(
        page_title="Echo Lab Protocol Generator",
        page_icon="🔬",
        layout="wide"
    )

    st.title("🔬 Echo Lab Protocol Generator")
    st.markdown(
        "Configure experiment parameters, inspect available notebooks, and preview the current "
        "protocol-generation workflow."
    )

    # Sidebar for configuration
    uploaded_values = DEFAULT_CONFIG.copy()
    uploaded_notebook = None
    uploaded_config_name = None
    upload_error = None

    with st.sidebar:
        st.header("Configuration")

        notebook_options = get_notebooks()
        default_notebook_index = 0
        selected_notebook = st.selectbox(
            "Select Notebook",
            notebook_options if notebook_options else ["No notebooks found"],
            index=default_notebook_index,
            help="Choose which notebook template or workflow to use first"
        )

        st.divider()
        st.subheader("Notebook Config")

        uploaded_config = st.file_uploader(
            "Upload config file (.ini)",
            type=["ini", "cfg", "txt"],
            help="Upload an INI config file after choosing a notebook",
        )

        if uploaded_config is not None:
            uploaded_config_name = uploaded_config.name
            try:
                uploaded_values, uploaded_notebook = parse_uploaded_config(uploaded_config)
                if notebook_options and uploaded_notebook in notebook_options:
                    selected_notebook = uploaded_notebook
            except Exception as exc:
                upload_error = str(exc)

        st.divider()
        st.info(
            "Workflow tip: choose a notebook first, then load the config that belongs to "
            "that notebook."
        )

    # Main form for experiment parameters
    st.subheader("Experiment Parameters")
    st.caption(f"Selected notebook: {selected_notebook}")
    st.info(
        "Current notebooks are still mostly self-contained templates. Core dose and volume fields "
        "line up better than `Experiment Name` or `Sample Names`, which are not yet used by every "
        "notebook."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        experiment_name = st.text_input("Experiment Name", value=uploaded_values["experiment_name"], help="Used in output filename")
        doses = st.number_input("Number of Doses", min_value=1, max_value=24, value=uploaded_values["doses"], help="Number of points in dose curve")
        doses2 = st.number_input("Number of Doses (Second Curve)", min_value=0, max_value=24, value=uploaded_values["doses2"], help="Number of points in second antigen dose curve")
        highest_dose = st.number_input("Highest Dose (µM)", min_value=0.1, max_value=100.0, value=uploaded_values["highest_dose"], step=0.1, help="Highest dose concentration in micromolar")
    
    with col2:
        vol_cellextract = st.number_input("Cell Extract Volume (nL)", min_value=1, max_value=100000, value=uploaded_values["vol_cellextract"], help="Volume of cell extract per well in nanoliters")
        vol_antigen = st.number_input("Antigen Volume (nL)", min_value=1, max_value=100000, value=uploaded_values["vol_antigen"], help="Volume of antigen per well in nanoliters")
        samples = st.text_input("Sample Names", value=uploaded_values["samples"], help="Comma-separated list of sample names")

    # If config file uploaded, show override option
    if uploaded_config is not None:
        if upload_error:
            st.warning(f"Could not parse config: {upload_error}")
        else:
            st.success(f"Config file loaded: {uploaded_config_name}")
            st.caption("Form fields were pre-populated from the uploaded config.")

    st.divider()
    
    # Generate button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        generate_btn = st.button("🚀 Generate Protocol", type="primary", use_container_width=True)

    if generate_btn:
        if not selected_notebook or selected_notebook == "No notebooks found":
            st.error("❌ No notebook selected. Please select a notebook first.")
        else:
            st.info(f"📋 Running notebook: {selected_notebook}")
            
            # Protocol execution is still being wired up; keep the UI honest for now.
            with st.spinner("Running experiment..."):
                import time
                time.sleep(1)  # Simulate work
                
            st.warning("Notebook execution is not implemented yet in the Streamlit app.")
            
            st.subheader("Current Status")
            st.info(
                "The web UI is ready for configuration and notebook selection, but the Generate "
                "button is still a placeholder until notebook execution is connected."
            )
            
            # Show what the current notebook workflows have historically produced.
            st.markdown("""
            **Historical notebook outputs in this repo include:**
            - source plate map CSVs such as `20240813_ML_L1_source_plateA.csv`
            - Echo protocol CSVs such as `20240813_ML_L1_echo_protocol_plateA.csv`
            """)
    
    # Show existing notebooks info
    if notebook_options:
        with st.expander("📚 Available Notebooks"):
            for nb in notebook_options:
                st.write(f"- {nb}")
    else:
        st.warning("⚠️ No notebooks found in the notebooks/ directory")

if __name__ == "__main__":
    main()
