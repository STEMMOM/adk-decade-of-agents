
---

# 📄 **DEVELOPMENT_WORKFLOW_SPEC_v1.0.md**



```markdown
# Development Workflow Specification (v1.0)

**Status:** Stable  
**Applies to:** Entire `adk-decade-of-agents` repository  
**Purpose:**  
Define the official development workflow for running projects inside a Python virtual environment (venv), validating Sessions & Memory behaviors, and pushing changes into Git with disciplined practices.

---

# 1. Overview

This specification defines the end-to-end workflow for:

1. Activating & using Python virtual environments  
2. Running ADK project code for validation  
3. Recording clean, structured progress in Git  
4. Ensuring reproducible, maintainable engineering practices  
5. Supporting the multi-project architecture of the repository  

This workflow applies to all **50+ mini-projects** and **all modules** (Sessions & Memory, MCP, Context Engineering, etc.).

---

# 2. Virtual Environment Specification

## 2.1 Location

Every developer must use the repository-local virtual environment:

```

adk-decade-of-agents/.venv

````

## 2.2 Creation

Run once per machine or after cloning:

```bash
python3 -m venv .venv
````

## 2.3 Activation

Every development session **must activate venv**:

```bash
source .venv/bin/activate
```

Prompt must display:

```
(.venv)
```

## 2.4 Deactivation

If needed:

```bash
deactivate
```

## 2.5 Required Packages

Inside venv:

```bash
pip install google-adk google-genai
pip install jupyter ipykernel   # Optional, for notebooks
```

`requirements.txt` MAY be added later for full reproducibility.

---

# 3. Project Execution Specification

Each project must run from its own directory:

```
projects/pXX-xxxx/src/main.py
```

### 3.1 Execution Command

Inside activated venv:

```bash
cd projects/pXX-xxxx
python src/main.py
```

### 3.2 Requirements for Project Execution

* Must run without error.
* Must produce deterministic logs where applicable.
* For Sessions & Memory projects:

  * MUST print Session.events (event timeline).
  * If persistent, MUST generate/append SQLite database.
  * If compaction applies, MUST display compacted events.
  * If state applies, MUST show state_delta and session.state.
  * If memory ETL applies, MUST produce memory_store.json.

### 3.3 Notebook Execution (Optional)

If a project includes `notebook.ipynb`, it must be runnable:

```bash
jupyter notebook
```

---

# 4. Git Workflow Specification

## 4.1 Branching Model

Default branch:

```
main
```

Use feature branches optionally:

```
feature/P11-sessions-inmemory
feature/P15-compaction
```

## 4.2 Commit Procedure

After code validation:

```bash
git status
git add .
git commit -m "P11: initial run and event timeline verified"
```

Commit messages MUST follow the format:

```
PXX: description
infra: description
docs: description
module: description
```

Examples:

```
P12: add SQLite persistent session implementation
P15: enable compaction and print compacted_content
infra: initialize repo structure v0.1
docs: add project structure specification
```

## 4.3 First push

```bash
git branch -M main
git remote add origin https://github.com/<username>/adk-decade-of-agents.git
git push -u origin main
```

## 4.4 Subsequent pushes

```bash
git push
```

## 4.5 Git Ignore Policy

Recommended minimal `.gitignore`:

```
.venv/
__pycache__/
*.db
memory_store.json
*.ipynb_checkpoints/
```

---

# 5. Development Loop (Official Cycle)

This is the required workflow for every project iteration:

### **Step 1 — Activate venv**

```bash
source .venv/bin/activate
```

### **Step 2 — Select a project**

```bash
cd projects/pXX-xxxx
```

### **Step 3 — Run for validation**

```bash
python src/main.py
```

### **Step 4 — Confirm output correctness**

* No crashes
* Expected events printed
* Expected memory files generated
* Expected compaction or state behavior observed

### **Step 5 — Commit the validated state**

Return to repo root:

```bash
cd ../..
git add .
git commit -m "PXX: validated behavior and updated documentation"
```

### **Step 6 — Push**

```bash
git push
```

### **Step 7 — Prepare next modification**

Repeat Steps 1–6.

---

# 6. Quality Assurance Specification

Each project commit MUST satisfy:

* Code runs under `.venv`
* Inputs produce expected agent behavior
* Prints or logs MUST align with the project goal:

  * Event timeline
  * State deltas
  * Compaction summaries
  * Memory extraction info
  * Memory injection persona behavior
* No unused directories or files
* Commit message must be descriptive and structured

---

# 7. Repository Structural Requirements

This workflow assumes the following repo layout:

```
adk-decade-of-agents/
├── projects/
├── modules/
├── notebooks/
├── docs/
├── assets/
├── scripts/
└── 0_inbox_raw/
```

Each new project MUST be under:

```
projects/pXX-xxxx/
```

Each project MUST contain:

```
project.card.yaml
README.md
src/main.py
```

---

# 8. Future Enhancements (v1.1 / v1.2)

* Add `scripts/run_project.py` to automate:

  * venv activation
  * project execution
  * output formatting
* Add `scripts/new_project.py` for automatic scaffolding
* Add CI workflow to validate projects on push
* Add tagging system in `project.card.yaml` for filtering

---

# 9. Summary

This specification defines:

* A repeatable development loop
* A structured Git workflow
* A stable virtual environment model
* A consistent execution environment
* The foundation for 50+ ADK mini-projects

Following this spec ensures that every project:

* Runs correctly
* Is reproducible
* Is versioned cleanly
* Fits into the StructureVerse Runtime
* Can evolve into an industrial-grade agent system

---

**End of Specification v1.0**

```

