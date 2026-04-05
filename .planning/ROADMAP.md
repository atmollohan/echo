# Roadmap: Echo Lab Protocol Generator

**Phase count:** 3
**Granularity:** standard
**Coverage:** refreshed against the current guided preprocessing workflow as of 2026-04-05

## Phases

- [x] **Phase 1: Guided Workflow Foundation** — Streamlit UI, CLI entry point, Docker packaging, fixture inspection
- [ ] **Phase 2: Preprocessing Execution & Artifact Generation** — Real workflow execution, generated outputs, new-plate path
- [ ] **Phase 3: Formal Protocol Validation & Trust Signals** — CSV validation, blocking errors, validation summaries

---

## Phase Details

### Phase 1: Guided Workflow Foundation

**Goal:** A scientist can launch the product, choose the guided preprocessing workflow, inspect committed examples, and start runs from the browser or CLI.

**Depends on:** Nothing (first phase)

**Status:** Substantially complete in the current repo

**Completed now:**
1. `streamlit run app.py` and `echo-protocol-generate` launch the current UI
2. Dockerfile exists and the README documents local and container workflows
3. UI is centered on one fixed preprocessing workflow instead of generic notebook switching
4. UI collects experiment parameters through form fields
5. UI makes the main workflow decision explicit: `premade plate` versus `create a new plate from scratch`
6. UI previews committed source plate CSVs from `data/raw`
7. UI previews committed Echo protocol CSVs from `data/raw`
8. CLI includes backend sanity checks and a preprocessing entry point
9. Backend config parsing and example config file still exist for compatibility and future decisions

**Remaining to close the phase cleanly:**
1. Decide whether config upload belongs in the UI or remains a CLI/backend capability
2. Decide whether notebook selection returns as a user-facing feature or stays out of the guided UI
3. Replace the current discovery questions with locked workflow requirements once the target lab flow is agreed

**UI hint:** yes

---

### Phase 2: Preprocessing Execution & Artifact Generation

**Goal:** The fixed preprocessing workflow produces real, auditable artifacts from user inputs across both premade and new-plate flows.

**Depends on:** Phase 1

**Status:** In progress

**Completed now:**
1. `echo_run.preprocessing` normalizes form and CLI inputs into a shared request model
2. Premade plate runs can replay committed fixture CSVs into generated output folders
3. The preprocessing runner writes an Echo protocol CSV, source plate CSV, destination composition CSV, and JSON run manifest for fixture replay mode
4. The Streamlit UI and CLI both call the same preprocessing entry point
5. Optional notebook execution support exists through papermill when `ECHO_WORKFLOW_NOTEBOOK` is configured
6. UI surfaces generated artifact paths and download buttons for successful runs

**Remaining:**
1. Implement or connect the actual `create a new plate from scratch` workflow
2. Promote the optional notebook path into a supported, documented execution mode with predictable artifact names
3. Ensure notebook mode and fixture mode both satisfy the same output contract
4. Add stronger progress and failure reporting around notebook execution
5. Decide whether timestamps, output naming controls, and saved run presets are required in v1

---

### Phase 3: Formal Protocol Validation & Trust Signals

**Goal:** Generated protocols are validated before delivery so users can trust outputs beyond visual inspection.

**Depends on:** Phase 2

**Status:** Not started as formal validation work, though visual inspection support exists

**Completed now:**
1. UI provides visual previews of source plate occupancy and destination-well composition from committed examples
2. Tests exist for preprocessing fixture replay and protocol/source summary helpers

**Remaining:**
1. Validate required protocol columns
2. Validate well formats against 384-well and 96-well expectations
3. Validate transfer volume bounds for Echo-compatible output
4. Detect problematic duplicate or conflicting destination-well transfers
5. Produce clear validation summaries and block export when rules fail
6. Resolve the validation policy question: fail hard versus warn-and-continue

**Planning note:** This phase should begin only after the real new-plate workflow and notebook-backed outputs are stable enough to validate consistently.

---

## Progress

| Phase | Status | Already done | Remaining focus |
|-------|--------|--------------|-----------------|
| 1. Guided Workflow Foundation | Substantially complete | UI, CLI, Docker, docs, committed fixture previews | Lock the workflow scope around config uploads and notebook selection |
| 2. Preprocessing Execution & Artifact Generation | In progress | Shared runner, fixture replay, output artifacts, papermill hook, UI downloads | New-plate implementation, stable notebook mode, stronger output contract |
| 3. Formal Protocol Validation & Trust Signals | Not started | Visual inspection helpers and smoke tests | Formal CSV validation, blocking errors, trust/reporting layer |

---

*Generated: 2026-04-01*
*Updated: 2026-04-05 after reconciling roadmap with current repo state*
