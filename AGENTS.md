# Echo Lab Protocol Generator

## Project Overview

**Echo Lab Protocol Generator** - A user-friendly web application for generating Beckman Echo liquid handler protocols.

**Core Value:** A non-coder lab scientist can:
1. Clone the repo (or pull the Docker image)
2. Open the web interface in a browser
3. Configure experiment parameters via form or config file
4. Click "Generate Protocol" and download validated CSV output

No Python coding, no notebook editing, no complex setup required.

### Constraints

- **Platform**: Python 3, Streamlit web UI, Jupyter notebooks
- **Output**: CSV files compatible with Beckman Echo liquid handler
- **Format**: 384-well source plates, 96-well destination plates

---

## Technology Stack

### Languages
- Python 3 - Core application logic
- Jupyter - Protocol generation notebooks

### Dependencies
- streamlit - Web UI framework
- pandas - Data manipulation/CSV processing
- numpy - Numerical operations for dose calculations
- matplotlib - Plate heatmaps, visualization
- papermill - Notebook execution
- tqdm - Progress bars

### Runtime
- Python 3.11+
- Docker (for containerized deployment)
- uv or pip for dependency management

---

## Architecture

### Pattern Overview
- Streamlit web UI as primary interface
- Jupyter notebooks contain protocol generation logic
- CSV configuration files for experiment parameters
- Docker for portable deployment

### Layers
1. **Web UI Layer** (app.py)
   - Config file upload
   - Form-based parameter entry
   - Notebook selector
   - Output display with download

2. **Configuration Layer**
   - INI format config files
   - Experiment parameters (doses, volumes, samples)
   - Notebook selection

3. **Protocol Generation Layer** (notebooks/)
   - 384-well plate layout generation
   - 96-well destination plate layouts
   - Dose-response matrix mapping
   - CSV protocol output

### Data Flow
- User inputs experiment parameters via UI
- Parameters passed to selected notebook
- Notebook generates CSV protocol
- CSV displayed in UI with download option

---

## Project Structure

```
.
├── app.py                    # Streamlit web UI
├── pyproject.toml            # Project dependencies
├── config.example.ini        # Example configuration
├── Dockerfile                # Docker container
├── README.md                 # Usage instructions
├── notebooks/                # Protocol generation notebooks
│   ├── library-PLATE-A.ipynb
│   └── library-PLATE-B.ipynb
└── data/                     # Sample data
    └── raw/
```

---

## Getting Started

### Local Development
```bash
# Install dependencies
pip install -e .

# Run web UI
streamlit run app.py
```

### Docker
```bash
# Build
docker build -t echo-run .

# Run
docker run -p 8501:8501 echo-run
```

Then open http://localhost:8501 in your browser.

---

## Configuration

Edit `config.example.ini` or use the web form:

```ini
experiment_name = my_experiment
doses = 6
doses2 = 3
highest_dose = 4
vol_cellextract = 2000
vol_antigen = 2000
samples = sample1,sample2,sample3
notebook = library-PLATE-A.ipynb
```

---

## Notes

- Units for all volumes are in nanoliters (nL)
- Notebooks require hardcoded parameters currently (v1)
- Output format: Beckman Echo CSV (Source Well, Dest Well, Transfer Volume)
- Validation layer coming in future phase