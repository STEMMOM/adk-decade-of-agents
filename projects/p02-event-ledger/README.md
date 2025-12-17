# P02 — Stateful Sessions & In-Memory Event Ledger

Series: Decade of Agents (P01–P10)  
Status: Active  
Mode: In-Memory Runtime Cache (no persistence)  
Goal: Record every agent action as structured events stored only in Python memory.

---

## 1. What P02 Is

P02 gives the agent its first internal world. Unlike P01, which forgot everything after a single run, P02 wraps each run in a Session with an append-only Event Ledger. The ledger captures user messages, tool calls, tool results, outputs, errors, and timestamps, all kept in Python RAM only.

## 2. Why In-Memory Mode?

P02 shapes the structure of agent memory before persistence exists. Keeping events in memory makes debugging clean, iteration fast, and side-effects zero. It mirrors real runtimes: ephemeral session memory now; long-term memory arrives later in P04.

## 3. Event Ledger (Cache Mode)

```python
class InMemoryLedger:
    def __init__(self):
        self.events = []  # stored only in Python RAM
```

Events are appended as:

```python
{
    "type": "...",
    "timestamp": "...",
    "data": {...},
}
```

When the Python process ends, the session and ledger vanish. That is intentional.

## 4. Execution Pipeline

1. User message  
2. `session.ledger.add("user_message")`  
3. `agent.run_once()`  
4. `session.ledger.add("tool_call")`  
5. Model executes  
6. `session.ledger.add("tool_result")`  
7. `session.ledger.add("final_output")`  

Each step becomes a structured event.

## 5. How to Run P02

```bash
cd projects/p02-event-ledger
python src/main.py
```

You should see a new session ID, the agent output, and a printed JSON ledger containing four structured events. If you see these, P02 is alive.

## 6. Relationship to Future Projects

- P03: convert events → logs, traces, metrics  
- P04: extract long-term memory from session.events  
- P05: planner reasons over event chains  
- P07: router chooses models based on event history  
- P08: agents coordinate via ledgered messages  
- P09: governance requires event audit  
- P10: self-evolution is powered by past events  

## 7. Summary

P02 delivers the agent’s first session, timeline, and structural (temporary) memory. Everything lives in Python runtime memory by design. This is not persistence; it is agency.
