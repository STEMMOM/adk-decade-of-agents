# Event Envelope Protocol v1 (Redline)

**Status:** Stable  
**Scope:** OS-level runtime events  
**Audience:** Runtime / Agent / Governance engineers  
**Version:** 1.0

## 1. Authority

This protocol defines the minimal, non-drifting **event envelope** for `events.jsonl` (JSONL).
Once an event is appended to the ledger, its envelope fields and meanings MUST NOT be implicitly changed.

- This file is the enforcement contract.
- Explanations, rationale, tutorials, and extended examples live in `docs/protocols/events/event_envelope_v1_guide.md`.

## 2. Data Contract

Each event is a single JSON object (one line, JSONL) with the following top-level fields:

```json
{
  "schema_version": "1.0",
  "event_type": "...",
  "session_id": "...",
  "trace_id": "...",
  "ts": "...",
  "payload": { ... },
  "payload_hash": "..."
}
Optional extension fields (allowed by forward compatibility rules):
prev_envelope_hash (string): pointer to the previous event’s envelope_hash within the same session (if the system defines envelope_hash).
envelope_hash (string): a system-defined hash of the envelope for tamper-evidence (if implemented).
Authoritative schema: protocols/events/event_envelope_v1.schema.json
3. Invariants (MUST / SHOULD)
3.1 Required fields
MUST contain: schema_version, event_type, session_id, trace_id, ts, payload, payload_hash.
MUST set schema_version to "1.0" for v1 events.
3.2 Types
payload MUST be a JSON object (default {}).
payload_hash MUST be a 64-hex SHA-256 digest string (lowercase hex recommended).
3.3 Timestamp
ts MUST be a UTC timestamp in RFC3339 / ISO 8601 format with milliseconds and trailing Z
(e.g., 2024-12-17T03:21:45.123Z).
3.4 Hash correctness
payload_hash MUST equal SHA-256 hex digest of the canonicalized payload (see §4).
3.5 Append-only ledger semantics
Events written to events.jsonl MUST be treated as durable facts.
Implementations MUST NOT rewrite historical events in-place.
If correction is needed, it MUST be represented as a new event.
3.6 Optional chaining (tamper-evidence)
If prev_envelope_hash is present, it SHOULD refer to the previous event’s envelope_hash in the same session.
If envelope_hash is present, its derivation MUST be deterministic and documented as a contract (in this protocol or a separately versioned protocol).
4. Canonicalization Rules (for payload_hash)
Canonicalize payload as JSON with:
keys sorted
no whitespace / compact separators
UTF-8 encoding
ensure_ascii=false behavior (i.e., do not escape non-ASCII)
Then:
payload_hash = SHA-256 hex digest of that canonicalized payload string.
5. Backward & Forward Compatibility
Old events are always valid under the protocol version they were written with.
New fields:
MAY be added as optional fields, or
MUST be introduced via a new schema_version for breaking changes.
Forbidden:
MUST NOT reinterpret existing fields’ semantics.
MUST NOT silently change field definitions or hashing rules.

---

## 2) `protocols/events/event_envelope_v1.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "event-envelope-v1.schema.json",
  "title": "Event Envelope Protocol v1",
  "type": "object",
  "additionalProperties": true,
  "required": [
    "schema_version",
    "event_type",
    "session_id",
    "trace_id",
    "ts",
    "payload",
    "payload_hash"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "1.0",
      "description": "Protocol version, fixed as '1.0' in v1."
    },
    "event_type": {
      "type": "string",
      "minLength": 1,
      "description": "Semantic category (e.g. session.start, user.message, agent.reply, session.end)."
    },
    "session_id": {
      "type": "string",
      "minLength": 1,
      "description": "Session identifier for a lifecycle instance."
    },
    "trace_id": {
      "type": "string",
      "minLength": 1,
      "description": "Correlation identifier for a causal chain."
    },
    "ts": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3}Z$",
      "description": "UTC timestamp in RFC3339/ISO8601 with milliseconds and trailing Z."
    },
    "payload": {
      "type": "object",
      "description": "Event-specific structured data. Defaults to {}."
    },
    "payload_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "SHA-256 hex digest of canonicalized payload."
    },

    "prev_envelope_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "Optional pointer to previous event's envelope_hash in the same session (if envelope_hash is implemented)."
    },
    "envelope_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$",
      "description": "Optional system-defined deterministic hash of the envelope for tamper-evidence (contract must be documented)."
    }
  }
}