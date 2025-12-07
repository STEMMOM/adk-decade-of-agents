
---


# ADK Decade-of-Agents — Project Structure Specification (v0.1)

**version:** 0.1  
**status:** draft  
**scope:** Applies to the entire repository for the “ADK 50+ Mini-Projects” curriculum.

---

## 0. Repository Purpose

- **Repository Name (recommended):** `adk-decade-of-agents`
- **Goal:**  
  Host ~50 ultra-small, highly executable mini-projects built around the Google Agent Development Kit (ADK).  
  Together, they form the foundational **digital literacy for the decade of agents (2025–2035)**.

- **Design Principles:**
  - Everything is organized around **Projects**.
  - Each project is a **Structure Card** — independently runnable, independently learnable.
  - All code and documentation are versioned, portable, and long-term maintainable.

---

## 1. Top-Level Directory Structure

The repository follows this standardized structure:

```text
adk-decade-of-agents/
├── README.md              # Repository overview (EN/CH)
├── PROJECTS.md            # 50+ project index (skill map)
├── projects/              # All executable project cells
├── modules/               # Conceptual teaching modules
├── notebooks/             # Kaggle / Jupyter notebooks
├── docs/                  # Specifications, long-form explanations
├── assets/                # Images, diagrams, covers
├── scripts/               # Utilities (e.g., project generator)
└── 0_inbox_raw/           # Cold storage of historical experiments (read-only)
````

### 1.1 Top-Level File Descriptions

* **README.md**

  * Overview of the repository, goals, and navigation.
* **PROJECTS.md**

  * List of all mini-projects.
  * Shows: project ID, status, level, corresponding folder.
* **0_inbox_raw/**

  * A sandbox for raw historical code and notebooks.
  * Never modify code inside; used only as reference/import.

---

## 2. Project Directory Specification (`projects/`)

Every executable mini-project must live inside the `projects/` directory.

### 2.1 Naming Rules

Directory name format:

```
pXX-short-slug/
```

Examples:

```
p01-minimal-agent/
p02-stateful-db-agent/
p03-memory-schema-agent/
```

Rules:

* `p` + two-digit project number (P01 → p01)
* `short-slug` must be lowercase, hyphen-delimited.

---

### 2.2 Standard Internal Structure of Each Project

```text
projects/pXX-short-slug/
├── README.md             # Human-facing explanation
├── project.card.yaml     # Machine-readable metadata (Structure Card)
├── src/                  # Executable code
│   └── main.py           # Entry point
├── notebook.ipynb        # (Optional) Jupyter/Kaggle notebook version
└── tests/                # (Optional) Lightweight sanity checks
```

Descriptions:

* **src/**
  Contains all Python / ADK code.
  Every project must execute via:

  ```
  python src/main.py
  ```

* **project.card.yaml**
  The structured “Project Card” metadata (explained in Section 3).

---

## 3. `project.card.yaml` Metadata Specification

Each project is treated as a **Structure Card**.
Metadata is stored in YAML to enable:

* automatic documentation generation
* dependency graphs
* module learning paths
* project querying and filtering

### 3.1 Field Definition (v0.1)

```yaml
id: P01                    # Required — Project ID
slug: minimal-agent        # Required — Directory slug
title_en: ...              # Required — English title
title_zh: ...              # Required — Chinese title
module: m01_adk_basics     # Required — Parent module
level: 1                   # Required — Difficulty (1=beginner, 2=intermediate, 3=advanced)
status: draft              # Required — draft | beta | stable

goal:                      # Required — 2 to 5 learning goals
  - ...
  - ...

prerequisites:             # Optional — Required prior skills or project IDs
  - python_basic_setup
  - adk_install
  - project:P01

skills:                    # Optional — Skills trained in this project
  - adk.LlmAgent
  - structured_memory
  - tool.google_search

entrypoint: src/main.py    # Required — Code entry point
estimated_time_min: 45     # Optional — Approximate completion time

outputs:                   # Optional — Expected artifacts
  - "A working CLI demo that answers a real-time query."

