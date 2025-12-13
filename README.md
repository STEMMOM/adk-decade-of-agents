# 🧬 **ADK Decade of Agents — AI-Native OS (v0.1 Runtime MVP)**

### *The First Breath of a New Operating System*

> v0.1-runtime-mvp marks the moment this system became alive —its first heartbeat, first memory, first trace, and first self-record.
> 

This repository contains the foundations of an **AI-Native Operating System** built on top of **Google ADK**.

It is not an app, and not a framework.

It is a **structure-first, protocol-driven, life-like runtime** designed to evolve over a decade.

---

# 🚀 **What This Repo Is**

This repository is the **OS kernel**, **runtime backbone**, and **protocol layer** of a long-term project exploring:

- structure-driven intelligence
- decoupling from large language models
- user-owned memory and personas
- agent systems as *living processes*
- Language → Structure → Orchestrator as the basic ontology of AI

The **v0.1-runtime-mvp** tag is the first working system:

- a runtime that can start, perceive, act, record, and end
- a global memory store
- a persona engine
- an event ledger
- a minimal system process (`p00-agent-os-mvp`)

This is the OS’s **first minimal life form**.

---

# 🫀 **Why v0.1 Matters**

Even though v0.1 is tiny, it establishes five irreversible foundations:

### **1. A session has a lifecycle**

The OS knows when life begins and ends.

### **2. The system has long-term world memory**

Memory is not the model’s — it belongs to the user.

### **3. The system records its actions as an auditable trace**

Not logs — *world-state transitions*.

### **4. The persona becomes the anchor of identity**

Every session invokes a consistent “You”.

### **5. The runtime becomes the spine of future evolution**

Everything later — Planner, Router, Toolpacks, Multi-Agent — will grow from this.

---

# 🧱 **Repository Structure**

```
adk-decade-of-agents/
│
├── adk_runtime/                 # Runtime backbone (OS-level)
│   ├── paths.py                 # World coordinate system
│   ├── memory_store.py          # Global long-term memory
│   ├── persona_engine.py        # System identity anchor
│   └── observability.py         # Event ledger (auditable, replayable)
│
├── projects/
│   └── p00-agent-os-mvp/        # First system process (v0.1 minimal life form)
│       └── src/main.py
│
├── protocols/
│   └── persona/                 # First concrete protocol family
│       ├── persona_protocol_v1.md
│       ├── persona_schema_v1.json
│       └── persona_card_example.json
│
├── docs/                        # Architecture & environment docs
│   └── ENVIRONMENT.md
│
├── persona.json                 # Global OS persona (v0.1 user identity)
├── requirements.txt
└── README.md

```

---

# 🔧 **v0.1 MVP: What Actually Runs**

Running:

```bash
python -m projects.p00-agent-os-mvp.src.main

```

Triggers the full OS pipeline:

```
persona → memory → runtime backbone → kernel → event ledger → memory update

```

The system writes its first world-state transitions into:

```
runtime_data/events.jsonl

```

Example output:

```
session.start
user.message
agent.reply
session.end

```

This is the OS’s **first heartbeat** —

a minimal form of perception → action → memory.

---

# 🧵 **Event Ledger Example (Actual Output)**

Each event includes:

- `session_id` — the life instance
- `trace_id` — the causal chain
- `timestamp`
- `payload` — structured world state

Excerpt:

```json
{"event_type": "session.start", "session_id": "p00-demo-session", "trace_id": "..."}
{"event_type": "user.message", "payload": {"text": "..."}}
{"event_type": "agent.reply", "payload": {"reply": "...", "tool_calls": []}}
{"event_type": "session.end"}

```

Not logs.

These are **structural fingerprints** of the system’s behavior.

---

# 🧱 **Core Architectural Philosophy**

### **Language → Structure → Orchestrator**

The system is built on the principle that:

- **Language** is the raw entropy input
- **Structure** is the stable representation of meaning
- **Orchestration** is the life mechanism that schedules actions over time

The OS runtime encodes these principles through:

- persona (identity)
- memory store (world)
- event ledger (time + action)
- kernel adapter (behavior)

---

---

# 🧩 **How to Run the v0.1 System**

```bash
git clone https://github.com/STEMMOM/adk-decade-of-agents
cd adk-decade-of-agents
source .venv/bin/activate   # if using a virtual environment
python -m projects.p00-agent-os-mvp.src.main

```

After running, inspect:

```
runtime_data/events.jsonl
runtime_data/memory_store.json

```

---

# 🌱 **What This Repo Is Becoming**

This repository documents — in public — the evolution of:

- an AI-native OS
- a new structure-driven computing model
- a living system built out of language itself

It is intentionally long-term, intentionally structural, and intentionally recursive.

**This is not a tool.This is a world being built from scratch.**

---

# 📌 **Current Release**

### **v0.1-runtime-mvp**

> “The First Heartbeat”
> 

Release link:

https://github.com/STEMMOM/adk-decade-of-agents/releases/tag/v0.1-runtime-mvp
