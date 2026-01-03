# Actor Identity Protocol v1

**Status:** Stable  
**Layer:** Identity  
**Audience:** Runtime / Governance / Agent Engineers

---

## Purpose

The Actor protocol defines **who is responsible** for an action recorded
in the system.

Actor is a **constitutional identity**, not an execution detail.
It represents **sovereign responsibility**, not implementation mechanics.

---

## Core Principle

> Every event written into the event ledger MUST declare
> a sovereign actor at the envelope level.

Actors are facts, not explanations.

---

## Actor Object

```json
{
  "kind": "runtime | agent | human | institution | system",
  "id": "stable-non-empty-string",

  "agent_id": "optional",
  "persona_id": "optional",
  "source": "config | runtime | cli | api | imported",
  "display": "optional human-readable name"
}
Required Fields
actor.kind
Defines the sovereign category of responsibility.
Allowed values:

runtime — system lifecycle (boot/shutdown)
agent — autonomous agent action
human — explicit human action
institution — governed automated system
system — low-level system authority (reserved)
actor.id
A stable, non-empty identifier.
Examples:

p00-agent-os-mvp
agent:p00
user:alice
institution:repo-release-bot
"unknown" is explicitly forbidden.
Optional Fields
Optional fields provide traceability, not authority.
They MUST NOT replace kind or id.

Non-Goals
Actor is NOT inferred.
Actor is NOT optional.
Actor is NOT a payload field.
Actor is NOT an execution hint.
Responsibility must be explicitly declared.
Institutional Statement
Facts without accountable actors are invalid.
This protocol establishes the minimum identity
required for long-term auditability, governance,
and replayable history.


---

# ② `protocols/events/event_envelope_v1_1.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Event Envelope Schema v1.1",
  "type": "object",

  "required": [
    "schema_version",
    "event_type",
    "timestamp",
    "actor",
    "payload",
    "payload_hash"
  ],

  "properties": {
    "schema_version": {
      "const": "1.1"
    },

    "event_type": {
      "type": "string"
    },

    "timestamp": {
      "type": "string",
      "format": "date-time"
    },

    "actor": {
      "type": "object",
      "required": ["kind", "id"],
      "properties": {
        "kind": {
          "type": "string",
          "enum": ["runtime", "agent", "human", "institution", "system"]
        },
        "id": {
          "type": "string",
          "minLength": 1,
          "not": {
            "enum": ["unknown"]
          }
        },
        "agent_id": { "type": "string" },
        "persona_id": { "type": "string" },
        "source": {
          "type": "string",
          "enum": ["config", "runtime", "cli", "api", "imported"]
        },
        "display": { "type": "string" }
      },
      "additionalProperties": true
    },

    "payload": {
      "type": "object"
    },

    "payload_hash": {
      "type": "string"
    },

    "session_id": {
      "type": ["string", "null"]
    },

    "trace_id": {
      "type": ["string", "null"]
    }
  },

  "additionalProperties": true
}