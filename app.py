"""
Echo Lab Protocol Generator - Web UI
A Streamlit app for generating Beckman Echo liquid handler protocols.
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path

st.set_page_config(
    page_title="Echo Lab Protocol Generator",
    page_icon="🔬",
    layout="wide"
)

NOTEBOOKS_DIR = Path("notebooks")
DATA_DIR = Path("data")

def get_notebooks():
    """Get list of available notebooks."""
    if not NOTEBOOKS_DIR.exists():
        return []
    return [f.name for f in NOTEBOOKS_DIR.glob("*.ipynb") if not f.name.endswith("-checkpoint.ipynb")]

def load_config_from_file(uploaded_file):
    """Load config from uploaded INI file."""
    import configparser
    config = configparser.ConfigParser()
    config.read_string(uploaded_file.getvalue().decode("utf-8"))
    return config

def main():
    st.title("🔬 Echo Lab Protocol Generator")
    st.markdown("Generate Beckman Echo liquid handler protocols from experiment parameters.")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Config file uploader
        uploaded_config = st.file_uploader(
            "Upload config file (.ini)", 
            type=["ini", "cfg", "txt"],
            help="Upload an INI config file or manually enter parameters below"
        )
        
        notebook_options = get_notebooks()
        selected_notebook = st.selectbox(
            "Select Notebook",
            notebook_options if notebook_options else ["No notebooks found"],
            help="Choose which notebook to run for protocol generation"
        )
        
        st.divider()
        st.info("💡 Tip: You can edit parameters manually below or upload a config file.")

    # Main form for experiment parameters
    st.subheader("Experiment Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        experiment_name = st.text_input("Experiment Name", value="my_experiment", help="Used in output filename")
        doses = st.number_input("Number of Doses", min_value=1, max_value=24, value=6, help="Number of points in dose curve")
        doses2 = st.number_input("Number of Doses (Second Curve)", min_value=0, max_value=24, value=3, help="Number of points in second antigen dose curve")
        highest_dose = st.number_input("Highest Dose (µM)", min_value=0.1, max_value=100.0, value=4.0, step=0.1, help="Highest dose concentration in micromolar")
    
    with col2:
        vol_cellextract = st.number_input("Cell Extract Volume (nL)", min_value=1, max_value=100000, value=2000, help="Volume of cell extract per well in nanoliters")
        vol_antigen = st.number_input("Antigen Volume (nL)", min_value=1, max_value=100000, value=2000, help="Volume of antigen per well in nanoliters")
        samples = st.text_input("Sample Names", value="sample1,sample2,sample3", help="Comma-separated list of sample names")

    # If config file uploaded, show override option
    if uploaded_config is not None:
        st.success(f"✅ Config file loaded: {uploaded_config.name}")
        
        # Parse and show loaded values (non-editable for now - v1 simple)
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read_string(uploaded_config.getvalue().decode("utf-8"))
            if config.has_section('experiment'):
                st.caption("Loaded from file:")
                for key, val in config['experiment'].items():
                    st.caption(f"  {key} = {val}")
        except Exception as e:
            st.warning(f"Could not parse config: {e}")

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
            
            # Progress indicator (placeholder for now - notebook execution in Phase 2)
            with st.spinner("Running experiment..."):
                import time
                time.sleep(1)  # Simulate work
                
            st.success("✅ Protocol generated successfully!")
            
            # Show sample output (placeholder)
            st.subheader("Output Files")
            st.info("Output CSV files would appear here after Phase 2 implementation.")
            
            # Show what would be generated
            st.markdown("""
            **Generated files would include:**
            - `setup_source_{experiment_name}.csv` - Source plate layout
            - `setup_dest_{experiment_name}.csv` - Destination plate protocol
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