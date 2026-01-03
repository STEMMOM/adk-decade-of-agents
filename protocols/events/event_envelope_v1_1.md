Event Envelope Protocol v1.1 (Authority)
Status: Stable
Scope: OS-level runtime events
Audience: Runtime / Agent / Governance engineers
Version: 1.1
Supersedes: Event Envelope Protocol v1.0
1. Authority
This protocol defines the authoritative event envelope for events.jsonl
under Event Envelope v1.1.
Once an event is appended to the ledger:
Its envelope fields
Their meanings
And their institutional semantics
MUST NOT be implicitly changed.
This file is the enforcement contract.
All explanations, rationale, tutorials, and extended examples
MUST live outside this file (e.g. in docs/).
2. Purpose
Event Envelope v1.1 upgrades the event system from:
“Events happened”
to:
“Someone is responsible for what happened.”
This version promotes Actor from an implicit or payload-level concept
to a constitutional, top-level field.
3. Data Contract
Each event is a single JSON object (one line, JSONL) with the following
top-level fields:
{
  "schema_version": "1.1",
  "event_id": "...",
  "event_type": "...",
  "ts": "...",
  "session_id": "...",
  "trace_id": "...",
  "span_id": "...",
  "actor": { ... },
  "payload": { ... },
  "payload_hash": "..."
}
Optional extension fields (allowed by forward compatibility rules):
parent_span_id (string | null)
envelope_hash (string)
prev_envelope_hash (string)
Authoritative schema:
protocols/events/event_envelope_v1_1.schema.json
4. Actor (Constitutional Field)
4.1 Definition
actor defines the sovereign entity responsible for causing the event.
Actor is:
A fact, not an explanation
A responsibility claim, not an execution detail
A top-level envelope field, not a payload attribute
4.2 Structure
"actor": {
  "kind": "...",
  "id": "...",

  "agent_id": "...",
  "persona_id": "...",
  "source": "...",
  "display": "..."
}
Required
actor.kind
actor.id
Optional
agent_id
persona_id
source
display
4.3 actor.kind
Defines the category of sovereign responsibility.
Allowed values:
runtime — system lifecycle actions (boot, shutdown)
agent — autonomous agent behavior
human — explicit human action
institution — governed automated authority
system — reserved low-level authority
4.4 actor.id
A stable, non-empty identifier for the actor.
MUST NOT be empty
MUST NOT be "unknown"
MUST remain stable across replay
Examples:
p00-agent-os-mvp
agent:p00
user:alice
institution:repo-release-bot
4.5 Actor Non-Goals
The following are explicitly forbidden:
Inferring actor from payload
Omitting actor
Reinterpreting payload fields as responsibility
Treating actor as optional metadata
Responsibility must be explicit.
5. Invariants (MUST / SHOULD)
5.1 Required Fields
Events MUST contain:
schema_version
event_id
event_type
ts
session_id
trace_id
span_id
actor
payload
payload_hash
Events written under this protocol MUST set:
"schema_version": "1.1"
5.2 Types
payload MUST be a JSON object
payload_hash MUST be a 64-character lowercase hex SHA-256 digest
actor MUST be an object with required fields
5.3 Timestamp
ts MUST be:
UTC
RFC3339 / ISO8601
Include milliseconds
End with Z
Example:
2024-12-17T03:21:45.123Z
5.4 Hash Correctness
payload_hash MUST equal:
SHA-256 hex digest of the canonicalized payload
Canonicalization rules are unchanged from v1.0.
5.5 Append-Only Ledger Semantics
Events MUST be treated as durable facts
Historical events MUST NOT be rewritten
Corrections MUST be represented as new events
5.6 Optional Chaining (Tamper Evidence)
If implemented:
prev_envelope_hash SHOULD point to the previous event’s envelope_hash
envelope_hash MUST be deterministic and documented
6. Backward & Forward Compatibility
6.1 Backward Compatibility
Events written under v1.0 remain valid under v1.0
v1.0 events MAY be replayed
v1.0 events MUST NOT be reinterpreted to have actors
6.2 Forward Compatibility
New optional fields MAY be added
Breaking changes MUST require a new schema_version
Forbidden:
Silent semantic changes
Reinterpretation of existing fields
Mixed semantics within the same version
7. Institutional Statement
Event Envelope v1.1 marks the transition
from event recording
to responsibility recording.
From this version forward:
No event may enter history without an accountable actor
Responsibility becomes replayable, auditable, and governable
This protocol establishes the minimum constitutional boundary
for AI-native systems that must answer, in the future:
“Who caused this — and under what authority?”