# P13 — DB Inspector (Event Ledger Microscope)

## 🎯 Project Goal

P13 builds a small but extremely important tool: a direct inspector for the ADK event ledger stored in SQLite.

This project:

- loads the SQLite file (`day3_sessions.db`) created in P12
- reads the underlying `events` table
- prints every event in chronological order
- displays `session_id`, author (user/agent), timestamp, and text content (decoded from JSON)

This is the first tool that allows you to audit an ADK agent from outside ADK.

## 🧠 Why this is important

- P11 created the event timeline in memory
- P12 wrote it into a persistent SQLite ledger
- P13 provides the microscope to examine that ledger directly

This enables debugging, verification, reproducibility, data provenance, safety/auditability, and future evaluation pipelines.

## 🚀 Usage

1) Generate the SQLite ledger (run P12 at least once):

```bash
python projects/p12-stateful-db-session/src/main.py
```

2) Inspect the events with P13:

```bash
python projects/p13-db-inspector/src/main.py
```

Expected output: a pretty-printed chronological event timeline sourced directly from `day3_sessions.db`.
