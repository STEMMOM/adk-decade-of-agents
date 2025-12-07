# P20A — Preference-Aware Router (ADK Version)

**ID:** P20A  
**Folder:** `projects/p20-preference-aware-router-ADK`  
**Status:** draft  
**Module:** `m03_sessions_memory`

ADK-backed evolution of the Preference-Aware Router. It extends **P18 — Preference Extraction** and **P19 — Preference-Aware Persona** by turning Persona fields into routing decisions that choose between real ADK `LlmAgent`s and produce Gemini model outputs.

## Concept: Persona → Policy → Real Agents

The system ties long-term Persona structure to real-time agent behavior:

1. **Load Persona:** Read `persona_state.json` (produced by P19).
2. **Derive Policy:** Map Persona fields (`answer_style`, `format_preferences`, `dislikes`) into routing flags (`prefer_structured_output`, `prefer_code_examples`, `avoid_marketing_style`, `default_agent`).
3. **Build Agents:** Configure two ADK agents: `structured_agent` and `narrative_agent`.
4. **Route & Run:** Choose an agent via the policy, then execute with `Runner`, `InMemorySessionService`, and a real Gemini call.
5. **Print Output:** Display the live LLM response.

## Project Structure

```text
projects/p20-preference-aware-router-ADK/
├── README.md
├── project.card.yaml
├── persona_state.json      # Input (from P19)
└── src/
    └── main.py             # ADK routing runtime
```

- `persona_state.json`: Must exist from P19; read-only for this project.  
- `src/main.py`: Loads persona, derives policy, builds agents, runs ADK, prints the response.

## How to Run

From the repository root:

1. `source .venv/bin/activate`
2. `cd projects/p20-preference-aware-router-ADK`
3. `python src/main.py`

Prerequisites:
- `.env` contains a valid `gsk_` Gemini API key.
- The project tied to the key has Billing enabled.
- `persona_state.json` is present from P19.

## Expected Output

A typical run shows persona load, policy extraction, routing, and the real ADK response. Example shape:

```
🚀 P20A — Preference-Aware Router (ADK) v1 started
📥 Loading persona ...
🎭 Persona Signals
🧭 Routing Policy
→ selected agent: structured_agent

🤖 ADK Agent Response
---------------------
<Gemini LLM response here>

🏁 P20A — Preference-Aware Router (ADK) v1 finished
```

This confirms routing logic plus real LLM inference.

## Files Touched

- Input: `persona_state.json` (read-only).
- Output: None (v1) — console logs only. Future versions may log routing decisions to JSON/SQLite.

## Development Loop

- Activate venv.
- Run P19 if Persona changed.
- Run this project.
- Validate: Persona signals render, policy derivation matches expectations, chosen agent aligns with Persona, ADK response appears.
- From repo root to commit:
  - `cd ../..`
  - `git add .`
  - `git commit -m "P20A: enable preference-driven ADK agent routing"`
  - `git push`

## Future Extensions

- Fallback to mock agent when ADK quota errors occur.
- Persist routing decisions in `routing_log.json`.
- Add tool routing (search, code execution) based on Persona.
- Control reasoning depth per Persona.
- Expand to a multi-agent routing mesh.

P20A is the first version where the agent’s behavioral path is fully driven by long-term user structure.
