# Roadmap: Echo Lab Protocol Generator

**Phase count:** 3
**Granularity:** standard
**Coverage:** 32/32 v1 requirements mapped

## Phases

- [ ] **Phase 1: Web UI & Docker Foundation** — Streamlit app, Dockerfile, config loading
- [ ] **Phase 2: Notebook Execution & Output** — Run notebooks, generate protocols, manage output
- [ ] **Phase 3: Protocol Validation** — Validate CSV output, well formats, volumes

---

## Phase Details

### Phase 1: Web UI & Docker Foundation

**Goal:** User can open web interface in browser and generate protocols

**Depends on:** Nothing (first phase)

**Requirements:** UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08, UI-09, UI-10, DOCKER-01, DOCKER-02, DOCKER-03, DOCKER-04, DOCKER-05, DOCKER-06, CFG-01, CFG-02, CFG-03, CFG-04, CFG-05, CFG-06, CFG-07, CFG-08, DATA-01, DATA-02, DATA-03

**Success Criteria** (what must be TRUE):
1. `streamlit run app.py` opens web interface in browser
2. User can upload or select config file via file picker
3. User can view/edit experiment parameters in form fields
4. User can select which notebook to run
5. UI shows progress during notebook execution
6. UI displays generated CSV output with download button
7. UI shows validation errors clearly with suggestions
8. `Dockerfile` exists and builds with Streamlit
9. `docker run -p 8501:8501 echo-run` opens web UI
10. README includes both local and docker run instructions
11. Example config file exists and is valid

**Plans:** TBD

**UI hint:** yes

---

### Phase 2: Notebook Execution & Output

**Goal:** Notebooks execute with config parameters and produce CSV output

**Depends on:** Phase 1

**Requirements:** NB-01, NB-02, NB-03, NB-04, NB-05, NB-06, PROT-01, PROT-02, PROT-03, PROT-04, PROT-05, OUT-01, OUT-02, OUT-03, OUT-04

**Success Criteria** (what must be TRUE):
1. UI executes notebooks programmatically and captures output
2. Config parameters are passed to notebooks at runtime
3. Notebooks generate 384-well source plate layouts
4. Notebooks generate 96-well destination plate layouts
5. Dose-response matrix maps correctly to well positions
6. CSV output follows Beckman Echo format (Source Well, Dest Well, Transfer Volume)
7. Sample names and volumes appear in output CSV
8. CSV files downloadable from UI
9. Output filename includes timestamp for versioning
10. User can override output filename
11. UI displays path to generated files on success

**Plans:** TBD

---

### Phase 3: Protocol Validation

**Goal:** Generated CSV protocols are validated before delivery to prevent errors

**Depends on:** Phase 2

**Requirements:** VAL-01, VAL-02, VAL-03, VAL-04, VAL-05

**Success Criteria** (what must be TRUE):
1. CSV output has required columns (Source Well, Dest Well, Transfer Volume)
2. Well format matches plate type (A-P[1-24] for 384, A-H[1-12] for 96)
3. Transfer volumes are within Echo limits (min 25nL)
4. Duplicate destination wells with multiple transfers are detected
5. Validation errors prevent output and show clear message

**Plans:** TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Web UI & Docker Foundation | 0/1 | Not started | - |
| 2. Notebook Execution & Output | 0/1 | Not started | - |
| 3. Protocol Validation | 0/1 | Not started | - |

---

*Generated: 2026-04-01*
*Updated: 2026-04-01 after user feedback - web UI (Streamlit) instead of CLI*