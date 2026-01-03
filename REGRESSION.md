

---

````md
# REGRESSION.md  
## Season 1 — Life-Cycle Regression Suite (P00–P20A)

## Release Gate
- Gate (blocking): `pytest -q -m gate`
- Legacy (non-blocking): `pytest -q -m legacy`
- Policy: Gate must be green for release; legacy may fail but must be observable/traceable.

This document defines the **canonical regression suite** for **Season 1** of the
**ADK Memory Series / Decade of Agents** project.

This is **not** a feature checklist.
It is a **life-cycle validation**: proving that the system can **exist, persist, isolate, and act with identity**.

Passing this suite means:

> The system has completed one full life cycle and is safe to evolve further.

---

## Scope

**Season 1 Coverage**
- P00 — Life Birth (cold start)
- P10 — System Process & Continuity
- P14 — Session Isolation (Boundary)
- P20A — Persona → Behavior Circuit (Ignition)

**Out of Scope**
- UI correctness
- Model intelligence quality
- Prompt tuning
- External API availability

Season 1 regressions are **structure-first, deterministic, and governance-safe**.

---

## Global Invariants (Must Always Hold)

- No external API keys required for regression
- No network dependency
- Deterministic outcomes
- Re-runnable on a clean machine
- No mutation of historical data outside `runtime_data/`
- All persistent state changes are auditable

---

## Environment Requirements

```bash
Python >= 3.12
venv activated (.venv)
PYTHONPATH=repo root
````

Canonical invocation pattern:

```bash
PYTHONPATH=. python3 <entry>
```

---

## Regression Order (Mandatory)

Regressions **must be run in order**.
Failure at any step blocks all subsequent steps.

---

## P00 — Life Birth (Cold Start)

**Purpose**
Verify the system can be born from nothing, recover from corrupt state, and create a valid memory ontology.

**Command**

```bash
PYTHONPATH=. python3 projects/p00-agent-os-mvp/src/main.py
```

**Acceptance Criteria**

* System starts and exits cleanly
* A new `run_id` is generated
* `runtime_data/memory_store.json` is created and **non-zero**
* JSON is valid and contains a schema version
* Prior corrupt or missing stores do not crash the system

**Failure Meaning**

> The system cannot exist independently of prior state.

---

## P10 — System Process & Continuity

**Purpose**
Verify the system behaves as a long-running process, not a one-shot script.

**Command**

```bash
PYTHONPATH=. python3 projects/p10-minimal-system-process-pack/main.py
```

**Acceptance Criteria**

* Boot mode is explicitly reported (`recover` / `warm`)
* Stable `system_id`
* New `run_id` on each execution
* Second execution does not depend on first
* Persistent artifacts update correctly:

  * events
  * observability
  * memory
* No zombie state or lock residue

**Failure Meaning**

> The system cannot persist over time.

---

## P14 — Session Isolation (Boundary Invariant)

**Purpose**
Verify that multiple sessions (worlds) are strictly isolated within the same runtime.

**Canonical Form (Season 1)**

* **Deterministic Mock Runner**
* No real LLM calls
* No external dependencies

**Command**

```bash
PYTHONPATH=. python3 projects/p14-session-isolation/src/main.py
```

**Acceptance Criteria**

* At least two sessions are created (e.g. session-A, session-B)
* Each session maintains its own independent history
* Events and responses do not cross session boundaries
* Turn counts are isolated per session
* Output explicitly identifies session_id

**Failure Meaning**

> The system cannot be governed or reasoned about safely.

---

## P20A — Persona → Behavior Circuit (Ignition)

**Purpose**
Verify that long-term structure (persona & preferences) directly influences runtime behavior.

**Canonical Form**

* Mocked or deterministic agent selection
* Persona-driven routing
* No reliance on prompt tricks

**Command**

```bash
PYTHONPATH=. python3 projects/p20-preference-aware-router-mocking/src/main.py
```

**Acceptance Criteria**

* Persona state loads successfully
* Preference signals are extracted
* Router decisions are logged and explainable
* Different persona signals lead to different agent selection
* Output behavior matches persona structure

**Failure Meaning**

> Memory and identity exist but do not affect action.

---

## Governance Regression — Repo Hygiene

**Purpose**
Verify repository-level invariants and governance rules.

**Command**

```bash
pytest tests/test_repo_hygiene.py
```

**Acceptance Criteria**

* All tests pass
* No forbidden artifacts tracked
* Structural invariants remain intact

---

## Final Gate — Clean State

```bash
git status
```

**Acceptance Criteria**

* Working tree clean
* No untracked runtime artifacts
* No accidental commits during regression

---

## Pass Condition (Season 1)

Season 1 regression **passes** if and only if:

* P00 ✅
* P10 ✅
* P14 ✅
* P20A ✅
* Repo hygiene ✅
* Clean git state ✅

At this point the system is considered:

> **A living, governable, identity-bearing agent system**

---

## Post-Regression Rules

* `main` is considered **Season 1 frozen**
* No experimental features may be added to `main`
* All new development must occur on feature or season branches
* Future regressions must extend, not rewrite, this document

---

## Historical Note

Season 1 is the first time the system completed a full life cycle:
birth → persistence → boundary → identity → action.

Future seasons build on this foundation.

```

---

```
