# Echo Lab Protocol Generator

## What This Is

A user-friendly Python-based web app (Streamlit) for running Jupyter notebooks that generate Beckman Echo liquid handler protocols. Designed for lab scientists who aren't coders — provides a clean browser interface to configure experiments, run notebooks, and download CSV protocols without touching notebook code.

## Core Value

A non-coder lab scientist can:
1. Clone the repo (or pull the Docker image)
2. Open the web interface in a browser
3. Configure experiment parameters via form fields or upload a config file
4. Click "Generate Protocol" and download validated CSV output

No Python coding, no notebook editing, no complex setup required.

## Requirements

### Validated

- ✓ 384-well plate layout generation — existing
- ✓ 96-well plate layout generation — existing
- ✓ Dose-response matrix mapping — existing
- ✓ CSV protocol output for Echo liquid handler — existing
- ✓ Sample name and volume tracking — existing

### Active

- [ ] TBD — define what to build next

### Out of Scope

- Full Python module refactoring — notebooks sufficient, but extract shared utilities
- Web interface — CLI meets current needs
- Real-time instrument integration — CSV export sufficient
- Inventory management — separate product category (LIMS/ELN)
- 1536-well plate support — not supported by Echo 525

## Context

**Existing codebase:**
- 6 Jupyter notebooks in `notebooks/` directory
- Raw CSV data in `data/raw/`
- No Python modules — all logic embedded in notebooks
- Notebooks require editing to change experiment parameters

**Target user:**
- Lab scientist (not a coder)
- Works with Python/Jupyter for lab work
- Needs to quickly configure and run experiments
- Wants portability — easy to share with colleagues

**Known concerns from mapping:**
- Hardcoded parameters (edit notebook cells to change)
- Duplicate logic between plate files
- No automated testing
- No version control for protocols
- Scientists must edit notebook code to configure experiments

## Constraints

- **Platform**: Python 3, Jupyter notebooks
- **Output**: CSV files compatible with Beckman Echo liquid handler
- **Format**: 384-well source plates, 96-well destination plates

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Notebook-based architecture | Familiar to lab scientists, easy to modify | — Pending |
| CSV output | Echo liquid handler accepts CSV protocols | — Pending |

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
*Last updated: 2026-04-01 after codebase mapping*