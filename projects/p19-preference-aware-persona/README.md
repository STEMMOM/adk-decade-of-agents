# P19 — Preference-Aware Persona

A lightweight runner that loads structured preferences from `memory_store.json`, compiles them into a stable persona, saves the result to `persona_state.json`, and prints a concise summary for verification.

## Overview
- Aggregates list-style preferences (interests, dislikes, format_preferences) and scalar preferences (answer_style) with confidence tracking.
- Builds a v1 persona schema that can be reused across sessions and downstream projects.
- Emits a human-readable summary so you can quickly confirm the persona fields.

## Prerequisites
- Python 3.10+ available locally.
- Dependencies from the ADK basic setup (`python_basic_setup`, `adk_install`).
- A populated `memory_store.json` with `preferences` and optional `user_profile`.

## How to Run
```bash
python src/main.py
```
Output appears in the console, and the persona file is written to `persona_state.json` at the project root.

## Inputs and Outputs
- **Input**: `memory_store.json`
  - Expected keys: `preferences` (list of preference objects), `user_profile` (optional identity fields), plus any metadata.
- **Output**: `persona_state.json`
  - Fields include `id`, `name`, `interests`, `dislikes`, `format_preferences`, `answer_style`, confidence scores, and source traceability.
  - The description string is auto-generated from available profile and preference data.

## Key Files
- `src/main.py` — Loads memory, aggregates preferences, builds and saves the persona, and prints the summary.
- `memory_store.json` — Source of preferences and optional user profile.
- `persona_state.json` — Generated persona artifact ready for reuse by later projects.

## Notes
- If `memory_store.json` is missing or malformed, the runner falls back to an empty skeleton and still produces a minimal persona.
- Preferences not provided in list form are normalized to lists where applicable; the highest-confidence scalar value is chosen for `answer_style`.
