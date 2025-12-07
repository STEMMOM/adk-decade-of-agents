# P12 — First Cross-Process Stateful Agent (SQLite Sessions)

## 🎯 Project Goal

This project extends P11 (“InMemory sessions”) and proves **persistent sessions**:

1. Use `DatabaseSessionService` to store all `Session.events` into a local SQLite file `day3_sessions.db`.
2. Reuse the same `session_id` across multiple runs and show that the agent still “remembers” you.
3. Read the underlying `events` table directly with `sqlite3` to verify that the event ledger is truly written to disk.

In other words:

> P11 gave the agent an external **short-term brain** (in-memory event timeline).  
> P12 gives it a **disk-backed brain** — an event ledger that survives process restarts.

---

## 🧩 Files

- `src/main.py`  
  The main script (refactored from your original `stateful_db.py`), using `DatabaseSessionService` + SQLite.
- `project.card.yaml`  
  Metadata card describing this project (ID, goals, skills, etc.).

---

## 🚀 How to Run

1. Activate the virtual environment:

```bash
cd /Users/Agent/adk-decade-of-agents
source .venv/bin/activate
```

2. Run P12 (run it twice to see persistence):

```bash
cd projects/p12-stateful-db-session
python src/main.py
```

What you should see:

- First run:
  - A new persistent session is created.
  - The agent learns “I am Sam”.
  - The SQLite file `day3_sessions.db` is created.
- Second run:
  - The script reuses the existing session.
  - The agent still knows your name without re-introduction.
  - The raw `events` table is printed from SQLite, confirming persistence.
