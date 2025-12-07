# P16 — Compacted Persona Memory ETL Demo
### StructureVerse Runtime · Sessions & Memory · Persona Line

## 📌 Overview

P16 shifts the Sessions & Memory arc from compacting technical conversations to **persona-driven compaction**:

- The agent receives structured information about the user.
- ADK automatically compacts the conversation.
- The compacted summaries are written into long-term memory.

This creates the first *Persona Seed* that supports P17–P20:

- P17 — Memory Schema v1
- P18 — Preference Extraction
- P19 — Values & Knowledge Extraction
- P20 — Persona Builder v1

P16 is the bridge from raw conversational identity to structured long-term persona memory.

## 🎯 What This Project Shows

1) A profiling-style Agent with strict markdown structure rules (Identity · Background · Interests · Work Style · Preferences · Values · Anti-Preferences).  
2) The user reveals structured persona information: name, origin, location, interests, hobbies, communication preferences, values, and dislikes/anti-preferences.  
3) Compaction automatically fires via `EventsCompactionConfig`.  
4) Compaction summaries (persona snapshots) are extracted from `Session.events`.  
5) Summaries are saved into `memory_store.json` under `conversation_summaries[]` for downstream projects (P17–P20).

## 📁 Project Structure

```text
p16-compacted-memory-etl-user-persona/
├── README.md
├── project.card.yaml
├── memory_store.json   # Long-term memory after running this project
└── src/
    └── main.py
```

## 🚀 How to Run

From the project directory:

```bash
(.venv) cd projects/p16-compacted-memory-etl-user-persona
(.venv) python src/main.py
```

The script will start a fresh session, run a structured persona-building dialogue, trigger compaction, extract summaries, and write them into `memory_store.json`.

## 📦 Output Format

After running, `memory_store.json` will contain content like:

```json
{
  "conversation_summaries": [
    {
      "app_name": "agents",
      "user_id": "susan",
      "session_id": "compacted-persona-demo",
      "created_at": "...",
      "summary_text": "The user, Susan, is providing information to build a persistent personal profile...",
      "raw": { "...": "..." }
    }
  ]
}
```

## 🧱 System Importance

- Establishes the Persona Compaction Layer.  
- Provides a clean, structured summary of the user.  
- Produces a stable, compacted memory artifact consumed by P17–P20.  
- Marks the first long-term, structured persona memory for the agent.

## 🔗 Next Steps

- P17 — Upgrade this memory to a versioned schema.  
- P18 — Extract Preferences.  
- P19 — Extract Work Style, Values, Knowledge.  
- P20 — Build a fully structured Persona Card.
