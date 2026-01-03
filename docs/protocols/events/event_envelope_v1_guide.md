# Event Envelope Protocol v1 — Guide

This document explains the intent, rationale, and operational guidance for **Event Envelope v1**.
The enforcement contract lives in:
- `protocols/events/event_envelope_v1.md`
- `protocols/events/event_envelope_v1.schema.json`

## What this protocol is for

Event Envelope v1 defines the minimal, non-drifting structure for runtime events in `events.jsonl`.

Key framing:
- Events are **not logs**.
- Events are **durable, structured facts** that support:
  - auditability
  - causal replay
  - long-term system memory

Once appended, events should be treated as historical records of what the system can claim “really happened”.

## Design principles (why it looks like this)

1. **Determinism**  
   Same payload → same canonical string → same hash. This makes drift detectable.

2. **Minimal but sufficient**  
   The envelope stays stable; semantics can evolve inside `payload` (under versioning rules).

3. **Machine-first**  
   Fixed fields, parseable format, schema-bound expectations.

4. **Auditability**  
   Important actions leave structured evidence that can be replayed and checked.

5. **Forward compatibility**  
   New capabilities add optional fields or bump versions—never silently reinterpret old facts.

## Envelope vs payload

- Envelope fields (`schema_version`, `event_type`, ids, timestamp) exist to support indexing, correlation, and replay.
- `payload` carries event-specific structure and may evolve over time.
- `payload_hash` anchors `payload` so downstream consumers can detect mutation or canonicalization drift.

## Canonicalization and hashing (operational notes)

`payload_hash` is computed from canonicalized `payload`:
- keys sorted
- compact JSON (no whitespace)
- UTF-8
- no ASCII escaping (`ensure_ascii=false` style)

This means:
- Producers and consumers can independently verify the same `payload_hash`.
- If a team changes their JSON serialization settings, verification tests should catch it.

## Event ordering & causality (顺序与因果)

Important: **time order ≠ causal order**.

- Time order: inferred from `ts` (useful but not definitive for causality).
- Causality: should be represented via correlation/trace structures.

In your broader system, you may use:
- `trace_id`
- `span_id`
- `parent_span_id`

Replay / Debug / Audit MUST prefer causal structure when available.

> Note: `span_id` / `parent_span_id` are not required by Event Envelope v1 itself; they can appear as optional fields or inside `payload`, as long as compatibility rules are respected.

## Optional tamper-evidence chain (prev_envelope_hash)

The protocol allows optional chaining:
- `prev_envelope_hash` points to the prior event’s `envelope_hash` within the same session.
- This forms a **hash-linked chain** for tamper-evidence detection.

Two important notes:
- v1 guarantees **detectability rules** only when the system defines a deterministic `envelope_hash`.
- If you implement `envelope_hash`, its derivation must be documented as a contract (either in v1 docs or a separately versioned protocol).

## Compatibility rules (why this is “constitutional”)

- Old events remain valid forever under the version they were written with.
- New fields can be added only if:
  - optional, or
  - introduced via a version bump (`schema_version` change).
- Forbidden:
  - reinterpreting old field meanings
  - silently changing hashing/canonicalization rules

This is what keeps the event ledger replayable years later.

## Non-goals (明确不做的事)

- Not trying to describe UI behavior
- Not a human logging system
- Not embedding model prompts or chain-of-thought
- Not guaranteeing tamper-proofness (only tamper-evidence detection when chaining is implemented)

## Extended example

See:
- `examples/events/event_envelope_v1.example.jsonl`

## One-line summary

> **Event Envelope v1 defines what counts as “really happened”.**
>
> In this OS: if it didn’t enter the event ledger, it didn’t happen (from the system’s standpoint).