links:                     # Optional — External references
  substack: ""             # Substack article about this project
  kaggle: ""               # Kaggle notebook
  notes: ""                # Additional references
```

---

### 3.2 Example `project.card.yaml`

```yaml
id: P01
slug: minimal-agent
title_en: Minimal Stateful Agent Cell
title_zh: 最小有记忆 Agent 细胞
module: m01_adk_basics
level: 1
status: draft

goal:
  - Build one Agent + one Runner + one Tool.
  - Demonstrate the first "breath" of an agent: call Google Search.

prerequisites:
  - python_basic_setup
  - adk_install

skills:
  - adk.LlmAgent
  - adk.InMemorySessionService
  - adk.Runner
  - tool.google_search

entrypoint: src/main.py
estimated_time_min: 30

outputs:
  - "A working CLI demo that answers a real-time query with Google Search."

links:
  substack: ""
  kaggle: ""
  notes: ""
```

---

## 4. Module Directory Specification (`modules/`)

Modules represent **conceptual groupings**, not code.

Examples:

```
modules/
├── m01_adk_basics/
├── m02_mcp_tools/
├── m03_sessions_memory/
├── m04_agent_quality/
└── m05_production_a2a/
```

### 4.1 Module Directory Layout

```text
modules/m01_adk_basics/
├── README.md            # What this module teaches
├── flow.md              # Learning order, dependency graph
└── diagrams/            # Mermaid diagrams / images
```

Modules **do not contain code**.
All executable work lives under `projects/`.

---

## 5. Project Index Specification (`PROJECTS.md`)

This file provides a single view of all mini-projects.

### 5.1 Example Foundation

```markdown
# ADK Decade-of-Agents — Mini Projects Map

> Completing this table = completing the 2025 ADK Agent Literacy Path.

## Module 1 — ADK Basics (m01_adk_basics)

| ID   | Project                                   | Status | Level | Folder                        |
|------|-------------------------------------------|--------|-------|-------------------------------|
| P01  | Minimal Stateful Agent                    | draft  | 1     | `projects/p01-minimal-agent/` |
| P02  | SQLite Persistent Agent                   | draft  | 2     | `projects/p02-stateful-db-agent/` |
```

The table expands as the repository grows.

---

## 6. Notebook Directory Specification (`notebooks/`)

* All standalone notebooks go here.
* If a notebook belongs to a specific project, place it inside that project directory as `notebook.ipynb`.

Example:

```
notebooks/
├── module1_overview.ipynb
├── module2_mcp_security.ipynb
└── ...
```

---

## 7. Documentation & Assets

### 7.1 `docs/`

Holds:

* long-form documentation
* specifications
* architecture files

Examples:

```
docs/
├── PROJECT_STRUCTURE_v0.1.md
├── ADK_SETUP_GUIDE.md
└── MCP_SOVEREIGNTY_LAYER_DESIGN.md
```

### 7.2 `assets/`

Holds images, diagrams, icons.

```
assets/
├── module1/
└── projects/
```

---

## 8. Scripts (`scripts/`)

Utility scripts, e.g.:

* **new_project.py**
  Generates skeleton for a new project:

  * folder
  * README.md
  * project.card.yaml
* Auto-generate `PROJECTS.md` from all `project.card.yaml` files.

---

## 9. Git Workflow (v0.1)

* Default branch: `main`
* Commit message convention:

```
P01: init minimal agent project
P02: add SQLite session example
infra: add project structure spec v0.1
```

Workflow:

1. Create new folder under `projects/`
2. Add `project.card.yaml`
3. Register the project in `PROJECTS.md`
4. Commit and push

---

## 10. Future Versions

* **v0.2**

  * Add tags, difficulty_score fields for project filtering
  * Introduce automatic project scaffolding
* **v0.3**

  * Add minimal test specs for every project
  * Add Structure Card six-field mapping (Name/Goal/Input/Mechanism/Condition/Output)

---

**End of Specification (v0.1)**

````

---


