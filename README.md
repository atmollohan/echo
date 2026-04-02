# Echo Lab Protocol Generator

A user-friendly web application for generating Beckman Echo liquid handler protocols. Designed for lab scientists who aren't coders — configure experiments via a simple form or config file, click a button, and download validated CSV output.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build the container
docker build -t echo-run .

# Run the web interface
docker run -p 8501:8501 echo-run
```

Then open http://localhost:8501 in your browser.

### Option 2: Local Development

```bash
# Install dependencies
pip install -e .

# Or with uv (faster)
uv pip install -e .

# Run the web interface
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Usage

1. **Open the web interface** in your browser
2. **Configure your experiment**:
   - Upload a config file (`.ini`), OR
   - Fill in the form fields (experiment name, doses, volumes, samples)
3. **Select a notebook** from the dropdown (e.g., `library-PLATE-A.ipynb`)
4. **Click "Generate Protocol"**
5. **Download** the generated CSV files

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
notebook = library-PLATE-A.ipynb
```

## Project Structure

```
.
├── app.py                    # Streamlit web UI
├── pyproject.toml            # Project dependencies
├── config.example.ini        # Example configuration
├── Dockerfile                # Docker container definition
├── notebooks/                # Protocol generation notebooks
│   ├── library-PLATE-A.ipynb
│   └── library-PLATE-B.ipynb
└── data/                     # Sample data files
    └── raw/
```

## Requirements

- Python 3.11+
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Papermill (for notebook execution)

## License

MIT