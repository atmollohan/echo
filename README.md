# Echo Lab Protocol Generator

A user-friendly web application for generating Beckman Echo liquid handler protocols. Designed for lab scientists who aren't coders: configure experiments via a simple form or config file, inspect the available notebook workflows, and prepare for CSV protocol generation without editing notebook code.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build the container
docker build -t echo-run .

# Run the web interface
docker run -p 8501:8501 echo-run
```

Then open http://localhost:8501 in your browser.

### Docker with Local Notebook/Data Folders

If your user keeps working files in a separate folder on their machine, mount those directories into
the container and point the app at them with environment variables.

Example host workspace:

```text
~/echo-work/
├── notebooks/
└── data/
```

Run the container with mounted folders:

```bash
docker run -p 8501:8501 \
  -v ~/echo-work/notebooks:/workspace/notebooks \
  -v ~/echo-work/data:/workspace/data \
  -e ECHO_NOTEBOOKS_DIR=/workspace/notebooks \
  -e ECHO_DATA_DIR=/workspace/data \
  echo-run
```

This lets her copy notebooks and CSV data in and out of `~/echo-work` without rebuilding the image.
The containerized app will read notebooks from `ECHO_NOTEBOOKS_DIR` and sample/output data from
`ECHO_DATA_DIR`.

### Option 2: Local Development with Python `venv`

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Run the web interface
echo-run

# Run a backend-only sanity check
echo-run --check

# Or run Streamlit directly
streamlit run app.py
```

If you prefer `uv`, replace the install step with `uv pip install -e .`.

Then open http://localhost:8501 in your browser.

### Option 3: Local Development with Conda

```bash
# Create and activate a Conda environment
conda create -n echo-run python=3.11 -y
conda activate echo-run

# Install dependencies
pip install -e .

# Run the web interface
echo-run

# Run a backend-only sanity check
echo-run --check
```

Then open http://localhost:8501 in your browser.

## Usage

1. **Open the web interface** in your browser
2. **Configure your experiment**:
   - Choose a notebook first
   - Upload a config file (`.ini`), OR
   - Fill in the form fields (experiment name, doses, volumes, samples)
3. **Review the notebook-specific parameters** before continuing
4. **Click "Generate Protocol"** to test the current UI flow
5. Review the status message describing what is already wired up and what is still pending

## Configuration

Edit `config.example.ini` to create your own config:

```ini
experiment_name = my_experiment
doses = 6
doses2 = 3
highest_dose = 4
vol_cellextract = 2000
vol_antigen = 2000
samples = sample1,sample2,sample3
notebook = library_plate_a_protocol.ipynb
```

The app accepts either:

- flat key/value INI files like `config.example.ini`
- an `[experiment]` section containing the same keys

At the moment, these notebooks still define most variant/sample lists internally, so config support is
best viewed as a future integration surface rather than the current source of truth for every
workflow.

The app also supports these optional environment variables:

- `ECHO_NOTEBOOKS_DIR`: override the notebook directory scanned by the UI and CLI
- `ECHO_DATA_DIR`: override the data directory used by backend checks and future protocol output

## Notebook Workflows

Current notebooks use clearer snake_case names and are still mostly self-contained workflow
templates:

- `library_plate_a_protocol.ipynb`
- `library_plate_b_protocol.ipynb`
- `premade_sensor_dual_antigen_protocol.ipynb`
- `dual_antigen_expression_protocol.ipynb`

Based on the committed raw outputs in `data/raw/`, the library plate A and B workflows have the
strongest evidence of prior successful runs. Those raw files include:

- source plate layouts as 16x24 CSV grids
- Echo transfer protocols with columns such as `Sample Name`, `Source Well`, `Destination Well`,
  and `Transfer Volume`

## Project Structure

```
.
├── app.py                    # Streamlit web UI
├── pyproject.toml            # Project dependencies
├── echo_run/                 # Console entry point
├── config.example.ini        # Example configuration
├── Dockerfile                # Docker container definition
├── notebooks/                # Protocol generation notebooks
│   ├── dual_antigen_expression_protocol.ipynb
│   ├── premade_sensor_dual_antigen_protocol.ipynb
│   ├── library_plate_a_protocol.ipynb
│   └── library_plate_b_protocol.ipynb
└── data/                     # Sample data files
    └── raw/
```

## Requirements

- Python 3.11+
- Either:
  - Python with a virtual environment created via `python3 -m venv`, or
  - Conda with a Python 3.11 environment
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Papermill (for notebook execution)

## Current Status

- The Streamlit UI starts, lists notebooks, and pre-populates form values from uploaded config files.
- The notebook list and documentation now reflect the notebook workflows that actually exist in the repo.
- The `Generate Protocol` button is still a placeholder; notebook execution and CSV generation are not connected yet.
- The current notebooks appear to be self-contained and historically write CSVs directly with hardcoded names.
- Docker and local editable installs now use the same package entry point: `echo-run`.
- On Linux systems with externally managed Python, use a virtual environment before running `pip install -e .`.
- Conda users can create a Python 3.11 environment and use the same `pip install -e .` and `echo-run` workflow.
- `echo-run --check` exercises the backend config parsing and repo wiring without requiring Streamlit to launch.
- Docker users can mount local notebook and data folders and point the app at them with `ECHO_NOTEBOOKS_DIR` and `ECHO_DATA_DIR`.

## Tests

Run the backend smoke tests with the Python standard library:

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
