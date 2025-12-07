# P18 — Preference Extraction

**ID:** P18  
**Folder:** `projects/p18-preference-extraction`  
**Status:** draft  
**Module:** `m03_sessions_memory`

This project implements a Preference Extraction cell on top of the ADK Sessions & Memory stack. It reads conversation summaries from `memory_store.json`, extracts structured user preferences (interests, answer style, dislikes, format preferences, etc.) with confidence scores, merges them with existing entries, and writes them back into long-term memory. The goal is to build agents that persistently “know you” across sessions.

---

## 1. Project Goals

- Read ADK conversation summaries from `memory_store.json`.
- Extract structured preferences as `(key, value, confidence, source)` objects.
- Deduplicate and merge preferences while handling conflicts.
- Update `memory_store.json` in place.
- Print a deterministic run summary (counts for summaries scanned, existing preferences, new preferences, and total preferences).

---

## 2. Prerequisites

Environment:
- Python environment with `.venv` created at the repo root.
- ADK installed and working.
- At least one ADK session that produced `memory_store.json` with `conversation_summaries`.

Recommended background:
- `python_basic_setup`
- `adk_install`
- Project P11 / P15 or other Sessions & Memory projects that generate `memory_store.json`

---

## 3. Project Structure

```text
projects/p18-preference-extraction/
├── README.md
├── project.card.yaml
└── src/
    └── main.py
```

- `src/main.py`: main entry point; loads memory, parses `conversation_summaries`, extracts preferences with confidence, merges them, saves back to `memory_store.json`, and prints the summary.

---

## 4. How to Run

All commands assume the repository root (`adk-decade-of-agents/`).

```bash
# 4.1 Activate the virtual environment
source .venv/bin/activate

# 4.2 Run the project
cd projects/p18-preference-extraction
python src/main.py
```

You should see the shell prompt prefixed with `(.venv)` after activation.

---

## 5. Expected Behavior & Output

A successful run:
- Loads `memory_store.json` from the configured path.
- Reads `conversation_summaries` and existing preferences.
- Extracts and merges preferences without crashing.
- Writes the updated `memory_store.json`.
- Prints a deterministic summary similar to:

```text
🚀 P18 — Preference Extraction v1 started
📥 Loading memory from: /Users/Agent/adk-decade-of-agents/projects/p18-preference-extraction/memory_store.json
✅ Memory loaded successfully.

🧬 Preference Extraction Summary
--------------------------------
- conversation_summaries seen: 4
- existing preferences: 0
- new preferences extracted: 5
- total preferences: 5

📚 preferences (truncated preview):
[
  {
    "key": "interests",
    "value": [
      "reading_sci_fi",
      "building_agent_projects",
      "math_logic_games_with_children"
    ],
    "confidence": 0.85,
    "source": "conversation_summaries[0]"
  },
  ...
]

🏁 P18 — Preference Extraction v1 finished
```

Exact counts may vary, but logs should be stable across runs given the same input memory file.

---

## 6. Files Produced / Touched

- `memory_store.json` (in-place update; no extra files created by default).
- Optional debug outputs should be opt-in and clearly named (e.g., `debug_preferences.json`), and disabled by default.

---

## 7. Development Loop (per SPEC)

```bash
source .venv/bin/activate
cd projects/p18-preference-extraction
python src/main.py
```

Validate that:
- No exceptions occur.
- The run summary prints.
- `memory_store.json` updates as expected.

---

## 8. Extending P18

Future iterations (P18 v1.1 / v1.2) may add:
- Stronger schemas for preference categories (interests, dislikes, answer_style, format_preferences, etc.).
- More sophisticated confidence aggregation (source weights, recency bias).
- Optional export to `preferences.json`.
- Integration with a Preference-Aware Persona Builder (P19).
