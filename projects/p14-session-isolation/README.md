# P14 — Session Isolation Test (Parallel Universes)

## 🎯 Project Goal

Proves a critical property of ADK sessions:

> **Different sessions are completely isolated universes.**

Specifically, P14:

1. Creates two separate sessions: `session-A` and `session-B`.
2. In `session-A`, the user tells the agent: “Hi, I am Sam!” and then asks: “What is my name?”
3. In `session-B`, the user directly asks: “What is my name?” without prior introduction.
4. Prints both `Session.events` timelines to verify:
   - A remembers “Sam.”
   - B does **not** know the name.
   - The two event timelines do not mix.

---

## 🧠 Why It Matters

This test demonstrates that ADK’s Session model is **structurally isolated**:

- Each session is identified by `(app_name, user_id, session_id)`.
- Events in different sessions never leak into each other.
- You can safely run multiple users, tasks, and agents in parallel without cross-contamination of context.

In StructureVerse terms:

> Each Session is a self-contained **structure bubble** (a mini-universe of events).  
> P14 is the first formal proof that these bubbles have clean boundaries.

---

## 🚀 How to Run

1. `cd /Users/Agent/adk-decade-of-agents`
2. `source .venv/bin/activate`
3. `cd projects/p14-session-isolation`
4. `python src/main.py`

Expected result:

- Logs indicating creation of Session A and Session B.
- Session A remembers “Sam.”
- Session B does not know the name.
- Two separate event timelines printed: `SESSION A EVENTS` and `SESSION B EVENTS`.
