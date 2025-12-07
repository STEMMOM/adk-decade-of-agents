# P15 — Context Compaction Demo (Automatic Summarization)

## 🎯 Project Goal
This project demonstrates automatic context summarization enabled by `EventsCompactionConfig` inside an ADK `App`. P15 shows how ADK can:
- Monitor the event timeline (`Session.events`)
- Detect when the number of events crosses a threshold
- Automatically generate a summary event
- Replace older events with a compacted low-entropy summary
- Preserve the most recent events using overlap

In other words:

> P11 = Event Timeline  
> P12 = Persistent Timeline  
> P13 = Observable Timeline  
> **P15 = Compressible Timeline**

This is the first engineering implementation of the entropy-control principle.

---

## 🧠 Why This Matters
LLMs cannot consume infinite context. Real agent systems require:
- summarization
- compaction
- entropy reduction
- retention of salient information
- forgetting irrelevant past

P15 implements this as a built-in ADK feature, not manual prompt logic. This is crucial for:
- long-running conversations
- stateful agents
- memory ETL
- long-horizon planning
- bounded-complexity reasoning

---

## 🚀 How to Run
```bash
cd /Users/Agent/adk-decade-of-agents
source .venv/bin/activate
cd projects/p15-compaction-demo
python src/main.py
```

You should see:
- an App configured with `EventsCompactionConfig`
- multiple user messages
- a compaction event automatically inserted
- a summary printed out at the end
