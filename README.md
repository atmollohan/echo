# Echo Protocol

A user-friendly web application for generating Beckman Echo liquid handler protocols. Designed for lab scientists who aren't coders: choose whether they are reusing a premade plate or creating a new one, configure experiment parameters in a form, inspect committed source plate layouts and Echo transfer plans, and prepare for CSV protocol generation without editing notebook code.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build the container
docker build -t echo-protocol-generate .

# Run the web interface
docker run -p 8501:8501 echo-protocol-generate
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
  echo-protocol-generate
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
echo-protocol-generate

# Run a backend-only sanity check
echo-protocol-generate --check

# Run the preprocessing workflow directly from the shell
echo-protocol-generate --run-preprocessing \
  --plate-mode "Use a premade plate" \
  --premade-plate 20240813_ML_L1_source_plateA.csv \
  --experiment-name plate_a_validation

# Or run Streamlit directly
streamlit run app.py
```

If you prefer `uv`, replace the install step with `uv pip install -e .`.

Then open http://localhost:8501 in your browser.

### Option 3: Local Development with Conda

```bash
# Create and activate a Conda environment
conda create -n echo-protocol python=3.11 -y
conda activate echo-protocol

# Install dependencies
pip install -e .

# Run the web interface
echo-protocol-generate

# Run a backend-only sanity check
echo-protocol-generate --check
```

Then open http://localhost:8501 in your browser.

## Usage

1. **Open the web interface** in your browser
2. **Choose the plate starting point**:
   - `Use a premade plate`, OR
   - `Create a new plate`
3. **Fill out the experiment parameters** in the form
   - When using a premade plate, the app now derives initial parameter values from the selected source plate and historical protocol
4. **Inspect the sample source plate maps** to see how the current repo arranges materials in the committed CSV examples
5. **Inspect the committed Echo protocol maps** to see how those source materials turn into destination transfers
6. **Click "Generate Protocol"** to test the current UI flow
7. Review the generated source plate and protocol previews, then download the CSV artifacts

The app is now intentionally centered on one workflow:

- a single preprocessing notebook conceptually called `echo-protocol-preprocessing`
- form-based setup instead of notebook switching or config upload
- an explicit branch for `premade plate` versus `manual source plate definition`
- a generic Python preprocessing runner that can accept form fields directly and later hand them to a parameterized notebook or Python implementation

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

The repo still includes config parsing support in the backend and CLI, but the current UI no longer
surfaces config upload because the product is being shaped around direct form entry for one guided
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

- case folders for each reference workflow under `data/raw/library_plate_a/` and `data/raw/library_plate_b/`
- source plate layouts as 16x24 CSV grids
- Echo transfer protocols with columns such as `Sample Name`, `Source Well`, `Destination Well`,
  and `Transfer Volume`

When a scientist selects a premade reference case, the UI renders that source plate together with
the paired historical protocol output so the workflow is easy to understand before running a new
experiment. The current UI also derives default parameter values from that selected source
plate/protocol pair so the scientist can quickly regenerate a similar run, though that inference
still needs validation with end users.

After a run completes, the UI renders the generated source plate and generated protocol together so
the protocol can be validated before the CSVs are downloaded. The review panel now includes:

- a completion banner with timestamp and runtime
- the generated protocol table itself
- a collapsible destination-composition view
- clearer artifact download cards with short file descriptions

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

- The Streamlit UI is now shaped around one fixed preprocessing workflow instead of notebook switching.
- The UI now makes the main workflow decision explicit: use a premade plate or define a new source plate manually.
- The app now pairs each selected premade source plate with its reference protocol output instead of showing every committed output up front.
- Premade plate selection now auto-fills parameter fields from the selected source plate and historical protocol.
- Premade plate parameter inference is still a product assumption and should be validated with end users.
- The app now shows generated source plate and protocol validation previews only after a workflow run completes.
- The validation view now includes the actual generated Echo protocol table before the destination-composition preview.
- The post-run experience now includes a completion timestamp, runtime, and clearer download cards.
- The notebook list and documentation now reflect the notebook workflows that actually exist in the repo.
- The Run button now calls a generic preprocessing runner that accepts form fields directly.
- Premade Plate A and Plate B runs can already be validated against the committed fixture CSVs.
- Manual source plate runs now use a built-in Python workflow and produce a protocol CSV plus companion visualization CSVs.
- Notebook-based preprocessing now falls back to an in-process executor when Jupyter kernel startup is unavailable in constrained environments.
- The current notebooks appear to be self-contained and historically write CSVs directly with hardcoded names.
- Docker and local editable installs now use the same package entry point: `echo-protocol-generate`.
- On Linux systems with externally managed Python, use a virtual environment before running `pip install -e .`.
- Conda users can create a Python 3.11 environment and use the same `pip install -e .` and `echo-protocol-generate` workflow.
- `echo-protocol-generate --check` exercises the backend config parsing and repo wiring without requiring Streamlit to launch.
- Docker users can mount local notebook and data folders and point the app at them with `ECHO_NOTEBOOKS_DIR` and `ECHO_DATA_DIR`.

## Tests

Run the backend smoke tests with the Python standard library:

```bash
python3 -m unittest discover -s tests -v
```

## Product Discovery Questions

These are better questions to ask as you shape this into a useful product for grad students and
other lab users, not just a thin wrapper around notebooks:

1. If the user chooses a premade plate, what information do they need to specify besides the plate itself: experiment type, sample list, concentrations, replicate pattern, or destination layout?
2. If the user defines a new plate manually, what are the minimum inputs required to build that plate correctly without opening a notebook?
3. Before the user clicks Run, what exact previews or checks would make them confident enough to trust the preprocessing step?
4. Which errors or warnings would be most valuable to catch automatically before a grad student sends the protocol to the robot?
5. For repeated experiments, would users prefer to clone a previous run, start from a saved preset, or reuse a premade plate with just a few parameter changes?
6. What would make this feel like a trustworthy lab product rather than a notebook wrapper: guided steps, plain-language labels, audit trails, downloadable summaries, or stronger validation?

## License

MIT
