# Persona Protocol v1.0 — Identity Contract for AI-Native Agents
Entropy-Controlled StructureVerse × ADK Runtime Specification

## 0. Metadata
- Protocol-Name: Persona Protocol
- Protocol-Version: 1.0
- Protocol-Type: Identity & Preference Contract
- Applies-To: All Agents, Runtimes, and Sessions
- Author: Entropy Control Theory (ECT)
- Status: Stable

## 1. Purpose
- Define the identity layer of an AI-native agent system.
- Establish a structured, stable representation of who the user is.
- Guide model behavior, tool routing, and planning preferences.
- Provide an ETL pipeline from event logs → memory → persona.
- Enable auditable, evolvable long-term personalization.
- Support multi-agent identity sharing with explicit governance.
- Minimize entropy by enforcing structure-first reasoning patterns.

Persona is not a prompt; it is a contract that governs how the agent should think, behave, and adapt on behalf of the user.

## 2. Protocol Schema
A valid Persona must follow this structure:

```json
{
  "id": "string",
  "version": "string",
  "card_type": "persona",
  "identity": {
    "user_name": "string",
    "roles": ["string"],
    "background": {
      "country": "string or null",
      "locale": "string or null"
    }
  },
  "traits": {
    "thinking_style": "string",
    "reasoning_bias": ["string"],
    "temperament": ["string"],
    "confidence": 0.0
  },
  "preferences": {
    "interests": ["string"],
    "interests_confidence": 0.0,
    "dislikes": ["string"],
    "dislikes_confidence": 0.0
  },
  "format_rules": {
    "preferred_formats": ["string"],
    "format_preferences_confidence": 0.0
  },
  "style_rules": {
    "answer_style": "string",
    "answer_style_confidence": 0.0
  },
  "behavior_rules": {
    "high_level": ["string"],
    "interaction": ["string"]
  },
  "update_rules": {
    "when_to_update": "string",
    "how_to_update": "string",
    "conflict_resolution": "string"
  },
  "sources": {
    "interests": ["string"],
    "dislikes": ["string"],
    "format_preferences": ["string"],
    "answer_style": ["string"]
  }
}
```

This schema ensures consistency, audibility, and tooling compatibility across the runtime.

## 3. Persona Lifecycle
Persona evolves through a structured multi-stage pipeline:
Events → ETL → Memory Store → Persona Card → Injection → Runtime Updates → Reconciliation

### 3.1 Event → ETL
Extract stable signals from Session.events:
- Preferences
- Task habits
- Writing style
- Reasoning patterns
- Emotional tendencies
- Tool usage patterns

### 3.2 ETL → Memory Store
- Persist to `memory_store.json` as atomic facts.

### 3.3 Memory → Persona Card
- Periodic compaction and merging into the formal Persona structure.

### 3.4 Persona Injection
- Injected at `session.start` → before first model call → before router decisions.
- Influences formatting, reasoning style, planning, routing choices, tool selection, and agent tone/interaction style.

### 3.5 Runtime Updates
- Persona signals accumulated in a buffer during the session.

### 3.6 Reconciliation
- Every N sessions: merge new traits, update confidences, remove noise, enforce structure, re-evaluate S-index.

## 4. Scheduling Rules
Persona directly influences the agent runtime.

### 4.1 Model Routing
- Concise style → prefer fast models.
- Deep reasoning → switch to smart models.
- Code preference → route to code model.

### 4.2 Planner Behavior
- Persona controls granularity of plans, number of steps, retry thresholds, and verbosity of reasoning traces.

### 4.3 Tool Routing
- Preferences affect lookup vs synthesis, proactive use of tools, and cautious verification patterns.

### 4.4 Multi-Agent Protocol
- Persona may be shared or isolated depending on ACL rules.

## 5. Update Rules
Persona updates must be deliberate, not reactive.

### 5.1 Stability Threshold
- Update only when signal repeats across ≥ 3 independent sessions.
- Confidence increases by ≥ 0.25.
- S-index ≥ 0.7 (high structure signal).

### 5.2 Conflict Resolution
Priority order:
- Higher confidence.
- More recent evidence.
- Higher-structure evidence (S-index).
- Explicit user statements override implicit extraction.

### 5.3 Immutable Fields
- `user_name`
- Core identity
- Long-term roles
Unless the user explicitly revises them.

## 6. Governance & ACL
Persona access is controlled by a strict ACL matrix.

| Field        | Planner | Researcher | Writer | Critic |
|--------------|---------|------------|--------|--------|
| traits       | R       | R          | R      | R      |
| preferences  | R       | R          | R/W    | R      |
| format_rules | R       | R          | R      | W      |
| update_rules | N       | N          | N      | N      |
| identity     | R       | N          | N      | N      |

R = read; W = write; N = no access. This prevents unintended overwrites or personality drift.

## 7. Injection Protocol
Persona must be injected in three layers:
- System Prompt Layer: natural-language identity and preferences.
- Structured Context Layer: structured traits used by planner, router, and behavior modules.
- Constraint Layer: hard constraints (e.g., "avoid verbosity").

Injection must occur before model selection, planner initialization, and tool routing to ensure persona governs downstream behavior.

## 8. Auditing
All persona activities must be auditable.
- Required logs: persona load events; persona injection logs; persona updates and their triggers; conflict resolution decisions; persona-version history.
- Stored in: `persona_audit_log.json`.

## 9. Compatibility
Persona Protocol is fully compatible with:
- Structure Card Protocol
- Primitive IR
- Memory ETL Protocol
- ADK Session + Event Model
- Routing & Planner Modules
- Multi-Agent Message Passing Protocol

Persona = identity layer binding all components into one consistent system.

## 10. Summary
- Structured, contract-oriented identity format.
- Lifecycle pipeline from events → memory → persona → behavior.
- Scheduling layer connecting persona to model/tool/planner.
- Governance system for safe multi-agent identity use.
- Reconciliation mechanism for long-term stability.

The protocol transforms persona from "metadata" into a living, evolving identity substrate for AI-native agents.
