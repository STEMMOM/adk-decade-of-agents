# P17 — Memory Schema v1 Upgrade
### StructureVerse Runtime · Sessions & Memory · Schema Layer

## 📌 Overview
P17 introduces the first formal long-term memory schema in the StructureVerse Runtime. Earlier projects (P15–P16) produced raw, ad-hoc JSON. P17 upgrades that into a versioned, typed container ready for downstream ETL.

```json
{
  "schema_version": "1.0",
  "user_profile": {},
  "conversation_summaries": [],
  "preferences": [],
  "knowledge": []
}
```

## 🎯 Goals
- Load the legacy `memory_store.json` produced by P16.
- Normalize and upgrade it into Memory Schema v1 with versioning.
- Split long-term memory into typed channels: `user_profile`, `conversation_summaries`, `preferences`, `knowledge`.
- Save the upgraded memory back to the same file (in-place upgrade).

## 📁 Project Structure
```
p17-memory-schema/
├── README.md
├── project.card.yaml
├── memory_store.json        # copy from P16 before running
└── src/
    └── main.py              # schema upgrader script
```

## 🚀 How to Run
1) Copy in your P16 memory:
```
cp ../p16-compacted-memory-etl-user-persona/memory_store.json .
```
2) Run the upgrader:
```
(.venv) cd projects/p17-memory-schema
(.venv) python src/main.py
```

## ✅ Expected Output
Example log:
```
schema_version: 1.0
user_profile keys: []
conversation_summaries: 4
preferences: 0
knowledge: 0
💾 Saved Memory Schema v1 to memory_store.json
```

## 🧬 Why This Matters
- Creates the first stable, structured long-term memory container.
- Enables preference extraction (P18), knowledge extraction (P19), and persona builder (P20).
- Sets a foundation for schedulable, composable memory operations across the runtime.

## 🔗 Next Steps
- P18 → Extract user preferences into `preferences[]`.
- P19 → Extract values, work-style, and knowledge into `knowledge[]`.
- P20 → Build a complete Persona Card from schema-structured memory.
