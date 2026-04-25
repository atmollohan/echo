<!-- GSD:project-start source:PROJECT.md -->
## Project

**Echo Protocol**

A user-friendly Python-based tool for running Jupyter notebooks that generate Beckman Echo liquid handler protocols. Designed for lab scientists who aren't coders — provides a clean interface to configure experiments, run notebooks, and export CSV protocols without touching notebook code.

**Core Value:** A non-coder lab scientist can:
1. Clone the repo (or pull the Docker image)
2. Edit a simple config file with experiment parameters
3. Run `docker run` (or `echo-protocol-generate` locally)
4. Use the web UI to configure experiments and inspect notebook workflows
5. Generate validated CSV output for the Echo liquid handler once notebook execution is connected

No Python coding, no notebook editing, no complex setup required.

### Constraints

- **Platform**: Python 3, Jupyter notebooks
- **Output**: CSV files compatible with Beckman Echo liquid handler
- **Format**: 384-well source plates, 96-well destination plates
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3 - Data analysis, notebook execution, plate map generation
- Jupyter - Interactive notebooks for experiment analysis
## Runtime
- Python 3 virtual environment (`.venv/`) or Conda environment
- Package Manager: pip (via requirements.txt)
- matplotlib - Data visualization
- notebook - Jupyter notebooks
- numpy - Numerical computing
- pandas - Data manipulation/CSV processing
- tqdm - Progress bars
- papermill - Notebook execution
- streamlit - Web UI
## Frameworks
- Pandas - CSV reading/writing for lab equipment protocols
- NumPy - Numerical operations for dose calculations
- Matplotlib - Plate heatmaps, dose-response curves
## Configuration
- Virtual environment or Conda environment setup for local development
- `pyproject.toml` - Python dependencies (uses setuptools)
- `Makefile` - Common development tasks
- Jupyter notebooks (`.ipynb`) for all analysis code
## Platform Requirements
- Python 3.11+
- Docker for containerized deployment
- Virtual environment or Conda environment
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Lowercase with hyphens: `library-PLATE-A.ipynb`, `2-ANTIGEN-2-MM-EXPRESSION.ipynb`
- Checkpoint files: `*-checkpoint.ipynb`
- Lowercase with underscores: `source_sample_names`, `dest_antigen_vol`, `plate_columns`
- Descriptive: `vol_cellextract`, `amnt_antigen_to_add`
- Simple descriptive names: `make_plate()` - defined inline in notebooks
## Code Style
- Python standard (PEP 8 implicit)
- No enforced formatting tools detected
- None detected
- Sequential cell execution
- Import cells at top
- Configuration cells before logic cells
## Import Organization
## Error Handling
- Print statements for verification
- No try/except blocks detected
- Minimal error handling - relies on sequential execution
- Print statements: `print(variants)`, `print(num_samples)`, `print(dest_antigen_vol)`
- Checkpoint saves for recovery
## Comments
- Inline comments for complex calculations
- Section headers via Markdown cells
- Example: `"Note: units for ALL volumes is nL"`
- No formal docstrings (Jupyter cells instead)
- No type hints detected
## Function Design
- Simple helper functions defined inline
- Example: `make_plate()` creates empty DataFrame
- Not applicable - logic in notebook cells, not modular functions
## Module Design
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Notebooks contain protocol logic, while the Python package provides the UI and startup entry point
- Direct manipulation of lists/arrays for plate operations
- CSV generation for Beckman Echo liquid handler protocols
- Experiment parameter configuration via notebook cells
## Layers
- Purpose: Define experiment parameters
- Location: `notebooks/` (cells near top of each notebook)
- Contains: Dose concentrations, volumes, variant lists
- Example parameters: `doses = 6`, `highest_dose = 4` (uM), `vol_cellextract = 2000` (nL)
- Purpose: Represent 384-well and 96-well plate layouts
- Location: `notebooks/library-PLATE-*.ipynb`
- Contains: List-based well tracking, dose-response mapping
- Pattern: Flat lists of 384 elements indexed by well position
- Purpose: Create liquid handler transfer instructions
- Location: `notebooks/library-PLATE-*.ipynb` (later cells)
- Contains: Source/destination well mapping, volume calculations
- Output: CSV files for Echo liquid handler
## Data Flow
- `wells` - List of 384 well identifiers (A1-P24)
- `wells96` - List of 96 well identifiers (A1-H12)
- `source_sample_names` - 384-length list of sample IDs
- `source_sample_vol` - 384-length list of volumes (nL)
- `dest_*_vol` - Destination well volumes for each reagent
## Key Abstractions
- Purpose: Represent 384-well plate layout
- Examples: `source_plate_df` in notebooks
- Pattern: Pandas DataFrame with rows A-P, columns 1-24
- Purpose: Map variant → dose point → well
- Pattern: Nested loops generating flat lists
## Entry Points
- Location: `app.py` and `echo_run/cli.py`
- Triggers: `echo-protocol-generate`, `streamlit run app.py`, or Docker startup
- Responsibilities: UI startup, config loading, notebook selection, future notebook execution
- Supporting protocol logic remains in `notebooks/*.ipynb`
## Error Handling
- Print statements for verification (`print(variants)`, `print(num_samples)`)
- Checkpoint notebooks saved as backups (`*-checkpoint.ipynb`)
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
