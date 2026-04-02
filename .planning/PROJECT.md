# Echo Lab Protocol Generator

## What This Is

A Jupyter notebook-based lab protocol generator for Beckman Echo liquid handler. It generates CSV transfer protocols for automated liquid handling in 384-well and 96-well plate formats based on experiment parameters (dose concentrations, sample variants, volumes).

## Core Value

Scientists can define experiment parameters in notebooks and generate validated liquid handler transfer protocols without manual spreadsheet work.

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

- Python module refactoring — notebooks sufficient for now
- Web interface — notebook execution meets current needs
- Real-time instrument integration — CSV export sufficient

## Context

**Existing codebase:**
- 6 Jupyter notebooks in `notebooks/` directory
- Raw CSV data in `data/raw/`
- No Python modules — all logic embedded in notebooks

**Key architecture patterns:**
- Plate maps using Pandas DataFrames (rows A-P, columns 1-24)
- Flat lists of 384 elements for well tracking
- Direct list/array manipulation for dose-response mapping

**Known concerns from mapping:**
- Hardcoded parameters (not configurable via external config)
- Duplicate logic between plate files
- No automated testing
- No version control for protocols

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