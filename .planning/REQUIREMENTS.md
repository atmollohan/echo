# Requirements: Echo Lab Protocol Generator

**Defined:** 2026-04-01
**Core Value:** A non-coder lab scientist can configure experiment parameters via a config file, run the protocol generator with one command, and get validated CSV output for the Echo liquid handler — no Python or notebook editing required.

## v1 Requirements

### CLI Interface

- [ ] **CLI-01**: User can run protocol generator via `echo-run` command
- [ ] **CLI-02**: User can specify config file path via `--config` flag
- [ ] **CLI-03**: User can specify output directory via `--output` flag
- [ ] **CLI-04**: CLI displays clear success/failure messages
- [ ] **CLI-05**: CLI shows progress during notebook execution

### Configuration Management

- [ ] **CFG-01**: User can define experiment parameters in YAML config file
- [ ] **CFG-02**: Config supports dose concentrations (array of values)
- [ ] **CFG-03**: Config supports sample/variant list (names and metadata)
- [ ] **CFG-04**: Config supports volume specifications (in nL)
- [ ] **CFG-05**: Config supports reagent definitions with source well positions
- [ ] **CFG-06**: CLI validates config on load with clear error messages
- [ ] **CFG-07**: Example config file provided as template

### Dependency Management

- [ ] **DEP-01**: Project uses uv for dependency management (or venv fallback)
- [ ] **DEP-02**: `pyproject.toml` defines all dependencies with version pins
- [ ] **DEP-03**: CLI checks that all required packages are installed before running
- [ ] **DEP-04**: CLI provides `install` subcommand to install dependencies
- [ ] **DEP-05**: CLI provides `sync` subcommand to sync dependencies from pyproject.toml
- [ ] **DEP-06**: Dependency conflicts produce clear error messages
- [ ] **DEP-07**: CLI detects and reports missing Python version requirements

### Notebook Execution

- [ ] **NB-01**: CLI executes notebooks programmatically (papermill or nbclient)
- [ ] **NB-02**: CLI passes config parameters to notebooks at runtime
- [ ] **NB-03**: CLI captures notebook output for logging
- [ ] **NB-04**: Notebook execution failures produce clear error messages
- [ ] **NB-05**: CLI supports dry-run mode to validate without executing
- [ ] **NB-06**: User can specify which notebook to run (default: all)

### Protocol Generation (from existing validated features)

- [ ] **PROT-01**: Generate 384-well source plate layouts
- [ ] **PROT-02**: Generate 96-well destination plate layouts
- [ ] **PROT-03**: Map dose-response matrix to well positions
- [ ] **PROT-04**: Output CSV in Beckman Echo format
- [ ] **PROT-05**: Track sample names and volumes in output

### Protocol Validation

- [ ] **VAL-01**: Validate CSV has required columns (Source Well, Dest Well, Transfer Volume)
- [ ] **VAL-02**: Validate well format matches plate type (A-P[1-24] for 384, A-H[1-12] for 96)
- [ ] **VAL-03**: Validate transfer volumes within Echo limits (min 25nL, max typical)
- [ ] **VAL-04**: Detect duplicate destination wells with multiple transfers
- [ ] **VAL-05**: Validation errors prevent output and show clear message

### Output Management

- [ ] **OUT-01**: CSV output written to user-specified directory
- [ ] **OUT-02**: Output filename includes timestamp for versioning
- [ ] **OUT-03**: CLI displays path to generated files on success
- [ ] **OUT-04**: User can override output filename

## v2 Requirements

### Multi-Notebook Support

- **[MULT-01]**: Config can specify multiple notebooks to run in sequence
- **[MULT-02]**: Output from one notebook can feed into next notebook

### Visualization

- **[VIZ-01]**: Generate plate map visualization (heatmap of well assignments)
- **[VIZ-02]**: Include visualization in notebook output

### Advanced Features

- **[ADV-01]**: Support multi-plate experiments (3+ source plates)
- **[ADV-02]**: Reagent pooling to minimize source well waste
- **[ADV-03]**: Auto-calculate serial dilutions from stock concentrations

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web interface | CLI sufficient for current needs |
| Real-time instrument integration | CSV export is sufficient |
| Inventory management | Separate product category (LIMS/ELN) |
| 1536-well plate support | Not supported by Echo 525 |
| Python module refactoring | Notebooks remain the primary interface |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 through CLI-06 | Phase 1 | Pending |
| CFG-01 through CFG-07 | Phase 1 | Pending |
| DEP-01 through DEP-07 | Phase 1 | Pending |
| NB-01 through NB-06 | Phase 1 | Pending |
| PROT-01 through PROT-05 | Phase 1 | Pending |
| VAL-01 through VAL-05 | Phase 2 | Pending |
| OUT-01 through OUT-04 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-01*
*Last updated: 2026-04-01 after research and user feedback*