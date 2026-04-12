# Echo Protocol - User Instruction Manual

## Overview

**Echo Protocol** generates liquid handler transfer instructions for Beckman Echo instruments. You can:
- Configure experiments via a web UI
- Choose between using a premade source plate or creating a new one from scratch
- Download validated CSV protocols ready for the liquid handler

No coding required.

---

## Quick Start

### Option 1: Web UI (Recommended)

```bash
docker run -p 8501:8501 echo-protocol-generate
# Or locally:
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

### Option 2: CLI

```bash
echo-protocol-generate --help
```

---

## Workflows

### 1. Using a Premade Plate

Select "Use a premade plate" in the web UI. This replays historical protocols from the repository fixture files:
- `data/raw/20240813_ML_L1_source_plateA.csv` → corresponding echo protocol
- `data/raw/20240813_ML_L1_source_plateB.csv` → corresponding echo protocol

Best for: Reproducing established experiments.

### 2. Creating a New Plate from Scratch

Select "Create a new plate from scratch." This runs the preprocessing notebook which:
1. Allocates sample wells in the first half of a 384-well plate
2. Allocates antigen/PBS reagent wells in the second half
3. Generates destination transfers with serial dilutions
4. Outputs Echo protocol CSV

Best for: New experiments with fresh sample libraries.

---

## Configuration Fields

| Field | Description | Typical Value |
|-------|------------|-------------|
| `experiment_name` | Identifier for the run | `my_assay_1` |
| `doses` | Number of dose points per sample | `6` |
| `doses2` | Second antigen curve doses | `3` |
| `highest_dose` | Maximum dose in μM | `4.0` |
| `vol_cellextract` | Cell extract volume per well (nL) | `2000` |
| `vol_antigen` | Antigen volume per well (nL) | `2000` |
| `samples` | Comma-separated sample IDs | `sample1,sample2,sample3` |

**Note:** All volumes are in nanoliters (nL).

---

## Output Files

After a successful run, you'll find in `generated/<experiment_name>/`:

| File | Description |
|------|-------------|
| `<name>_echo_protocol.csv` | Liquid handler transfer instructions |
| `<name>_source_plate.csv` | Source plate layout |
| `<name>_destination_composition.csv` | What's in each destination well |
| `<name>_run_manifest.json` | Run parameters and metadata |

The Echo protocol CSV has these columns:
- `Sample Name`
- `Source Plate Name`
- `Source Well`
- `Destination Well`
- `Transfer Volume` (nL)
- `Destination Plate Name`
- `Source Plate Type`

---

## Validation (Automatic)

Protocols are validated before export. Validation checks:

### Errors (blocking)
- Missing required columns
- Invalid well formats (e.g., `Q1` or `A25` for 96-well plate)
- Transfer volumes > 500,000 nL
- Conflicting samples at same destination well

### Warnings (non-blocking)
- Transfer volumes < 25 nL (Echo may not dispense accurately)
- Duplicate transfers to the same destination well
- Source plate volumes exceeding well capacity (65,000 nL)

---

## Troubleshooting

### "Missing required column" Error

The protocol CSV lacks one of the required columns. Check:
- Was the notebook interrupted?
- Is the source data in `data/raw/` corrupted?

### "Invalid 384-well format" Error

Well names must match 384-well format: `A1` to `P24`. Examples:
- ✅ Valid: `A1`, `C12`, `P24`
- ❌ Invalid: `Q1`, `A25`, `AA1`

### "Transfer volume exceeds maximum" Error

Volumes > 500,000 nL exceed Echo specifications. Reduce your transfer volumes.

### "Destination receives multiple samples" Error

Two different samples are being transferred to the same destination well. Check the sample allocation logic.

### Notebook Execution Fails

1. Check that `papermill` is installed: `pip install papermill`
2. Verify the notebook path is correct
3. Check the output directory is writable

### Output CSV Missing

Check:
1. The experiment name contains only alphanumeric characters
2. The output directory is not read-only
3. There is sufficient disk space

### Validation Passes But Liquid Handler Fails

Ensure:
- Source plate wells contain sufficient volume
- Reagents are in the expected wells
- The plate map matches the protocol's source well references

---

## Debug Mode

### Run Backend Checks

```bash
.venv/bin/python -m echo_run.cli --check
```

This verifies:
- Notebooks are discoverable
- Config files are valid
- Source plate CSVs are readable

### View Generated Outputs

```bash
ls -la generated/
cat generated/<name>_<experiment_name>_echo_protocol.csv
```

### Run Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

---

## Architecture (What Happens Under the Hood)

```
UI Input → PreprocessingRequest
    ↓
If "premade plate": load fixture CSV pair
If "new plate": execute notebook (via papermill)
    ↓
Source plate + Echo protocol CSV generated
    ↓
Validation runs (if enabled)
    ↓
Output files written to generated/<experiment_name>/
```

### Key Files

- `app.py` - Streamlit web UI
- `echo_run/preprocessing.py` - Workflow runner
- `echo_run/validation.py` - Protocol validation
- `echo_run/backend.py` - Config parsing, file utilities
- `notebooks/echo-protocol-preprocessing.ipynb` - Protocol generation notebook

---

## Getting Help

- Run `.venv/bin/python -m echo_run.cli --help`
- Open an issue at https://github.com/anomalyco/echo/issues
- Check `README.md` for setup instructions