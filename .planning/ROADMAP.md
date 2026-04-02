# Roadmap: Echo Lab Protocol Generator

**Phase count:** 3
**Granularity:** standard
**Coverage:** 32/32 v1 requirements mapped

## Phases

- [ ] **Phase 1: Docker & CLI Foundation** — Dockerfile, CLI entry point, config file format
- [ ] **Phase 2: Notebook Execution & Output** — Run notebooks, generate protocols, manage output
- [ ] **Phase 3: Protocol Validation** — Validate CSV output, well formats, volumes

---

## Phase Details

### Phase 1: Docker & CLI Foundation

**Goal:** User can clone the repo or pull Docker image and run with a simple config file

**Depends on:** Nothing (first phase)

**Requirements:** DOCKER-01, DOCKER-02, DOCKER-03, DOCKER-04, DOCKER-05, DOCKER-06, CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, CFG-01, CFG-02, CFG-03, CFG-04, CFG-05, CFG-06, CFG-07, CFG-08, DATA-01, DATA-02, DATA-03, DEP-01, DEP-02, DEP-03, DEP-04, DEP-05, DEP-06, DEP-07

**Success Criteria** (what must be TRUE):
1. `Dockerfile` exists and builds successfully
2. `docker build -t echo-run .` produces working image
3. `docker run -v /path/to/config:/config echo-run --help` shows usage
4. `docker run -v /path/to/config:/config -v /path/to/output:/output echo-run --config /config/experiment.ini` runs without errors
5. Config file format is simple key=value pairs (INI style)
6. Example config file `config.example.ini` exists and is valid
7. CLI displays clear success or failure messages with exit codes
8. README includes both local and docker run instructions
9. `pyproject.toml` exists with all dependencies pinned
10. Project works on macOS, Linux, and Windows (WSL compatible)

**Plans:** TBD

**UI hint:** no

---

### Phase 2: Notebook Execution & Output

**Goal:** Notebooks execute with config parameters and produce CSV output

**Depends on:** Phase 1

**Requirements:** NB-01, NB-02, NB-03, NB-04, NB-05, NB-06, PROT-01, PROT-02, PROT-03, PROT-04, PROT-05, OUT-01, OUT-02, OUT-03, OUT-04

**Success Criteria** (what must be TRUE):
1. CLI executes notebooks programmatically and captures output
2. Config parameters are passed to notebooks at runtime
3. Notebooks generate 384-well source plate layouts
4. Notebooks generate 96-well destination plate layouts
5. Dose-response matrix maps correctly to well positions
6. CSV output follows Beckman Echo format (Source Well, Dest Well, Transfer Volume)
7. Sample names and volumes appear in output CSV
8. CSV files written to user-specified output directory
9. Output filename includes timestamp for versioning
10. User can override output filename
11. CLI displays path to generated files on success

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
| 1. Docker & CLI Foundation | 0/1 | Not started | - |
| 2. Notebook Execution & Output | 0/1 | Not started | - |
| 3. Protocol Validation | 0/1 | Not started | - |

---

*Generated: 2026-04-01*
*Updated: 2026-04-01 after user feedback on Docker and config format*