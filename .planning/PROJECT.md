# Echo Lab Protocol Generator

## What This Is

A user-friendly Python-based workflow app for Beckman Echo protocol generation. The current product centers on a Streamlit UI plus a shared CLI/backend preprocessing runner so a lab scientist can choose a guided workflow, inspect committed plate/protocol examples, and generate auditable CSV artifacts without editing notebook code.

## Core Value

A non-coder lab scientist can:
1. Clone the repo (or pull the Docker image)
2. Open the web interface in a browser
3. Choose whether they are reusing a premade plate or creating a new plate
4. Configure experiment parameters via form fields
5. Inspect committed source plate and Echo protocol examples
6. Click "Generate Protocol" and get protocol artifacts without touching notebook code

No Python coding, no notebook editing, no complex setup required.

## Requirements

### Validated

- ✓ Streamlit web UI exists and launches through `app.py` or `echo-protocol-generate`
- ✓ Dockerfile and local editable install path exist for the current app
- ✓ Scientists can choose `premade plate` versus `create a new plate from scratch`
- ✓ UI previews committed source plate CSVs and Echo protocol CSVs from `data/raw/`
- ✓ Shared preprocessing runner is wired into both the UI and the CLI
- ✓ Premade plate runs can replay committed fixtures into generated protocol/source/composition outputs
- ✓ Run manifest JSON is written for preprocessing runs
- ✓ Backend and preprocessing smoke tests exist for the current Python package

### Active

- [ ] Connect a real parameterized notebook or Python implementation for `create a new plate from scratch`
- [ ] Turn the optional papermill notebook hook into a supported workflow with a stable output contract
- [ ] Add formal protocol validation before export instead of relying on visual inspection alone
- [ ] Decide the long-term input model: direct form entry only, config files, saved presets, or a hybrid
- [ ] Replace the current product-discovery questions in the UI with locked workflow requirements once the target lab flow is settled

### Out of Scope

- Full extraction of all protocol logic out of notebooks — keep shared helpers in Python, but do not require a full rewrite yet
- Generic notebook picker as the primary UI — the current product is intentionally centered on one guided preprocessing workflow
- Real-time instrument integration — CSV export sufficient
- Inventory management — separate product category (LIMS/ELN)
- 1536-well plate support — not supported by Echo 525

## Context

**Existing codebase:**
- Streamlit app in `app.py`
- Python package in `echo_run/` with shared backend, CLI, and preprocessing runner
- 4 workflow notebooks in `notebooks/`
- Raw CSV data in `data/raw/`
- Example config file plus backend config parsing helpers
- Test suite in `tests/` covering backend helpers and preprocessing fixture replay

**Target user:**
- Lab scientist (not a coder)
- Needs a browser-first workflow with minimal setup
- Wants to inspect trusted examples before generating outputs
- Wants portability — easy to share with colleagues

**Known concerns from mapping:**
- `Create a new plate from scratch` is not yet connected to a real implementation
- Current notebooks still rely on hardcoded internals and historically write directly to CSV
- Formal protocol validation is not implemented yet
- Some planning assumptions still reflect the older config-upload and notebook-picker direction
- Product workflow questions are still embedded in the UI and README, which means scope is not fully locked

## Constraints

- **Platform**: Python 3, Streamlit UI, shared CLI/backend runner, Jupyter notebooks
- **Output**: CSV files compatible with Beckman Echo liquid handler
- **Format**: 384-well source plates, 96-well destination plates

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Guided preprocessing workflow over notebook chooser | Reduce branching in the UI and focus the product on one user task | Adopted in current UI |
| Premade-vs-new plate choice is the first workflow split | Matches the current scientist decision point and simplifies the form | Adopted in current UI |
| Shared preprocessing runner for UI and CLI | Keeps workflow behavior aligned across browser and command-line entry points | Adopted in `echo_run.preprocessing` |
| CSV output remains the delivery format | Echo liquid handler accepts CSV protocols directly | Adopted |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-05 after planning refresh against current repo state*
