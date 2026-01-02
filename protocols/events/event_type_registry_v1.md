# Event Type Registry v1

**Status:** Stable  
**Scope:** Event type law (protocol-level)  
**Purpose:** Define canonical event types and their minimal invariants.

## Why a Registry

Event types are not “log labels”. They are **institutional vocabulary**.
If an event type drifts, replay and long-term audit become ambiguous.

This registry exists so that:
- Verifiers can check event-level invariants
- Tests can enforce constitutional red lines
- Engineers can evolve event semantics without breaking history

## Stable Type Families

### `system.lifecycle`

#### `system.boot`
- Declares the start of a system run as an institutional fact.
- Minimal invariants (P00):
  - `payload.system_id / payload.process_id / payload.run_id` MUST exist
  - `trace_id` MUST equal `payload.run_id` after boot
  - `session_id` MUST NOT be `"unknown"`
  - `payload.actor` or `payload._actor` MUST exist (runtime identity visible)

#### `system.shutdown`
- Declares the end of a system run as an institutional fact.
- Minimal invariants (P00):
  - same required payload identity fields as boot
  - `trace_id` MUST equal `payload.run_id`
  - `session_id` MUST NOT be `"unknown"`
  - `payload.actor` or `payload._actor` MUST exist
- Closure:
  - Every `system.boot` MUST have a corresponding `system.shutdown` (same `trace_id`)

## Evolution Rules

- Renaming an existing event type requires a new registry version.
- Adding new event types is allowed if:
  - it declares required fields and trace/session rules
  - it does not weaken existing invariants
